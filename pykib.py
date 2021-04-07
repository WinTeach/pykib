#!/usr/bin/env python3
# pykib - A PyQt5 based kiosk browser with a minimum set of functionality
# Copyright (C) 2018 Tobias Wintrich
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
import signal
import os
import subprocess
import threading
import logging

from PyQt5.QtWebEngineWidgets import QWebEnginePage

import pykib_base.ui
import pykib_base.arguments
import time
import platform

from pykib_base.memoryCap import MemoryCap
from pykib_base.memoryDebug import MemoryDebug
from pykib_base.autoReload import AutoReload

#
from PyQt5 import QtCore, QtWidgets, QtNetwork
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtCore import QSize, QUrl, QCoreApplication, QTimer
from PyQt5.QtGui import QIcon, QKeyEvent
from PyQt5.QtWidgets import QApplication, QWidget

from PyQt5.QtWidgets import QApplication, QWidget


#Workaround for Problem with relative File Paths

if getattr(sys, 'frozen', False):
    dirname = os.path.dirname(sys.executable)
elif __file__:
    dirname = os.path.dirname(os.path.realpath(__file__))



class MainWindow(QWidget):
    
    def __init__(self, transferargs, parent=None): 
        print("running in: "+dirname)
        global args 
        args = transferargs
        global firstrun
        firstrun = True
        
        super(MainWindow, self).__init__(parent)
        pykib_base.ui.setupUi(self, args, dirname)        
        self.web.load(args.url)
        self.web.renderProcessTerminated.connect(self.viewTerminated)
        self.removeDownloadBarTimer = QTimer(self)
        self.page.featurePermissionRequested.connect(self.onFeaturePermissionRequested)

        if(args.addMemoryCap):
            logging.info("Starting memory monitoring. Going to close browser when memory usage is over "+str(args.addMemoryCap)+"MB")
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
            logging.info("AutoRefreshTimer is set. Going to reload the webpage each" + str(args.autoReloadTimer) + "seconds")
            self.autoRefresher = AutoReload(int(args.autoReloadTimer))
            self.autoRefresher.daemon = True  # Daemonize thread
            self.autoRefresher.autoRefresh.connect(self.autoRefresh)
            self.autoRefresher.start()

    def onFeaturePermissionRequested(self, url, feature):
        logging.info(
            "Permission" + str(feature) + " requestet and...")
        if(args.allowMicAccess and feature == QWebEnginePage.MediaAudioCapture):
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
            return True
        if(args.allowWebcamAccess and feature == QWebEnginePage.MediaVideoCapture):
            self.page.setFeaturePermission(url, feature, QWebEnginePage.PermissionGrantedByUser)
            return True
        if(args.allowMicAccess and args.allowWebcamAccess and feature == QWebEnginePage.MediaAudioVideoCapture):
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
        self.memoryCapCloseBar.setFormat("Speicherlimit überschritten, beende Anwendung automatisch in "+str(remaining_time_to_close)+" Sekunden")

    def autoRefresh(self):
        self.web.reload()
        logging.info("Auto reloading Webpage")

    def memoryDebugUpdate(self, currentMemUse, currentSwapUse):
        informationstring = "Current Memory Usage: "
        if(currentMemUse > 0):
            informationstring += "RAM: "+str(currentMemUse)+" MB "
        if (currentSwapUse > 0):
            informationstring += "| SWAP: "+str(currentSwapUse) + " MB "

        informationstring += "| Total: " + str(currentSwapUse+currentMemUse) + " MB "

        if(args.addMemoryCap):
            if((currentSwapUse+currentMemUse) > int(args.addMemoryCap)):
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
        percent = round(100/bytesTotal*bytesReceived)
        self.downloadProgress.setValue(percent)
        
        self.downloadProgress.setFormat(str(round(bytesReceived/1024/1024,2))+"MB / "+str(round(bytesTotal/1024/1024,2))+"MB completed")

    def downloadFinished(self):        
        self.downloadProgress.show()
        if(platform.system().lower() == "linux"):
            self.downloadProgress.setFormat("Download finished....(Syncing File System)") 
            logging.info("Running 'sync' after download")
            os.system("sync")

            
        self.downloadProgress.setValue(100)            
        
        self.timeToHideDownloadBar = 10
        
        self.removeDownloadBarTimer.setInterval(1000)
        self.removeDownloadBarTimer.timeout.connect(self.onRemoveDownloadBarTimout)
        self.removeDownloadBarTimer.start()
        
    def onRemoveDownloadBarTimout(self):
        self.downloadProgress.setFormat("Download finished....(closing in " +str(self.timeToHideDownloadBar)+"s)") 
        self.timeToHideDownloadBar -= 1
        if(self.timeToHideDownloadBar  == -1):
            self.removeDownloadBarTimer.stop() 
            self.downloadProgress.hide()
        
    def loadingProgressChanged(self, percent):
        #Setting Zoomfactor
        self.web.setZoomFactor(args.setZoomFactor / 100)
        global firstrun

        if(not self.progress.disabled):
            self.progress.show()
            self.progress.setValue(percent)
            self.progress.changeStyle("loading")

            if(percent == 100):
                self.progress.hide()

        if(args.enableAutoLogon and firstrun == True):
                    firstrun = False
                    # if(len(autologin) >= 2):
                    username = args.autoLogonUser.replace("\\","\\\\")
                    password = args.autoLogonPassword.replace("\\","\\\\")
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
                    script =r"""
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
                            """.format(username=username, password=password, domain=domain, usernameID=usernameID, passwordID=passwordID, domainID=domainID)    
                    self.page.runJavaScript(script)

        if(args.enableMouseDrag and percent == 100):
            #logging.info("Mouse Drag Mode is enabled")
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

        #catch defined Shortcuts
    def keyPressEvent(self, event):
        keyEvent = QKeyEvent(event)
        shift = event.modifiers() & QtCore.Qt.ShiftModifier
        ctrl = event.modifiers() & QtCore.Qt.ControlModifier
        alt = event.modifiers() & QtCore.Qt.AltModifier
        if (shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key_B):
            logging.info("leave by shortcut")
            sys.exit()
        if ((keyEvent.key() == QtCore.Qt.Key_F5) or(ctrl and keyEvent.key() == QtCore.Qt.Key_R)):
            self.web.reload()
            logging.info("Refresh")
        if (args.adminKey and shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key_A):
            logging.info("Hit admin key")
            subprocess.Popen([args.adminKey])
        if (keyEvent.key() == QtCore.Qt.Key_F4):	
            logging.info("Alt +F4 is disabled")
        if(ctrl and keyEvent.key() == QtCore.Qt.Key_F):
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

#Handle for Sigterm (CTRL+C)        
def sigint_handler(*args):
        """Handler for the SIGINT signal."""    
        QApplication.quit()
        
def startPykib():
    
    app = QApplication(sys.argv)
    logging.getLogger().setLevel(logging.INFO)

    #Register Sigterm command
    signal.signal(signal.SIGINT, sigint_handler)
    
    parser = pykib_base.arguments.getArgumentParser()
    args = parser.parse_args()

    if(args.configFile):
        if(os.path.isfile(dirname+"/"+args.configFile)):
            args.configFile = dirname+"/"+args.configFile
        elif(not os.path.isfile(args.configFile)):
            print("Configuration File "+args.configFile+" can't be found!")
            sys.exit()
        args = pykib_base.arguments.parseConfigFile(args, parser)

    if(args.url is None and args.defaultURL):
        args.url = args.defaultURL;
    elif(args.url is None and args.defaultURL is None):
        args.url = "https://github.com/WinTeach/pykib";

    #Set Proxy
    if(args.proxy):
        proxy = QtNetwork.QNetworkProxy()
        proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
        proxy.setHostName(args.proxy)
        proxy.setPort(args.proxyPort)
        if (args.proxyUsername and args.proxyPassword):
            proxy.setUser(args.proxyUsername);
            proxy.setPassword(args.proxyPassword);
        elif(args.proxyUsername or args.proxyPassword):
            print("It is not possible to use a proxy username without password")
            sys.exit()

        QtNetwork.QNetworkProxy.setApplicationProxy(proxy)

    view = MainWindow(args)

    if(args.allowWebcamAccess ):
        if(PYQT_VERSION_STR < "5.15.0"):
            logging.info("Webcam Access is only supported with PyQt5 Version 5.15.0 and will be disabled. Currently installed Version:"+ PYQT_VERSION_STR)
            args.allowWebcamAccess = False;

    if (args.allowMicAccess):
        if (PYQT_VERSION_STR < "5.15.0"):
            logging.info("Microfon Access is only supported with PyQt5 Version 5.15.0 and will be disabled. . Currently installed Version:"+ PYQT_VERSION_STR)
            args.allowMicAccess = False;

    if(args.downloadPath ):
        if(os.path.isdir(args.downloadPath) != True):
            print("The folder for downloadPath ("+args.downloadPath+") does not exists or is unreachable")
            sys.exit()

    if(args.setZoomFactor < 25 or args.setZoomFactor > 500):
        print("The Zoom factor must be a value between 25 and 500")
        sys.exit()
        
    #Check autologin Data
    if (args.enableAutoLogon and not (args.autoLogonUser and args.autoLogonPassword)):
        print("When Autologin is enabled at least autoLogonUser and autoLogonPassword has to be set also")
        sys.exit()
        
    #Set Dimensions
    if (args.fullscreen):
        if(len(args.geometry) != 2 and len(args.geometry) != 4):
            print("When geometry is set with maximized or fullsreen only 2 parameters for starting point (#left# and #top#) is allowed")
            sys.exit()
        view.move(args.geometry[0], args.geometry[1])
        view.showFullScreen()
    elif(args.maximized):
        if(len(args.geometry) != 2 and len(args.geometry) != 4):
            print("When geometry is set with maximized or fullsreen only 2 parameters for starting point (#left# and #top#) is allowed")
            sys.exit()
        view.move(args.geometry[0], args.geometry[1])
        view.showMaximized()    
    else:    
        if(len(args.geometry) != 4):
            print("When geometry without maximized or fullsreen is set, you have to define the whole position an screen #left# #top# #width# #height#")
            sys.exit()
        view.show()     
        view.setGeometry(args.geometry[0], args.geometry[1], args.geometry[2], args.geometry[3])
    
    sys.exit(app.exec_())   
  
    
startPykib()