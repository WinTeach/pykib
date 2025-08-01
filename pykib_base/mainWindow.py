#!/usr/bin/env python3
# pykib - A PyQt6 based kiosk browser with a minimum set of functionality
# Copyright (C) 2021 Tobias Wintrich
#
# This file is part of pykib.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import pathlib
import sys
import os
import subprocess
import logging
import tempfile

from PyQt6.QtPrintSupport import QPrintDialog, QPrinter

import pykib_base.ui
import pykib_base.arguments
import platform
from functools import partial
from datetime import datetime

from pykib_base.myQWebEngineView import myQWebEngineView
from pykib_base.myQWebEnginePage import myQWebEnginePage
from pykib_base.PrintPdf import PrintPdf
from pykib_base.memoryCap import MemoryCap
from pykib_base.memoryDebug import MemoryDebug
from pykib_base.autoReload import AutoReload
from pykib_base.resetTimeout import ResetTimeout
from pykib_base.oAuthFileHandler import OAuthFileHandler

#
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6 import QtCore
from PyQt6.QtCore import QTimer, Qt, QEvent
from PyQt6.QtGui import QGuiApplication

from PyQt6.QtWidgets import QWidget, QSystemTrayIcon

class MainWindow(QWidget):
    fullScreenState = False
    firstRun = True

    def __init__(self, transferargs, dirname, parent=None, tray: QSystemTrayIcon = None, browserProfile=None):
        print("running in: " + dirname)
        self.args = transferargs
        self.dirname = dirname
        self.tray = tray
        self.isLoading = True
        self.printPdfThread = None
        self.browserProfile = browserProfile

        if (self.args.remoteBrowserDaemon):
            super(MainWindow, self).__init__(parent, Qt.WindowType.Tool)
        else:
            super(MainWindow, self).__init__(parent)

        self.applyWindowHints()
        # self.setAttribute(Qt.WA_DeleteOnClose)

        # Create WebView and WebPage
        self.web = myQWebEngineView(self.args, dirname, self)
        self.web.setObjectName("view")

        if self.browserProfile:
            self.page = myQWebEnginePage(self.args, dirname, self, True, self.browserProfile)
        else:
            self.page = myQWebEnginePage(self.args, dirname, self, True)
            self.browserProfile = self.page.browserProfile
        self.web.setPage(self.page)

        # Setup UI
        pykib_base.ui.setupUi(self, self.args, dirname)

        # Added progress Handling
        self.web.loadProgress.connect(self.loadingProgressChanged)
        self.web.loadFinished.connect(self.jsInjection)
        self.web.loadStarted.connect(self.startLoading)
        self.web.loadFinished.connect(self.loadFinished)
        self.web.renderProcessTerminated.connect(self.viewTerminated)
        self.removeDownloadBarTimer = QTimer(self)
        self.page.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

        if self.args.enablePrintSupport:
            self.page.printRequested.connect(self.printSiteRequest)

        # Definde Action when Fullscreen ist choosen
        self.page.fullScreenRequested.connect(self.toggleFullscreen)


        if self.args.closeOnUrl:
            logging.debug('closeOnUrl is set')
            self.web.urlChanged.connect(self.closeOnUrl)

        if (self.args.oAuthInputFile):
            logging.info(
                "oAuthInputFile is set. Going to monitor the file each second and inject the content into the browser")
            self.oAuthFileHandler = OAuthFileHandler(str(self.args.oAuthInputFile))
            self.oAuthFileHandler.daemon = True  # Daemonize thread
            self.oAuthFileHandler.oAuthFileChanged.connect(self.oAuthHandleInput)
            self.oAuthFileHandler.start()
            logging.debug(
                "start")
        if (self.args.addMemoryCap):
            logging.info("Starting memory monitoring. Going to close browser when memory usage is over " + str(
                self.args.addMemoryCap) + "MB")
            self.memoryCapThread = MemoryCap(int(self.args.addMemoryCap))
            self.memoryCapThread.daemon = True  # Daemonize thread
            self.memoryCapThread.memoryCapExceeded.connect(self.closeBecauseMemoryCap)
            self.memoryCapThread.start()
        if (self.args.memoryDebug):
            logging.info("Starting memory monitoring")
            self.memoryDebugThread = MemoryDebug()
            self.memoryDebugThread.daemon = True  # Daemonize thread
            self.memoryDebugThread.memoryDebugTick.connect(self.memoryDebugUpdate)
            self.memoryDebugThread.start()
        if (self.args.autoReloadTimer):
            logging.info(
                "AutoRefreshTimer is set. Going to reload the webpage each" + str(
                    self.args.autoReloadTimer) + "seconds")
            self.autoRefresher = AutoReload(int(self.args.autoReloadTimer))
            self.autoRefresher.daemon = True  # Daemonize thread
            self.autoRefresher.autoRefresh.connect(self.autoRefresh)
            self.autoRefresher.start()
        if (self.args.browserResetTimeout):
            logging.info(
                "BrowserResetTimeout is set. Going to reset the webpage after " + str(
                    self.args.browserResetTimeout) + "seconds of inactivity")

            self.resetTimeout = ResetTimeout(int(self.args.browserResetTimeout))
            self.resetTimeout.daemon = True  # Daemonize thread
            self.resetTimeout.resetTimeoutExeeded.connect(self.resetTimeoutExeeded)
            self.resetTimeout.start()
            self.web.loadProgress.connect(self.resetTimerReset)
            self.web.urlChanged.connect(self.resetTimerReset)

        # Store initial Restore State
        self.restoreState = self.windowState()

        # Start with url
        self.web.load(self.args.url)

    def startLoading(self):
        self.isLoading = True

    def loadFinished(self):
        self.isLoading = False

    def changeEvent(self, event: QEvent):
        if (event.type() == QEvent.Type.WindowStateChange):
            if not self.windowState().__contains__(Qt.WindowState.WindowMinimized):
                self.restoreState = self.windowState()
                logging.debug("Set RestoreState = " + str(self.restoreState))

    def closeOnUrl(self):
        logging.debug(self.web.url().toString().lower());
        logging.debug(self.args.closeOnUrl.lower());
        logging.debug(self.web.url().toString().lower().find(self.args.closeOnUrl.lower()));
        if self.web.url().toString().lower().find(self.args.closeOnUrl.lower()) != -1:
            logging.info("CloseOnUrl is set. Closing Browser")
            self.closeWindow()

    def oAuthHandleInput(self, url):
        logging.debug("Handling oAuthInputFile URL " + str(url))
        #temporary store current url for return after oAuth
        currentUrl = self.web.url().toString()
        #set url from file
        self.web.load(url)
        #if oAuthOutputFile is set, wait for loadFinished and write the current url to the file
        if(self.args.oAuthOutputFile):
            self.oAuthLoadFinished = self.web.loadFinished.connect(partial(self.oAuthHandleOutput, currentUrl))

    def oAuthHandleOutput(self, restoreUrl):
        #if current url contains oAuthOutputUrlIdentifier then
        if(not self.args.oAuthOutputUrlIdentifier or self.web.url().toString().lower().find(self.args.oAuthOutputUrlIdentifier.lower()) != -1):
            if not os.path.exists(self.args.oAuthOutputFile):
                open(self.args.oAuthOutputFile, 'w').close()
            with open(self.args.oAuthOutputFile, 'w') as f:
                f.write(self.web.url().toString())
            self.web.loadFinished.disconnect(self.oAuthLoadFinished)
            if(self.args.oAuthOutputCloseSuccess):
                self.closeWindow()
            else:
                self.web.load(restoreUrl)

    def resetTimerReset(self):
        logging.info(
            "BrowserResetTimeout is set.")
        self.resetTimeout.resetTimer()

    def resetTimeoutExeeded(self):
        # Reset Page if resetTimeoutExeeded
        python = sys.executable
        os.execl(python, python, *sys.argv) # Restart the Browser
        # self.page.setParent(None)
        # self.page.deleteLater()
        # self.page = None
        # self.page = myQWebEnginePage(self.args, self.dirname, self, False)
        # self.page.featurePermissionRequested.connect(self.onFeaturePermissionRequested)
        # self.page.fullScreenRequested.connect(self.toggleFullscreen)
        # self.web.setPage(self.page)
        # self.web.load(self.args.url)

    def applyWindowHints(self):
        if (self.args.alwaysOnTop and self.args.removeWindowControls or self.args.remoteBrowserDaemon):
            if (self.args.remoteBrowserIgnoreX11):
                self.setWindowFlags(
                    Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.X11BypassWindowManagerHint)
            else:
                self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        elif (self.args.removeWindowControls):
            self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        elif (self.args.alwaysOnTop):
            self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

    def toggleFullscreen(self, request):
        logging.info("Fullscreen Request received")
        logging.info(self.fullScreenState)
        if (not self.args.fullscreen):
            if (self.fullScreenState):
                logging.info("leave Fullscreen")
                self.fullScreenState = False
                self.showNormal()
                self.applyWindowHints()
                if (self.args.remoteBrowserIgnoreX11):
                    logging.info("Restore previous Windows Position")
                    if (self.oldgeometry == 'maximized'):
                        self.showMaximized()
                    else:
                        self.setGeometry(self.oldgeometry)
                self.show()
            else:
                # remove Mask
                self.web.parent.clearMask()

                if (self.args.remoteBrowserIgnoreX11):
                    logging.info("Store Current Windows Position")
                    if (self.isMaximized()):
                        self.oldgeometry = 'maximized'
                    else:
                        self.oldgeometry = self.frameGeometry()

                logging.info("set Fullscreen")
                self.fullScreenState = True
                # Need to remove X11BypassWindowManagerHint because without showFullscreen not possible
                if (self.args.remoteBrowserIgnoreX11):
                    self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)

                self.showFullScreen()
                # Need set X11BypassWindowManagerHint again after going to Fullscreen
                if (self.args.remoteBrowserIgnoreX11):
                    self.setWindowFlags(
                        Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint | Qt.WindowType.X11BypassWindowManagerHint)
                    self.show()
        request.accept()

    def enterEvent(self, event):
        # When working with a remote Daemon, the Browse need to get focussed on Enter
        if (self.args.remoteBrowserDaemon):
            self.activateWindow()
            logging.debug("Enter window")

    def leaveEvent(self, event):
        if (self.args.remoteBrowserDaemon):
            # Workaround for Applications which don't grab the focus when click on them (like VMWare View)
            if (platform.system().lower() == "linux"):
                os.system("activeWindow=$(xdotool getactivewindow) && xdotool windowfocus $activeWindow")
            logging.debug("Leave window")

    def onFeaturePermissionRequested(self, url, feature):
        logging.info("Permission" + str(feature))
        if (self.args.allowMicAccess and feature == QWebEnginePage.Feature.MediaAudioCapture):
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            logging.info("Permission" + str(feature) + " | granted")
            return True
        if (self.args.allowWebcamAccess and feature == QWebEnginePage.Feature.MediaVideoCapture):
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            logging.info("Permission" + str(feature) + " | granted")
            return True
        if (
                self.args.allowMicAccess and self.args.allowWebcamAccess and feature == QWebEnginePage.Feature.MediaAudioVideoCapture):
            logging.info("Permission" + str(feature) + " | granted")
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            return True
        if (self.args.allowDesktopSharing and (
                feature == QWebEnginePage.Feature.DesktopVideoCapture or feature == QWebEnginePage.Feature.DesktopAudioVideoCapture)):
            logging.info("Permission" + str(feature) + " | granted")
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            return True
        if (self.args.allowBrowserNotifications and feature == QWebEnginePage.Feature.Notifications):
            logging.info("Permission" + str(feature) + " | granted")
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            return True

        self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)
        logging.info("Permission " + str(feature) + " | denied")
        return False

    # Handling crash of wegengineproc
    def viewTerminated(self, status, exitCode):
        if status == QWebEnginePage.RenderProcessTerminationStatus.NormalTerminationStatus:
            return True
        else:
            logging.error("WebEngineProcess stopped working. Stopping pykib")
            logging.error(status)
            logging.error(exitCode)
            os._exit(1)

    def closeBecauseMemoryCap(self, time_to_close, remaining_time_to_close):
        progress_percent = 100 / time_to_close * remaining_time_to_close
        self.memoryCapBar.show()
        self.memoryCapCloseBar.setValue(int(progress_percent))
        self.memoryCapCloseBar.setFormat("Speicherlimit überschritten, beende Anwendung automatisch in " + str(
            remaining_time_to_close) + " Sekunden")

    def autoRefresh(self):
        self.web.reload()
        logging.info("Auto reloading Webpage")

    def memoryDebugUpdate(self, currentMemUse, currentSwapUse):
        informationstring = "Current Memory Usage: "
        if (currentMemUse > 0):
            informationstring += "RAM: " + str(currentMemUse) + " MB "
        if (currentSwapUse > 0):
            informationstring += "| SWAP: " + str(currentSwapUse) + " MB "

        informationstring += "| Total: " + str(currentSwapUse + currentMemUse) + " MB "

        if (self.args.addMemoryCap):
            if ((currentSwapUse + currentMemUse) > int(self.args.addMemoryCap)):
                self.memoryDebug.changeStyle('memorycap')
            else:
                self.memoryDebug.changeStyle('loading')
            informationstring += "| MemoryCap: " + str(self.args.addMemoryCap) + " MB"

        self.memoryDebug.setFormat(informationstring)

    def closeWindow(self):
        logging.info("Closing Browser by Exit Call")
        sys.exit(0)

    def pressed(self):
        self.web.load(self.addressBar.displayText())

    def downloadProgressChanged(self, bytesReceived, bytesTotal):
        self.downloadProgress.show()
        percent = round(100 / bytesTotal * bytesReceived)
        self.downloadProgress.setValue(percent)

        self.downloadProgress.setFormat(str(round(bytesReceived / 1024 / 1024, 2)) + "MB / " + str(
            round(bytesTotal / 1024 / 1024, 2)) + "MB completed")

    def downloadFinished(self):
        self.downloadProgress.show()
        if (platform.system().lower() == "linux"):
            self.downloadProgress.setFormat("Download finished....(Syncing File System)")
            logging.info("Running 'sync' after download")
            os.system("sync")

        self.downloadProgress.setValue(100)

        self.timeToHideDownloadBar = 10

        self.removeDownloadBarTimer.setInterval(1000)
        self.removeDownloadBarTimer.timeout.connect(self.onRemoveDownloadBarTimout)
        self.removeDownloadBarTimer.start()

    def onRemoveDownloadBarTimout(self):
        self.downloadProgress.setFormat("Download finished....(closing in " + str(self.timeToHideDownloadBar) + "s)")
        self.timeToHideDownloadBar -= 1
        if (self.timeToHideDownloadBar == -1):
            self.removeDownloadBarTimer.stop()
            self.downloadProgress.hide()

    def jsInjection(self, loadFinished):
        if (self.args.injectJavascript):
            logging.debug("JS Files injection")
            if (loadFinished):
                for injection in self.args.injectJavascript:
                    script = ''
                    if (injection[1] == '1' and self.firstRun) or injection[1] == '0':
                        logging.debug("Inject Javascript")
                        logging.debug(injection)
                        script = open(injection[0], "r").read()
                        if(self.args.enableAutoLogon):
                            if(self.args.autoLogonUser):
                                script = script.replace('{autoLogonUser}', self.args.autoLogonUser)
                            if(self.args.autoLogonPassword):
                                script = script.replace('{autoLogonPassword}', self.args.autoLogonPassword)
                            if(self.args.autoLogonDomain):
                                script = script.replace('{autoLogonDomain}', self.args.autoLogonDomain)
                        for parameter in injection[2::]:
                            script = script.replace('{'+parameter[0]+'}', parameter[1])
                        self.page.runJavaScript(script)
        if (loadFinished):
            if (self.args.enableAutoLogon and self.firstRun == True):
                logging.info("Perform AutoLogin")
                # if(len(autologin) >= 2):
                username = self.args.autoLogonUser.replace("\\", "\\\\").replace("'", "\\'")
                password = self.args.autoLogonPassword.replace("\\", "\\\\").replace("'", "\\'")
                domain = self.args.autoLogonDomain.replace("'", "\\'") if self.args.autoLogonDomain else False
                usernameID = self.args.autoLogonUserID
                passwordID = self.args.autoLogonPasswordID
                domainID = self.args.autoLogonDomainID
                # if(len(autologin) >= 3):
                # if(autologin[2]):
                # domain = autologin[2].replace("\\","\\\\")
                # if(len(autologin) == 6):
                # usernameID = autologin[3].replace("\\","\\\\")
                # passwordID = autologin[4].replace("\\","\\\\")
                # if(autologin[5]):
                # domainID = autologin[5].replace("\\","\\\\")

                # """+len(autologin)+"""<=3
                script = r"""
                                        usernameID = "False";
                                        passwordID = "False";
                                        domainID = "False";
                                        
                                        document.onload=login();
                                        
                                        async function populateIDs(){{
                                            if('{usernameID}' == "False"){{          
                                                    if(document.getElementById('FrmLogin') && document.getElementById('DomainUserName') && document.getElementById('UserPass')){{ 
                                                        usernameID = "DomainUserName";
                                                        passwordID = "UserPass";                             
                                                    }}else if(document.getElementById('passwd') && document.getElementById('login')){{
                                                        usernameID = "login";
                                                        passwordID = "passwd";                                              
                                                    }}else if(document.getElementById('Enter user name')){{
                                                        usernameID = "Enter user name";
                                                        passwordID = "passwd";
                                                    }}else if(document.getElementById('user')){{
                                                        usernameID = "user";
                                                        passwordID = "password";
                                                    }}else{{
                                                        usernameID = "username";
                                                        passwordID = "password";                                             
                                                    }}
                                                }}else if('{usernameID}' != 'False'){{
                                                    usernameID = "{usernameID}";
                                                    passwordID = "{passwordID}";
                                                    domainID = "{domainID}";
                                                }}
                                        }}
                                        async function login(){{                                                      

                                            //Wait until usernameID and PasswordID is loaded
                                            while(!document.getElementById(usernameID) && !document.getElementById(passwordID)) {{   
                                              populateIDs();                               
                                              await new Promise(r => setTimeout(r, 50));                                                           
                                            }}

                                            if('{domain}' != 'False' && domainID == 'False'){{                                 
                                                document.getElementById(usernameID).value='{domain}\\{username}';
                                                document.getElementById(passwordID).value='{password}';
                                            }}else if('{domain}' != 'False' && domainID != 'False'){{                                
                                                document.getElementById(usernameID).value='{username}';
                                                document.getElementById(passwordID).value='{password}';
                                                document.getElementById(domainID).value='{domain}';
                                            }}else{{                                
                                                document.getElementById(usernameID).value='{username}';
                                                document.getElementById(passwordID).value='{password}';
                                            }}    
                                            //for the Storefront/Citrix Netscaler Gateway Login the Login Button had to be clicked
                                            if(document.getElementById("loginBtn")){{
                                                document.getElementById("loginBtn").click();
                                            }}else if(document.getElementById("nsg-x1-logon-button")){{
                                                document.getElementById("nsg-x1-logon-button").click();
                                            }}else{{
                                                document.forms[0].submit();
                                            }}1
                                        }}
                                        """.format(username=username, password=password, domain=domain,
                                                   usernameID=usernameID,
                                                   passwordID=passwordID, domainID=domainID)
                self.page.runJavaScript(script)

            if (self.args.enableMouseDrag):
                logging.info("Perform Mouse Drag Mode Scripts")
                script = r"""

            document.body.addEventListener("mousedown", mouseDown);
            document.body.addEventListener("mousemove", mouseMove);
            document.body.addEventListener("mouseup", mouseUp);
            document.body.addEventListener("mouseout", mouseOut);

            var drag = false;
            var startx = 0;
            var starty = 0;

            function mouseDown(e) {{
            if (!e) {{ e = window.event; }}   
                if (e.srcElement && e.srcElement.nodeName === 'IMG') {{
                    e.returnValue = e.preventDefault();
                }}
                 e.preventDefault();
                this.starty = e.clientY + document.body.scrollTop;
                drag = true;
            }}

            function mouseUp(e) {{
            if (!e) {{ e = window.event; }}
                drag = false;
                var start = 1,
                    animate = function () {{
                        var step = Math.sin(start);           

                        if (step <= 0) {{
                            window.cancelAnimationFrame(animate);
                        }} else {{
                            diffy = 0;
                            document.body.scrollTop += diffy * step;
                            document.documentElement.scrollTop += diffy * step;        
                            start -= 0.02;
                            window.requestAnimationFrame(animate);
                        }}
                    }};
                animate();
            }}

            function mouseOut(e) {{
                 e = e ? e : window.event;
                var from = e.relatedTarget || e.toElement;
                if (!from || from.nodeName == "HTML") {{
                    drag = false;
                }}
            }}

            function mouseMove(e) {{
             if (drag === true) {{
                    if (!e) {{ e = window.event; }}
                    diffy = (this.starty - (e.clientY + document.body.scrollTop)) * 2;        
                    document.body.scrollTop += diffy;
                    document.documentElement.scrollTop += diffy;        
                    this.starty = e.clientY + document.body.scrollTop;
                }}
            }}

             """
                self.page.runJavaScript(script)
            self.firstRun = False

    # Print Function
    def printSiteRequest(self):
        logging.info("Test if site is loaded")
        if self.isLoading:
            logging.debug("Site is still loading. Wait for loadFinished before printing")
            self.web.loadFinished.connect(self.printSiteToPdf)
        else:
            self.printSiteToPdf()

    def printSiteToPdf(self):
        try:
            self.web.loadFinished.disconnect(self.printSiteToPdf)
        except Exception as e:
            pass

        tempPdfFolder = tempfile.gettempdir() + "/pykib/"
        # check if folder exists
        if not os.path.exists(tempPdfFolder):
            os.makedirs(tempfile.gettempdir() + "/pykib/")

        # create a unique filename
        tempPdfFile = tempPdfFolder + datetime.now().strftime("%Y%m%d%H%M%S") + ".pdf"
        logging.debug("Created temporary PDF for Printing: " + tempPdfFile)
        self.web.setStyleSheet("body { background: white; }")

        script = "var bodyElement = document.querySelector('body');"
        script += "bodyElement.style.backgroundColor = 'white';"

        self.page.runJavaScript(script)
        self.web.printToPdf(tempPdfFile)

        # Create Printer Dialog
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setResolution(300)
        dialog = QPrintDialog(printer)

        logging.debug("Show Print Dialog")
        dialogResult = dialog.exec()
        if(dialogResult == QPrintDialog.DialogCode.Accepted):
            #Printing in Background Thread
            self.printPdfThread = PrintPdf(tempPdfFile, printer)
            self.printPdfThread.daemon = True
            self.printPdfThread.printFinished.connect(self.printFinished)
            self.printPdfThread.start()
        else:
            logging.debug("Print aborted by user")
            if os.path.isfile(tempPdfFile):
                os.remove(tempPdfFile)

    def printFinished(self):
        logging.debug("Finished print process")

    def loadingProgressChanged(self, percent):
        # Setting Zoomfactor
        logging.debug("Progress Changed" + str(percent))
        self.web.setZoomFactor(self.args.setZoomFactor / 100)

        if (not self.args.showLoadingProgressBar):
            self.progress.hide()
        elif (not self.progress.disabled):
            self.progress.show()
            self.progress.setValue(percent)
            self.progress.changeStyle("loading")

            if (percent == 100):
                self.progress.hide()

    # catch defined Shortcuts

    def keyPressEvent(self, event):
        if (self.args.browserResetTimeout):
            self.resetTimerReset()

        keyEvent = event

        shift = event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
        ctrl = event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
        alt = event.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier

        if(self.args.enablePrintSupport and ctrl and keyEvent.key() == QtCore.Qt.Key.Key_P):
            logging.info("Print")
            self.printSiteRequest()
        if (shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key.Key_B):
            logging.info("leave by shortcut")
            os._exit(0)
        if ((keyEvent.key() == QtCore.Qt.Key.Key_F5) or (ctrl and keyEvent.key() == QtCore.Qt.Key.Key_R)):
            self.web.reload()
            logging.info("Refresh")
        if (self.args.adminKey and shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key.Key_A):
            logging.info("Hit admin key")
            subprocess.Popen([self.args.adminKey])
        if (self.args.enablePrintKeyHandle and keyEvent.key() == QtCore.Qt.Key.Key_Print):
            logging.info("Saving image to clipboard")
            clipboard = QGuiApplication.clipboard()
            clipboard.setPixmap(self.grab())
            # self.grab().save("d:\\test.png", b'PNG')
        if (keyEvent.key() == QtCore.Qt.Key.Key_F4 and alt):
            logging.info("Alt +F4 is disabled")
        if (ctrl and keyEvent.key() == QtCore.Qt.Key.Key_F):
            self.openSearchBar()
        if (keyEvent.key() == QtCore.Qt.Key.Key_Escape):
            self.closeSearchBar()

    def closeEvent(self, event):
        if self.args.fullscreen:
            logging.debug("Ignore event Close because fullscreen is set")
            event.ignore()
        if self.args.enableTrayMode:
            logging.debug("Ignore event close and hide window because enableTrayMode is set")
            self.hide()
            event.ignore()

    def adjustTitle(self):
        self.setWindowTitle(self.web.title())

    def adjustTitleIcon(self):
        self.setWindowIcon(self.web.icon())
        if self.args.enableTrayMode:
            self.tray.setIcon(self.web.icon())

    def adjustAdressbar(self):
        if (not self.web.url().toString().lower().endswith('.pdf')):
            self.addressBar.setText(self.web.url().toString())

    def openSearchBar(self):
        self.searchBar.show()
        self.searchText.setFocus()
        self.searchText.setSelection(0, self.searchText.maxLength())

    def closeSearchBar(self):
        self.searchBar.hide()

    def searchOnPage(self):
        signalFrom = self.sender().objectName()
        if (signalFrom == "searchUpButton"):
            self.page.findText(self.searchText.text(), QWebEnginePage.FindBackward)
        else:
            self.page.findText(self.searchText.text())
