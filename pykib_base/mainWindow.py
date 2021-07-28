#!/usr/bin/env python3
# pykib - A PyQt5 based kiosk browser with a minimum set of functionality
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

import sys
import os
import subprocess
import logging

from PyQt5.QtWebEngineWidgets import QWebEnginePage

import pykib_base.ui
import pykib_base.arguments
import pykib_base.mainWindow
import platform

from pykib_base.memoryCap import MemoryCap
from pykib_base.memoryDebug import MemoryDebug
from pykib_base.autoReload import AutoReload

#
from PyQt5 import QtCore
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QKeyEvent

from PyQt5.QtWidgets import QWidget

class MainWindow(QWidget):
    fullScreenState = False

    def __init__(self, transferargs, dirname, parent=None):
        print("running in: " + dirname)
        global args
        args = transferargs
        global firstrun
        firstrun = True

        if(args.remoteBrowserDaemon):
            super(MainWindow, self).__init__(parent,Qt.Tool)
        else:
            super(MainWindow, self).__init__(parent)

        if (args.alwaysOnTop and args.removeWindowControls or args.remoteBrowserDaemon):
            self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.X11BypassWindowManagerHint)

        elif(args.removeWindowControls):
            self.setWindowFlags(Qt.FramelessWindowHint)
        elif(args.alwaysOnTop):
            self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        pykib_base.ui.setupUi(self, args, dirname)
        self.web.load(args.url)
        self.web.renderProcessTerminated.connect(self.viewTerminated)
        self.removeDownloadBarTimer = QTimer(self)
        self.page.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

        #Definde Action when Fullscreen ist choosen
        self.page.fullScreenRequested.connect(self.toggleFullscreen)

        if (args.addMemoryCap):
            logging.info("Starting memory monitoring. Going to close browser when memory usage is over " + str(
                args.addMemoryCap) + "MB")
            self.memoryCapThread = MemoryCap(int(args.addMemoryCap))
            self.memoryCapThread.daemon = True  # Daemonize thread
            self.memoryCapThread.memoryCapExceeded.connect(self.closeBecauseMemoryCap)
            self.memoryCapThread.start()
        if (args.memoryDebug):
            logging.info("Starting memory monitoring")
            self.memoryDebugThread = MemoryDebug()
            self.memoryDebugThread.daemon = True  # Daemonize thread
            self.memoryDebugThread.memoryDebugTick.connect(self.memoryDebugUpdate)
            self.memoryDebugThread.start()
        if (args.autoReloadTimer):
            logging.info(
                "AutoRefreshTimer is set. Going to reload the webpage each" + str(args.autoReloadTimer) + "seconds")
            self.autoRefresher = AutoReload(int(args.autoReloadTimer))
            self.autoRefresher.daemon = True  # Daemonize thread
            self.autoRefresher.autoRefresh.connect(self.autoRefresh)
            self.autoRefresher.start()

    def toggleFullscreen(self, request):
         logging.info("Fullscren Request received")
         logging.info(self.fullScreenState)
         if(not args.fullscreen):
             if (self.fullScreenState):
                logging.info("leave Fullscreen")
                self.fullScreenState = False
                self.showNormal()
             else:
                 logging.info("set Fullscreen")
                 self.fullScreenState = True
                 self.showFullScreen()
         request.accept()

    def enterEvent(self, event):
        #When working with a remote Daemon, the Browse need to get focussed on Enter
        if(args.remoteBrowserDaemon):
            self.activateWindow()

    def onFeaturePermissionRequested(self, url, feature):
        logging.info(
            "Permission" + str(feature) + " requestet and...")
        if (args.allowMicAccess and feature == QWebEnginePage.MediaAudioCapture):
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
            return True
        if (args.allowWebcamAccess and feature == QWebEnginePage.MediaVideoCapture):
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
            return True
        if (args.allowMicAccess and args.allowWebcamAccess and feature == QWebEnginePage.MediaAudioVideoCapture):
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
            return True
        if (args.allowDesktopSharing and (feature == QWebEnginePage.DesktopVideoCapture or feature == QWebEnginePage.DesktopAudioVideoCapture)):
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
            return True

        self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionDeniedByUser)
        logging.info(
            "denied")
        return False

    # Handling crash of wegengineproc
    def viewTerminated(self, status, exitCode):
        if status == QWebEnginePage.NormalTerminationStatus:
            return True
        else:
            logging.error("WebEngineProcess stopped working. Stopping pykib")
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

        if (args.addMemoryCap):
            if ((currentSwapUse + currentMemUse) > int(args.addMemoryCap)):
                self.memoryDebug.changeStyle('memorycap')
            else:
                self.memoryDebug.changeStyle('loading')
            informationstring += "| MemoryCap: " + str(args.addMemoryCap) + " MB"

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

    def loadingProgressChanged(self, percent):
        # Setting Zoomfactor
        self.web.setZoomFactor(args.setZoomFactor / 100)
        global firstrun

        if (not self.progress.disabled):
            self.progress.show()
            self.progress.setValue(percent)
            self.progress.changeStyle("loading")

            if (percent == 100):
                self.progress.hide()

        if (args.enableAutoLogon and firstrun == True):
            firstrun = False
            # if(len(autologin) >= 2):
            username = args.autoLogonUser.replace("\\", "\\\\")
            password = args.autoLogonPassword.replace("\\", "\\\\")
            domain = args.autoLogonDomain
            usernameID = args.autoLogonUserID
            passwordID = args.autoLogonPasswordID
            domainID = args.autoLogonDomainID
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
                            document.onload=login();
                            async function login(){{
                            usernameID = "False";
                            passwordID = "False";
                            domainID = "False";
                                if('{usernameID}' == "False"){{                         
                                    if(document.getElementById('FrmLogin') && document.getElementById('DomainUserName') && document.getElementById('UserPass')){{ 
                                        usernameID = "DomainUserName";
                                        passwordID = "UserPass";                               
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

                                //Wait until usernameID and PasswordID is loaded
                                while(!document.getElementById(usernameID) && !document.getElementById(passwordID)) {{
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
                                //for the Storefront Login the Login Button had to be clicked
                                if(document.getElementById("loginBtn")){{
                                    document.getElementById("loginBtn").click();
                                }}else{{
                                    document.forms[0].submit();
                                }}
                            }}
                            """.format(username=username, password=password, domain=domain, usernameID=usernameID,
                                       passwordID=passwordID, domainID=domainID)
            self.page.runJavaScript(script)

        if (args.enableMouseDrag and percent == 100):
            # logging.info("Mouse Drag Mode is enabled")
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

        # catch defined Shortcuts

    def keyPressEvent(self, event):
        keyEvent = QKeyEvent(event)
        shift = event.modifiers() & QtCore.Qt.ShiftModifier
        ctrl = event.modifiers() & QtCore.Qt.ControlModifier
        alt = event.modifiers() & QtCore.Qt.AltModifier
        if (shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key_B):
            logging.info("leave by shortcut")
            os._exit(0)
        if ((keyEvent.key() == QtCore.Qt.Key_F5) or (ctrl and keyEvent.key() == QtCore.Qt.Key_R)):
            self.web.reload()
            logging.info("Refresh")
        if (args.adminKey and shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key_A):
            logging.info("Hit admin key")
            subprocess.Popen([args.adminKey])
        if (keyEvent.key() == QtCore.Qt.Key_F4):
            logging.info("Alt +F4 is disabled")
        if (ctrl and keyEvent.key() == QtCore.Qt.Key_F):
            self.page.openSearchBar()
        if (keyEvent.key() == QtCore.Qt.Key_Escape):
            self.page.closeSearchBar()

    def closeEvent(self, event):
        if (args.fullscreen):
            event.ignore()

    def adjustTitle(self):
        self.setWindowTitle(self.web.title())

    def adjustTitleIcon(self):
        self.setWindowIcon(self.web.icon())

    def adjustAdressbar(self):
        self.addressBar.setText(self.web.url().toString())
