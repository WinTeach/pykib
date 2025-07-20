#!/usr/bin/env python3
# pykib - A PyQt6 based kiosk browser with a minimum set of functionality
# Copyright (C) 2025 Tobias Wintrich
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
from PyQt6.QtGui import QGuiApplication, QIcon, QCursor

from PyQt6.QtWidgets import QWidget, QSystemTrayIcon, QLabel, QHBoxLayout, QTabBar, QSizePolicy, QToolButton


class MainWindow(QWidget):
    fullScreenState = False
    firstRun = True
    dirname = None

    def __init__(self, transferargs, dirname, parent=None, tray: QSystemTrayIcon = None, browserProfile=None):
        print("running in: " + dirname)
        self.args = transferargs
        self.dirname = dirname
        self.tray = tray
        self.isLoading = True
        self.printPdfThread = None
        self.browserProfile = browserProfile
        self.tabs = {}
        self.currentTabIndex = 0

        if (self.args.remoteBrowserDaemon):
            super(MainWindow, self).__init__(parent, Qt.WindowType.Tool)
        else:
            super(MainWindow, self).__init__(parent)

        self.applyWindowHints()

        # Setup UI
        pykib_base.ui.setupUi(self, self.args, dirname)

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

        for url in self.args.url:
            self.addTab(url)

    def goForward(self):
        if self.currentTabIndex in self.tabs:
            self.tabs[self.currentTabIndex]['web'].forward()

    def goBack(self):
        if self.currentTabIndex in self.tabs:
            self.tabs[self.currentTabIndex]['web'].back()

    def goHome(self):
        if self.currentTabIndex in self.tabs:
            self.tabs[self.currentTabIndex]['web'].load(self.args.url[0])

    def openBookmark(self, url):
        if self.currentTabIndex in self.tabs:
            self.tabs[self.currentTabIndex]['web'].load(url)

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
        logging.debug(self.tabs[self.currentTabIndex]['web'].url().toString().lower());
        logging.debug(self.args.closeOnUrl.lower());
        logging.debug(self.tabs[self.currentTabIndex]['web'].url().toString().lower().find(self.args.closeOnUrl.lower()));
        if self.tabs[self.currentTabIndex]['web'].url().toString().lower().find(self.args.closeOnUrl.lower()) != -1:
            logging.info("CloseOnUrl is set. Closing Browser")
            self.closeWindow()

    def oAuthHandleInput(self, url):
        logging.debug("Handling oAuthInputFile URL " + str(url))
        #temporary store current url for return after oAuth
        currentUrl = self.tabs[self.currentTabIndex]['web'].url().toString()
        #set url from file
        self.tabs[self.currentTabIndex]['web'].load(url)
        #if oAuthOutputFile is set, wait for loadFinished and write the current url to the file
        if(self.args.oAuthOutputFile):
            self.oAuthLoadFinished = self.tabs[self.currentTabIndex]['web'].loadFinished.connect(partial(self.oAuthHandleOutput, currentUrl))

    def oAuthHandleOutput(self, restoreUrl):
        #if current url contains oAuthOutputUrlIdentifier then
        if(not self.args.oAuthOutputUrlIdentifier or self.tabs[self.currentTabIndex]['web'].url().toString().lower().find(self.args.oAuthOutputUrlIdentifier.lower()) != -1):
            if not os.path.exists(self.args.oAuthOutputFile):
                open(self.args.oAuthOutputFile, 'w').close()
            with open(self.args.oAuthOutputFile, 'w') as f:
                f.write(self.tabs[self.currentTabIndex]['web'].url().toString())
            self.tabs[self.currentTabIndex]['web'].loadFinished.disconnect(self.oAuthLoadFinished)
            if(self.args.oAuthOutputCloseSuccess):
                self.closeWindow()
            else:
                self.tabs[self.currentTabIndex]['web'].load(restoreUrl)

    def resetTimerReset(self):
        logging.info(
            "BrowserResetTimeout is set.")
        self.resetTimeout.resetTimer()

    def resetTimeoutExeeded(self):
        # Reset Page if resetTimeoutExeeded
        python = sys.executable
        os.execl(python, python, *sys.argv) # Restart the Browser
        # self.tabs[self.currentTabIndex]['page'].setParent(None)
        # self.tabs[self.currentTabIndex]['page'].deleteLater()
        # self.tabs[self.currentTabIndex]['page'] = None
        # self.tabs[self.currentTabIndex]['page'] = myQWebEnginePage(self.args, self.dirname, self, False)
        # self.tabs[self.currentTabIndex]['page'].featurePermissionRequested.connect(self.onFeaturePermissionRequested)
        # self.tabs[self.currentTabIndex]['page'].fullScreenRequested.connect(self.toggleFullscreen)
        # self.tabs[self.currentTabIndex]['web'].setPage(self.tabs[self.currentTabIndex]['page'])
        # self.tabs[self.currentTabIndex]['web'].load(self.args.url)

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
                self.tabs[self.currentTabIndex]['web'].parent.clearMask()

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
            self.tabs[self.currentTabIndex]['page'].setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            logging.info("Permission" + str(feature) + " | granted")
            return True
        if (self.args.allowWebcamAccess and feature == QWebEnginePage.Feature.MediaVideoCapture):
            self.tabs[self.currentTabIndex]['page'].setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            logging.info("Permission" + str(feature) + " | granted")
            return True
        if (
                self.args.allowMicAccess and self.args.allowWebcamAccess and feature == QWebEnginePage.Feature.MediaAudioVideoCapture):
            logging.info("Permission" + str(feature) + " | granted")
            self.tabs[self.currentTabIndex]['page'].setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            return True
        if (self.args.allowDesktopSharing and (
                feature == QWebEnginePage.Feature.DesktopVideoCapture or feature == QWebEnginePage.Feature.DesktopAudioVideoCapture)):
            logging.info("Permission" + str(feature) + " | granted")
            self.tabs[self.currentTabIndex]['page'].setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            return True
        if (self.args.allowBrowserNotifications and feature == QWebEnginePage.Feature.Notifications):
            logging.info("Permission" + str(feature) + " | granted")
            self.tabs[self.currentTabIndex]['page'].setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionGrantedByUser)
            return True

        self.tabs[self.currentTabIndex]['page'].setFeaturePermission(url, feature, QWebEnginePage.PermissionPolicy.PermissionDeniedByUser)
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
        self.memoryCapBar.setVisible(True)
        self.memoryCapCloseBar.setValue(int(progress_percent))
        self.memoryCapCloseBar.setFormat("Speicherlimit überschritten, beende Anwendung automatisch in " + str(
            remaining_time_to_close) + " Sekunden")

    def autoRefresh(self):
        self.tabs[self.currentTabIndex]['web'].reload()
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
        self.tabs[self.currentTabIndex]['web'].load(self.addressBar.displayText())

    def downloadProgressChanged(self, bytesReceived, bytesTotal):
        self.downloadProgress.setVisible(True)
        percent = round(100 / bytesTotal * bytesReceived)
        self.downloadProgress.setValue(percent)

        self.downloadProgress.setFormat(str(round(bytesReceived / 1024 / 1024, 2)) + "MB / " + str(
            round(bytesTotal / 1024 / 1024, 2)) + "MB completed")

    def downloadFinished(self):
        self.downloadProgress.setVisible(True)
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
            self.downloadProgress.setVisible(False)

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
                        self.tabs[self.currentTabIndex]['page'].runJavaScript(script)
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
                self.tabs[self.currentTabIndex]['page'].runJavaScript(script)

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
                self.tabs[self.currentTabIndex]['page'].runJavaScript(script)
            self.firstRun = False

    # Print Function
    def printSiteRequest(self):
        logging.info("Test if site is loaded")
        if self.isLoading:
            logging.debug("Site is still loading. Wait for loadFinished before printing")
            self.tabs[self.currentTabIndex]['web'].loadFinished.connect(self.printSiteToPdf)
        else:
            self.printSiteToPdf()

    def printSiteToPdf(self):
        try:
            self.tabs[self.currentTabIndex]['web'].loadFinished.disconnect(self.printSiteToPdf)
        except Exception as e:
            pass

        tempPdfFolder = tempfile.gettempdir() + "/pykib/"
        # check if folder exists
        if not os.path.exists(tempPdfFolder):
            os.makedirs(tempfile.gettempdir() + "/pykib/")

        # create a unique filename
        tempPdfFile = tempPdfFolder + datetime.now().strftime("%Y%m%d%H%M%S") + ".pdf"
        logging.debug("Created temporary PDF for Printing: " + tempPdfFile)
        self.tabs[self.currentTabIndex]['web'].setStyleSheet("body { background: white; }")

        script = "var bodyElement = document.querySelector('body');"
        script += "bodyElement.style.backgroundColor = 'white';"

        self.tabs[self.currentTabIndex]['page'].runJavaScript(script)
        self.tabs[self.currentTabIndex]['web'].printToPdf(tempPdfFile)

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
            try:
                if os.path.isfile(tempPdfFile):
                    os.remove(tempPdfFile)
            except:
                logging.error("Error removing temporary PDF file: " + tempPdfFile)

    def printFinished(self):
        logging.debug("Finished print process")

    def loadingProgressChanged(self, percent):
        # Setting Zoomfactor
        logging.debug("Progress Changed" + str(percent))
        self.tabs[self.currentTabIndex]['web'].setZoomFactor(self.args.setZoomFactor / 100)

        if (not self.args.showLoadingProgressBar):
            self.progressModal.hide()
        elif (not self.progressModal.disabled):
            self.progressModal.show()
            self.progressModal.setValue(percent)
            self.progressModal.changeStyle("loading")

            if (percent == 100):
                self.progressModal.hide()

    # catch defined Shortcuts

    def keyPressEvent(self, event):
        if (self.args.browserResetTimeout):
            self.resetTimerReset()

        keyEvent = event

        shift = event.modifiers() & QtCore.Qt.KeyboardModifier.ShiftModifier
        ctrl = event.modifiers() & QtCore.Qt.KeyboardModifier.ControlModifier
        alt = event.modifiers() & QtCore.Qt.KeyboardModifier.AltModifier

        if (self.args.allowManageTabs and ctrl and keyEvent.key() == QtCore.Qt.Key.Key_T):
            self.addTab()
        if(self.args.enablePrintSupport and ctrl and keyEvent.key() == QtCore.Qt.Key.Key_P):
            logging.info("Print")
            self.printSiteRequest()
        if (shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key.Key_B):
            logging.info("leave by shortcut")
            os._exit(0)
        if ((keyEvent.key() == QtCore.Qt.Key.Key_F5) or (ctrl and keyEvent.key() == QtCore.Qt.Key.Key_R)):
            self.tabs[self.currentTabIndex]['web'].reload()
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
            logging.debug("Open Search Bar")
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
        self.setWindowTitle(self.tabs[self.currentTabIndex]['web'].title())

    def adjustTitleIcon(self):
        self.setWindowIcon(self.tabs[self.currentTabIndex]['web'].icon())
        if self.args.enableTrayMode:
            self.tray.setIcon(self.tabs[self.currentTabIndex]['web'].icon())

    def adjustTabTitle(self, tabIndex):
        logging.debug("Adjust Tab Title for Tab Index " + str(tabIndex))
        try:
            logging.debug("Adjust Tab Title for Tab to " + self.tabs[tabIndex]['web'].title())
            self.tabs[tabIndex]['label'].setText(self.tabs[tabIndex]['web'].title())
        except Exception as e:
            logging.error("Error adjusting Tab Title for Tab Index " + str(tabIndex) + ": " + str(e))

    def adjustTabTitleIcon(self, tabIndex):
        logging.debug("Adjust Tab Title Icon for Tab Index " + str(tabIndex))
        try:
            icon = self.tabs[tabIndex]['web'].icon()
            pixmap = icon.pixmap(16, 16)
            self.tabs[tabIndex]['icon'].setPixmap(pixmap)

        except Exception as e:
            logging.error("Error adjusting Tab Title Icon for Tab Index " + str(tabIndex) + ": " + str(e))

    def adjustAdressbar(self):
        if (
                self.currentTabIndex in self.tabs and
                'web' in self.tabs[self.currentTabIndex] and
                self.args.showAddressBar and
                not self.tabs[self.currentTabIndex]['web'].url().toString().lower().endswith('.pdf')
        ):
            self.addressBar.setText(self.tabs[self.currentTabIndex]['web'].url().toString())

    def openSearchBar(self):
        self.updateSearchModalPosition()
        self.searchText.setSelection(0, self.searchText.maxLength())
        self.searchModal.show()
        self.searchModal.raise_()
        self.searchText.setFocus()

    def closeSearchBar(self):
        self.searchModal.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateSearchModalPosition()
        self.updateLoadingModalPosition()

    def updateSearchModalPosition(self):
        self.searchModal.setFixedWidth(max(int(self.width() * 0.6), 400))
        self.searchModal.move(
            10,
            self.height() - self.searchModal.height() - 10
        )
        self.searchModal.raise_()

    def updateLoadingModalPosition(self):
        self.progressModal.setFixedWidth(self.width())
        self.progressModal.move(
            0,
            self.height() - self.progressModal.height() - 0
        )
        self.progressModal.raise_()

    def searchOnPage(self):
        signalFrom = self.sender().objectName()
        if (signalFrom == "searchUpButton"):
            self.tabs[self.currentTabIndex]['page'].findText(self.searchText.text(), QWebEnginePage.FindFlag.FindBackward)
        else:
            self.tabs[self.currentTabIndex]['page'].findText(self.searchText.text())

    def enableCleanupBrowserProfileOption(self):
        self.tabs[self.currentTabIndex]['page'].enableCleanupBrowserProfileOption()

    def addTab(self, url = False):
        # Create WebView and WebPage
        web = myQWebEngineView(self.args, self.dirname, self)

        if self.browserProfile:
            page = myQWebEnginePage(self.args, self.dirname, self, True, self.browserProfile)
        else:
            page = myQWebEnginePage(self.args, self.dirname, self, True)
            self.browserProfile = page.browserProfile
        web.setPage(page)

        if (self.args.enableTabs):
            # self.currentTabIndex = self.tabWidget.addTab("")
            self.currentTabIndex, iconLabel, textLabel = self.tabWidget.addButtonTab(web, QIcon(os.path.join(self.dirname, 'icons/close.png')), self.args.allowManageTabs)
        else:
            self.currentTabIndex = 0
            iconLabel = QLabel()
            textLabel = QLabel()

        self.tabs[self.currentTabIndex] = {}
        self.tabs[self.currentTabIndex]['web'] = web
        self.tabs[self.currentTabIndex]['page'] = page
        self.tabs[self.currentTabIndex]['icon'] = iconLabel
        self.tabs[self.currentTabIndex]['label'] = textLabel
        self.pageGridLayout.addWidget(web, 4, 0, 1, 0)

        # ###########################################################
        web.urlChanged['QUrl'].connect(self.adjustAdressbar)

        if (self.args.dynamicTitle):
            web.titleChanged.connect(self.adjustTitle)
            web.iconUrlChanged.connect(self.adjustTitleIcon)

        if(self.args.enableTabs):
            # web.titleChanged.connect(partial(self.adjustTabTitle, web.tabIndex))
            # web.iconUrlChanged.connect(partial(self.adjustTabTitleIcon, web.tabIndex))
            web.titleChanged.connect(lambda: self.adjustTabTitle(web.tabIndex))
            web.iconUrlChanged.connect(lambda: self.adjustTabTitleIcon(web.tabIndex))

        # Context Menu
        if not self.args.enableContextMenu:
            web.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)

        # PDF Handling if buttons are generated
        try:
            self.PDFbackButton.clicked.connect(page.closePDFPage)
            self.PDFDownloadButton.clicked.connect(page.pdfDownloadAction)
        except:
            logging.debug("PDF Buttons not found. Skipping PDF Button Setup")

        # Added progress Handling
        web.loadProgress.connect(self.loadingProgressChanged)
        web.loadFinished.connect(self.jsInjection)
        web.loadStarted.connect(self.startLoading)
        web.loadFinished.connect(self.loadFinished)

        web.renderProcessTerminated.connect(self.viewTerminated)
        self.removeDownloadBarTimer = QTimer(self)
        page.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

        if self.args.enablePrintSupport:
            page.printRequested.connect(self.printSiteRequest)

        # Definde Action when Fullscreen ist choosen
        page.fullScreenRequested.connect(self.toggleFullscreen)

        if self.args.closeOnUrl:
            logging.debug('closeOnUrl is set')
            web.urlChanged.connect(self.closeOnUrl)

        if (self.args.browserResetTimeout):
            web.loadProgress.connect(self.resetTimerReset)
            web.urlChanged.connect(self.resetTimerReset)

        # Store initial Restore State
        self.restoreState = self.windowState()

        # Start with url
        if url == False:
            web.load(self.args.url[0])
        else:
            logging.debug("loading url %s" % url)
            web.load(url)

    def onTabChanged(self):
        self.currentTabIndex = self.tabWidget.currentIndex()
        logging.debug("Tab changed to " + str(self.currentTabIndex))
        # Hide all Tabs
        for tabIndex in self.tabs:
            if(self.currentTabIndex != tabIndex):
                logging.debug("Hiding Tab " + str(tabIndex))
                self.tabs[tabIndex]['web'].hide()

        if (self.currentTabIndex in self.tabs):
            self.tabs[self.currentTabIndex]['web'].show()
            self.adjustTitle()
            self.adjustAdressbar()
            self.adjustTitleIcon()
        else:
            logging.error("Tab " + str(self.tabWidget.currentIndex()) + " not found")

    def onTabMoved(self, fromPos, toPos):
        logging.debug("Tab moved from " + str(toPos) + " to " + str(fromPos))

        if fromPos in self.tabs and toPos in self.tabs:
            self.tabs[fromPos], self.tabs[toPos] = self.tabs[toPos], self.tabs[fromPos]
            self.tabs[fromPos]['web'].tabIndex = fromPos
            self.tabs[toPos]['web'].tabIndex = toPos

        logging.debug("Tab from Index  " + str(self.tabs[fromPos]['web'].tabIndex))
        logging.debug("Tab to Index  " + str(self.tabs[toPos]['web'].tabIndex))


    def closeTab(self, index):
        logging.debug("Closing Tab " + str(index))
        if self.tabWidget.count() == 1:
            if self.args.fullscreen:
                logging.info("Ignore Close Tab because fullscreen is set")
                return
            if self.args.enableTrayMode:
                logging.debug("Ignore Close last Tab and hide window because enableTrayMode is set")
                self.hide()
                return

        if index in self.tabs:

            # Remove WebView from GridLayout
            #self.pageGridLayout.removeWidget(self.tabs[index]['web'])
            # Delete WebView and Page
            self.tabs[index]['web'].deleteLater()
            self.tabs[index]['page'].deleteLater()
            del self.tabs[index]

            new_tabs = {}
            for i, key in enumerate(sorted(self.tabs.keys())):
                new_tabs[i] = self.tabs[key]
                new_tabs[i]['web'].tabIndex = i
            self.tabs = new_tabs
            logging.debug("Remaining tabs: " + str(self.tabs))
            # Remove Tab from TabWidget
            self.tabWidget.removeTab(index)

            logging.debug("Tab " + str(index) + " closed")
            if self.tabWidget.count() <= 0:
                logging.debug("No Tabs left. Closing Browser")
                self.closeWindow()

        else:
            logging.error("Tab " + str(index) + " not found")
