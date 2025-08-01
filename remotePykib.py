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
import base64
import io
import sys
import os
import logging
import random
import string
import tempfile
import time

import pykib_base.ui
import pykib_base.arguments
import pykib_base.mainWindow
import pykib_base.remotePykibWebsocketServer
import pykib_base.remotePykibUnixSocketServer

from PyQt6.QtGui import QIcon, QAction, QPixmap
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu


#Workaround for Problem with relative File Paths
class RemotePykib():
    def __init__(self, args, dirname, tray):
        self.args = args
        self.dirname = dirname
        self.app = QApplication(sys.argv)
        self.tray = tray
        self.pykibInstances = {}
        self.browserProfile = None

        self.startRemotePykib()

    def startRemotePykib(self):
        logging.info("Pykib Remote Browser Daemon Mode")

        self.app.setQuitOnLastWindowClosed(False)

        # Build Configuration Array for Plugin
        config = {
            "remotingList": self.args.remotingList.split(" "),
            "allowUserBasedRemoting": self.args.allowUserBasedRemoting,
            "remoteBrowserMoveInterval": self.args.remoteBrowserMoveInterval,
            "remoteDaemonProtocolVersion": self.args.remoteDaemonProtocolVersion,
            "remoteBrowserPixmapMonitorInterval": self.args.remoteBrowserPixmapMonitorInterval,
        }

        # Configure a Remote Pykib Tray App
        self.tray.setVisible(True)
        self.tray.setToolTip("Remote Browser Daemon")

        # Create the menu
        menu = QMenu()

        # Add a Quit option to the menu.
        quit = QAction("Close Remote Browser Daemon")
        quit.triggered.connect(sys.exit)
        menu.addAction(quit)

        # Add the menu to the tray
        self.tray.setContextMenu(menu)

        if(self.args.remoteBrowserSocketPath):
            # Create and Start the UnixSocket Server Thread
            socketServer = pykib_base.remotePykibUnixSocketServer.RemotePykibUnixSocketServer(config,
                                                                                               self.args)
        else:
            #Create Temp Session Token if Option is set
            if(self.args.useTemporarySessionToken):
                logging.info("Temporary Session Token is used:")
                characters = string.ascii_letters + string.digits
                self.args.remoteBrowserSessionToken = ''.join(random.choice(characters) for i in range(128))
                logging.info("  Token: " + self.args.remoteBrowserSessionToken)

                token_path = tempfile.gettempdir()
                if (self.args.temporarySessionTokenPath):
                    token_path = self.args.temporarySessionTokenPath

                token_path = token_path.replace("\\", "/")+"/.pykibTemporarySessionToken"

                with open(token_path, "w") as text_file:
                    text_file.write(self.args.remoteBrowserSessionToken)

                logging.info("  Storing Token under: " + token_path)

            # Create and Start the Websocket Server Thread
            socketServer = pykib_base.remotePykibWebsocketServer.RemotePykibWebsocketServer(config, self.args.remoteBrowserSessionToken,
                                                                           self.args.remoteBrowserPort)

        socketServer.daemon = True  # Daemonize thread
        socketServer.configureInstance.connect(self.configureInstance)
        socketServer.closeInstance.connect(self.closeInstance)
        socketServer.activateInstance.connect(self.activateInstance)
        socketServer.moveInstance.connect(self.moveInstance)
        socketServer.changeTabWindow.connect(self.changeTabWindow)
        socketServer.setPixmap.connect(self.setPixmap)
        socketServer.start()

        sys.exit(self.app.exec())

    def configureInstance(self, tabId, windowId, url):
        logging.info("RemotePykib:")

        #Create Window Array if not exist
        try:
            self.pykibInstances[windowId]
        except:
            self.pykibInstances[windowId] = {}

        if(tabId in self.pykibInstances[windowId] and self.pykibInstances[windowId][tabId].web):
            logging.info("  Tab found, set as CurrentView:"+str(tabId))
            logging.info("    TabID: " + str(tabId))
            logging.info("    WindowID: " + str(windowId))
            currentView = self.pykibInstances[windowId][tabId]
            try:
                currentView.web.load(url)
            except:
                logging.info("    Tab should be availeable but is not. May be closed manually. creating new: " + str(tabId))
                self.args.url = url
                if self.browserProfile:
                    currentView = pykib_base.mainWindow.MainWindow(self.args, self.dirname, None, self.tray, self.browserProfile)
                else:
                    currentView = pykib_base.mainWindow.MainWindow(self.args, self.dirname, None, self.tray)
                    self.browserProfile = currentView.browserProfile
                self.pykibInstances[windowId][tabId] = currentView
        else:
            logging.info("  Tab not found, create new an set as CurrentView:" + str(tabId))
            logging.info("    TabID: " + str(tabId))
            logging.info("    WindowID: " + str(windowId))
            self.args.url = url
            if self.browserProfile:
                currentView = pykib_base.mainWindow.MainWindow(self.args, self.dirname, None, self.tray,
                                                               self.browserProfile)
            else:
                currentView = pykib_base.mainWindow.MainWindow(self.args, self.dirname, None, self.tray)
                self.browserProfile = currentView.browserProfile
            self.pykibInstances[windowId][tabId] = currentView

        for key in self.pykibInstances[windowId]:
            if(key != tabId):
                logging.info("  Hiding Tabs with:")
                logging.info("    TabID: " + str(key))
                logging.info("    WindowID: " + str(windowId))

                currentView.hide()

        logging.info("  Showing CurrenView")
        logging.info("------------------------------------------------------------")
        currentView.show()
        #currentView.activateWindow()

    def closeInstance(self, tabId, windowId):
        logging.info("RemotePykib:")
        try:
            if(tabId == 0 and windowId == 0):
                logging.info("  Closing All Tabs")
                try:
                    for window in self.pykibInstances:
                        try:
                            for tab in self.pykibInstances[window]:
                                try:
                                    self.pykibInstances[window][tab].web.close()
                                    self.pykibInstances[window][tab].close()
                                except Exception as f:
                                    logging.debug(f)
                        except Exception as i:
                            logging.warning(i)
                except Exception as e:
                    logging.warning(e)
                self.pykibInstances = {}
            elif(tabId == 0):
                logging.info("  Closing All Tabs:")
                logging.info("    WindowID: " + str(windowId))
                try:
                    for tab in self.pykibInstances[windowId]:
                        logging.info("      Tab closed: " + str(tab))
                        self.pykibInstances[windowId][tab].web.close()
                        self.pykibInstances[windowId][tab].close()
                except Exception as e:
                    logging.warning(e)
            elif (tabId in self.pykibInstances[windowId]):
                logging.info("  Closing Tabs:")
                logging.info("    TabID: " + str(tabId))
                logging.info("    WindowID: " + str(windowId))
                self.pykibInstances[windowId][tabId].web.close()
                self.pykibInstances[windowId][tabId].close()
                del self.pykibInstances[windowId][tabId]
        except Exception as e:
            logging.warning(e)
            return False
        logging.info("------------------------------------------------------------")

    def activateInstance(self, tabId, windowId):
        logging.info("RemotePykib:")
        logging.info("  Bringing Tab in Front")
        logging.info("    TabID: " + str(tabId))
        logging.info("    WindowID: " + str(windowId))

        try:
            if (tabId in self.pykibInstances[windowId]):
                logging.info("      Tab found. Set as CurrentView")
                self.pykibInstances[windowId][tabId].show()
                #self.pykibInstances[windowId][tabId].activateWindow()
            else:
                logging.info("      Tab not found - Nothing to bring in Front.")

            for tab in self.pykibInstances[windowId]:
                if (tab != tabId):
                    logging.info("  Hiding Tabs with:")
                    logging.info("    TabID: " + str(tab))
                    logging.info("    WindowID: " + str(windowId))
                    try:
                        self.pykibInstances[windowId][tab].hide()
                    except Exception as e:
                        logging.info("  Error, Tab not found")
        except Exception as e:
            logging.info("  Error, WindowID not configured")
        logging.info("------------------------------------------------------------")

    def moveInstance(self, tabId, windowId, geometry, zoomFactor = 1):
        logging.debug("RemotePykib:")
        logging.debug("  Moving/Resizing Tab")
        logging.debug("    TabID: " + str(tabId))
        logging.debug("    WindowID: " + str(windowId))
        try:
            if(tabId in self.pykibInstances[windowId]):
                logging.debug("      Tab found. Moving/Resizing")
                if(self.args.ignoreSystemDpiSettings == True):
                    self.args.setZoomFactor = zoomFactor * 100
                    dpi = 1
                else:
                    dpi = self.pykibInstances[windowId][tabId].devicePixelRatio()
                #self.pykibInstances[windowId][tabId].web.setZoomFactor(zoomFactor)
                logging.debug("      1")
                logging.debug(geometry)
                logging.debug(self.args.screenOffsetLeft)
                self.pykibInstances[windowId][tabId].setGeometry(int(geometry[0] / dpi + self.args.screenOffsetLeft), int(geometry[1] / dpi), int(geometry[2] / dpi), int(geometry[3] / dpi))
                logging.debug("      2")
                self.pykibInstances[windowId][tabId].show()
                logging.debug("      3")
                #self.pykibInstances[windowId][tabId].activateWindow()
            else:
                logging.debug("      Tab not found.")
        except Exception as e:
            logging.info(e)
            logging.info("  Error, WindowID not found")

    def changeTabWindow(self, tabId, oldWindowId, newWindowId):
        logging.info("RemotePykib:")
        logging.info("  Change Tab Window")
        logging.info("    TabID: " + str(tabId))
        logging.info("    oldWindowId: " + str(oldWindowId))
        logging.info("    newWindowId: " + str(newWindowId))
        try:
            if(tabId in self.pykibInstances[oldWindowId]):
                logging.debug("      Tab found. Move to new Window")
                try:
                    # Array for newWindowId found
                    self.pykibInstances[newWindowId]
                except:
                    # No Array for newWindowId exist, creating one
                    self.pykibInstances[newWindowId] = {}

                #Move Tab from old to new Window Id
                self.pykibInstances[newWindowId][tabId] = self.pykibInstances[oldWindowId][tabId]
                del self.pykibInstances[oldWindowId][tabId]
            else:
                logging.info("      Tab not found.")
        except Exception as e:
            logging.info(e)


    def setPixmap(self, tabId, pixmapData):
        logging.info("RemotePykib:")
        logging.info("  Apply Pixmap")
        logging.info("    TabID: " + str(tabId))
        try:
            for pykibInstance in self.pykibInstances:
                if(tabId in self.pykibInstances[pykibInstance]):
                    pixmap = QPixmap()
                    pixmap.loadFromData(base64.b64decode(pixmapData))
                    self.pykibInstances[pykibInstance][tabId].web.parent.setMask(pixmap.mask())
                    self.pykibInstances[pykibInstance][tabId].web.parent.mask()
        except Exception as e:
            logging.info(e)
