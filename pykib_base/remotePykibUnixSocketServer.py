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

import asyncio

import json
import logging
import os
import socket


from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal

from pykib_base.remotePykibUnixSocketKeepAlive import RemotePykibUnixSocketKeepAlive

class RemotePykibUnixSocketServer(QtCore.QThread):
    configureInstance = pyqtSignal(int, int, str)
    closeInstance = pyqtSignal(int, int)
    activateInstance = pyqtSignal(int, int)
    moveInstance = pyqtSignal(int, int, list, float)
    changeTabWindow = pyqtSignal(int, int, int)
    setPixmap = pyqtSignal(int, str)

    def __init__(self, config, args):
        super(RemotePykibUnixSocketServer, self).__init__()

        self.config = config
        self.args = args
        self.openSockets = {}

        self.keepAliveThread = RemotePykibUnixSocketKeepAlive(self.args.remoteBrowserKeepAliveInterval, self.args.remoteBrowserKeepAliveErrorLimit)
        self.keepAliveThread.daemon = True  # Daemonize thread
        self.keepAliveThread.keepAliveExeeded.connect(self.keepAliveExeeded)

    def run(self):
        logging.info("UnixSocket: Starting UnixSocket Server:")
        logging.info("  Try creating Socket " + str(self.args.remoteBrowserSocketPath))

        # Make sure the socket does not already exist
        try:
            os.unlink(self.args.remoteBrowserSocketPath)
        except OSError as e:
            if os.path.exists(self.args.remoteBrowserSocketPath):
                raise

        # try to open Socket
        try:
            unixSocket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            unixSocket.bind(self.args.remoteBrowserSocketPath)
            # Listen for incoming connections
            unixSocket.listen(20)
        except Exception as e:
            logging.info(e)

        while True:
            try:
                try:
                    self.keepAliveThread.exit()
                    logging.debug("Stopped Unix Socket KeepAliveThread")
                except Exception as e:
                    logging.debug(e)

                keepOpen = True
                connection, client_address = unixSocket.accept()
                logging.info("Client connected on Unix Socket")

                if(self.args.remoteBrowserKeepAliveInterval != 0):
                    self.keepAliveThread.start()

                while keepOpen:
                    logging.info("Wait for Message")
                    try:
                        connection.settimeout(5)
                        message = connection.recv(256)
                        #receive message until it end with b'\r\n')
                        while not message.endswith(b'\r\n') and message:
                            message += connection.recv(256)

                    except Exception as e:
                        logging.debug(e)
                        keepOpen = False
                        connection.sendall(json.dumps([{
                            "Timed Out": 5}
                        ]).encode() + b'\n')
                        connection.close()
                        continue

                    logging.info("Message Received")
                    if not message:
                        logging.debug("no more data on unix socket...reset Connection")
                        keepOpen = False
                    else:
                        try:
                            logging.debug(message)
                            data = json.loads(message)
                        except Exception as e:
                            logging.debug(e)
                            connection.sendall(b'Unable to read request\n')
                            continue
                        try:
                            if data['action']:
                                True
                        except Exception as e:
                            logging.debug('Action Missing')
                            connection.sendall(b'Action Missing\n')
                            keepOpen = False
                            continue

                        if data['action'] == 'tabAlive':
                            logging.debug("UnixSocket:")
                            logging.debug("  Tab registered")
                            logging.debug("    TabID: " + str(data["tabId"]))
                            logging.debug("    WindowID: " + str(data["windowId"]))
                            logging.debug("------------------------------------------------------------")
                            tab = {
                                "tabId": data["tabId"],
                                "windowId": data["windowId"]
                            }
                            self.openSockets[unixSocket] = tab
                        if data['action'] == 'keepAlive':
                            logging.debug("UnixSocket:")
                            logging.debug("  KeepAliveReceived")
                            logging.debug("------------------------------------------------------------")
                            try:
                                self.keepAliveThread.resetKeepAliveTimer()
                            except Exception as e:
                                logging.debug(e)
                                keepOpen = False
                        elif data['action'] == 'setPixmap':
                            logging.debug("UnixSocket:")
                            logging.debug("  Apply Pixmap on Tab: " + str(data["tabId"]))
                            self.setPixmap.emit(int(data["tabId"]), str(data['pixmap']))
                            logging.info("------------------------------------------------------------")
                            #connection.sendall(json.dumps([self.config]).encode()+b'\n')
                            #keepOpen = False
                            #continue
                        elif data['action'] == 'register':
                            logging.debug("UnixSocket:")
                            logging.debug("  Register:Return config")
                            logging.debug("    Return config")
                            logging.debug("    First Start - Closing all may opened Sessions")
                            self.closeInstance.emit(0, 0)
                            logging.info("------------------------------------------------------------")
                            connection.sendall(json.dumps([self.config]).encode()+b'\n')
                            continue
                        elif data['action'] == 'setTab':
                            logging.debug("UnixSocket:")
                            logging.debug("  set Tab:")
                            logging.debug("    TabID: " + str(data["tabId"]))
                            logging.debug("    WindowID: " + str(data["windowId"]))
                            logging.debug("    URL: " + data['url'])
                            logging.debug("------------------------------------------------------------")
                            self.configureInstance.emit(int(data["tabId"]), int(data["windowId"]), data['url'])
                        elif data['action'] == 'setTabActive':
                            logging.debug("UnixSocket:")
                            logging.debug("  set Tab Active:")
                            logging.debug("    TabID: " + str(data["tabId"]))
                            logging.debug("    WindowID: " + str(data["windowId"]))
                            logging.debug("------------------------------------------------------------")
                            self.activateInstance.emit(int(data["tabId"]), int(data["windowId"]))
                        elif data['action'] == 'closeTab':
                            logging.debug("UnixSocket:")
                            logging.debug("  Closing Tab:")
                            logging.debug("    TabID: " + str(data["tabId"]))
                            logging.debug("    WindowID: " + str(data["windowId"]))
                            logging.debug("------------------------------------------------------------")
                            self.closeInstance.emit(int(data["tabId"]), int(data["windowId"]))
                        elif data['action'] == 'moveTab':
                            logging.debug("UnixSocket:")
                            logging.debug("  Moving Tab:")
                            logging.debug("    TabID: " + str(data["tabId"]))
                            logging.debug("    WindowID: " + str(data["windowId"]))
                            logging.debug("------------------------------------------------------------")
                            if data['geometry'][1] < 0:
                                self.activateInstance.emit(0, int(data["windowId"]))
                            else:
                                self.moveInstance.emit(int(data["tabId"]), int(data["windowId"]), data['geometry'],
                                                       float(data['zoomFactor']))
                        elif data['action'] == 'changeTabWindow':
                            logging.debug("UnixSocket:")
                            logging.debug("  change Tab Window:")
                            logging.debug("    TabID: " + str(data["tabId"]))
                            logging.debug("    oldWindowId: " + str(data["oldWindowId"]))
                            logging.debug("    newWindowId: " + str(data['newWindowId']))
                            logging.debug("------------------------------------------------------------")
                            self.changeTabWindow.emit(int(data["tabId"]), int(data["oldWindowId"]),
                                                      int(data['newWindowId']))
                            self.openSockets[unixSocket]["windowId"] = data['newWindowId']
                        elif data['action'] == 'getRemoteBrowserKeepAliveInterval':
                            logging.debug("UnixSocket:")
                            logging.debug("  RemoteBrowserKeepAliveInterval Requests")
                            logging.debug("------------------------------------------------------------")
                            connection.sendall(str(self.args.remoteBrowserKeepAliveInterval).encode()+b'\n')
                            continue

                        connection.sendall(json.dumps([{
                            "Ack": True}
                        ]).encode() + b'\n')

            except Exception as e:
                try:
                    logging.info(e)
                    self.closeInstance.emit(self.openSockets[unixSocket]["tabId"], self.openSockets[unixSocket]["windowId"])
                    logging.debug("Socket:")
                    logging.debug("  Connection to Tab lost. Closing")
                except Exception as e2:
                    logging.warning(e2)
                    logging.warning(e)

    def keepAliveExeeded(self):
        self.closeInstance.emit(0, 0)