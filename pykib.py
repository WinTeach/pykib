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
import signal
import os
import logging
import tempfile
import atexit
import pprint

import pykib_base.ui
import pykib_base.arguments
import pykib_base.mainWindow
import pykib_base.remotePykibWebsocketServer
import faulthandler

from remotePykib import RemotePykib

#
from PyQt5 import QtNetwork
from PyQt5.Qt import PYQT_VERSION_STR
from PyQt5.QtWidgets import QApplication


class Pykib():
    global args
    global app
    global dirname
    global pykibInstances

    def __init__(self):
        if getattr(sys, 'frozen', False):
            self.dirname = os.path.dirname(sys.executable)
        elif __file__:
            self.dirname = os.path.dirname(os.path.realpath(__file__))

        #register at Exit Function
        atexit.register(self.exitCleanup)

        self.app = QApplication(sys.argv)

        #faulthandler.enable()
        self.startPykib()

    def startPykib(self):
        # Register Sigterm command
        signal.signal(signal.SIGINT, sigint_handler)


        # ----------------------------------------------------------
        # Eval for all relevant Arguments
        # ----------------------------------------------------------

        # Parsing Arguments
        self.args = pykib_base.arguments.getArguments(self.dirname)

        #Set Logging:
        logging.basicConfig(
            format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s %(lineno) s - %(funcName)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
        )
        # logging.getLogger().setLevel(logging.INFO)
        if(self.args.logLevel == "ERROR"):
            logging.getLogger().setLevel(logging.ERROR)
        elif(self.args.logLevel == "WARNING"):
            logging.getLogger().setLevel(logging.WARNING)
        elif(self.args.logLevel == "INFO"):
            logging.getLogger().setLevel(logging.INFO)
        elif(self.args.logLevel == "DEBUG"):
            logging.getLogger().setLevel(logging.DEBUG)

        #Storing Process ID to file if set
        if (self.args.storePid):
            logging.info("Storing current process id:")
            logging.info("  ProcId: " + str(os.getpid()))

            pid_path = tempfile.gettempdir()
            if (self.args.storePidPath):
                pid_path = self.args.storePidPath

            pid_path = pid_path.replace("\\", "/") + "/.pykibLatestProcId"

            with open(pid_path, "w") as text_file:
                text_file.write(str(os.getpid()))

            logging.info("  Storing process id under: " + pid_path)

        # Set Start URL
        if (self.args.url is None and self.args.defaultURL):
            self.args.url = self.args.defaultURL;
        elif (self.args.url is None and self.args.defaultURL is None):
            self.args.url = "https://github.com/WinTeach/pykib";

        # Set Proxy
        if (self.args.proxy):
            proxy = QtNetwork.QNetworkProxy()
            proxy.setType(QtNetwork.QNetworkProxy.HttpProxy)
            proxy.setHostName(self.args.proxy)
            proxy.setPort(self.args.proxyPort)
            if (self.args.proxyUsername and self.args.proxyPassword):
                proxy.setUser(self.args.proxyUsername);
                proxy.setPassword(self.args.proxyPassword);
            elif (self.args.proxyUsername or self.args.proxyPassword):
                print("It is not possible to use a proxy username without password")
                sys.exit()

            QtNetwork.QNetworkProxy.setApplicationProxy(proxy)

        # Allow Webcam and Microfon Support. Warn if PyQt Version is to old
        if (self.args.allowWebcamAccess):
            if (PYQT_VERSION_STR < "5.15.0"):
                logging.info(
                    "Webcam Access is only supported with PyQt5 Version 5.15.0 and will be disabled. Currently installed Version:" + PYQT_VERSION_STR)
                self.args.allowWebcamAccess = False;

        if (self.args.allowMicAccess):
            if (PYQT_VERSION_STR < "5.15.0"):
                logging.info(
                    "Microfon Access is only supported with PyQt5 Version 5.15.0 and will be disabled. . Currently installed Version:" + PYQT_VERSION_STR)
                self.args.allowMicAccess = False;

        # Check if a configred Download Location exists
        if (self.args.downloadPath):
            if (os.path.isdir(self.args.downloadPath) != True):
                print("The folder for downloadPath (" + self.args.downloadPath + ") does not exists or is unreachable")
                sys.exit()

        # Parse Download Handle
        if (self.args.downloadHandle):
            tempDownloadHandle = []
            for x in self.args.downloadHandle:
                handle = x.split("|")
                if(len(handle) != 0):
                    tempDownloadHandle.append(handle)
            self.args.downloadHandle = tempDownloadHandle


        # Check if a configred temporarySessionTokenPath Location exists
        if (self.args.temporarySessionTokenPath):
            if (os.path.isdir(self.args.temporarySessionTokenPath) != True):
                print("The folder for storing the temporary Session Token (" + self.args.temporarySessionTokenPath + ") does not exists or is unreachable")
                sys.exit()

        # Check if a set Zoom Factor is inside the allowed area
        if (self.args.setZoomFactor < 25 or self.args.setZoomFactor > 500):
            print("The Zoom factor must be a value between 25 and 500")
            sys.exit()

        # Calculate Screen Offset when normalizeGeometry is set
        self.args.screenOffsetLeft = 0
        try:
            if (self.args.normalizeGeometry):
                    screens = self.app.screens()
                    for key in screens:
                        if (self.app.primaryScreen() == key):
                            self.args.screenOffsetLeft = key.availableGeometry().left()
        except:
            self.args.screenOffsetLeft = 0

        # ----------------------------------------------------------
        # Define System application Name
        # ----------------------------------------------------------
        self.app.setApplicationName(self.args.systemApplicationName)

        # ----------------------------------------------------------
        # Switch between Remote Daemon an Default Pykib
        # ----------------------------------------------------------
        if (self.args.remoteBrowserDaemon):
            RemotePykib(self.args, self.dirname)

        # ----------------------------------------------------------
        # Eval Arguments for da Default Pykib Start
        # ----------------------------------------------------------

        # Check autologin Data
        if (self.args.enableAutoLogon and not (self.args.autoLogonUser and self.args.autoLogonPassword)):
            print("When Autologin is enabled at least autoLogonUser and autoLogonPassword has to be set also")
            sys.exit()

        view = pykib_base.mainWindow.MainWindow(self.args, self.dirname)

        # Set Dimensions
        if (self.args.fullscreen):
            if (len(self.args.geometry) != 2 and len(self.args.geometry) != 4):
                print(
                    "When geometry is set with maximized or fullsreen only 2 parameters for starting point (#left# and #top#) is allowed")
                sys.exit()
            view.move(self.args.geometry[0] + self.args.screenOffsetLeft, self.args.geometry[1])
            view.showFullScreen()
        elif (self.args.maximized):
            if (len(self.args.geometry) != 2 and len(self.args.geometry) != 4):
                print(
                    "When geometry is set with maximized or fullsreen only 2 parameters for starting point (#left# and #top#) is allowed")
                sys.exit()
            view.move(self.args.geometry[0] + self.args.screenOffsetLeft, self.args.geometry[1])
            view.showMaximized()
        else:
            if (len(self.args.geometry) != 4):
                print(
                    "When geometry without maximized or fullsreen is set, you have to define the whole position an screen #left# #top# #width# #height#")
                sys.exit()
            view.show()
            view.setGeometry(self.args.geometry[0] + self.args.screenOffsetLeft, self.args.geometry[1], self.args.geometry[2], self.args.geometry[3])

        sys.exit(self.app.exec_())

    def exitCleanup(self):
        logging.info("Closing Pykib, doing cleanup:")

        #Delete Session Token File if set
        if (self.args.useTemporarySessionToken):
            logging.info("  Cleanup session token file")
            token_path = tempfile.gettempdir()
            if (self.args.temporarySessionTokenPath):
                token_path = self.args.temporarySessionTokenPath
            token_path = token_path.replace("\\", "/") + "/.pykibTemporarySessionToken"

            try:
                stored_token = open(token_path, "r").read()
                if(stored_token == self.args.remoteBrowserSessionToken):

                    logging.info("  Removing token file at "+token_path)
                    os.remove(token_path)
                else:
                    logging.info("  Session token in file "+token_path+" is not the same like the current used - doing nothing")
            except Exception as e:
                logging.info("No Stored Session Token found at "+token_path)
                logging.warning(e)

        if (self.args.storePid):
            logging.info("  Cleanup process id file")
            pid_path = tempfile.gettempdir()
            if (self.args.storePidPath):
                pid_path = self.args.storePidPath
            pid_path = pid_path.replace("\\", "/") + "/.pykibLatestProcId"

            try:
                stored_pid = open(pid_path, "r").read()
                if(stored_pid == str(os.getpid())):
                    logging.info("  Removing pocess id file at "+pid_path)
                    os.remove(pid_path)
                else:
                    logging.info("  Stored pid id in file "+pid_path+" is not the same like the current process id")
            except Exception as e:
                logging.info("No process id file found at "+pid_path)
                logging.warning(e)

        logging.info("Cleanup ended... goodbye")




#Handle for Sigterm (CTRL+C)        
def sigint_handler(*args):
        """Handler for the SIGINT signal."""    
        QApplication.quit()

Pykib()