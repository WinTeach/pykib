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

import websockets
import json
import logging
import time

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal


class RemotePykibWebsocketServer(QtCore.QThread):
    configureInstance = pyqtSignal(int, int, str)
    closeInstance = pyqtSignal(int, int)
    activateInstance = pyqtSignal(int, int)
    moveInstance = pyqtSignal(int, int, list, float)
    changeTabWindow = pyqtSignal(int, int, int)

    def __init__(self, config, sessionToken, port):
        super(RemotePykibWebsocketServer, self).__init__()
        self.config = config
        self.port = port
        self.sessionToken = sessionToken
        self.openSockets = {}

    def run(self):
        logging.info("Websocket: Starting Websocket Server:")
        logging.info("  Listening on 0.0.0.0:"+str(self.port))

        websockloop = asyncio.new_event_loop()
        start_server = websockets.serve(self.handler, "0.0.0.0", self.port, loop=websockloop)
        websockloop.run_until_complete(start_server)
        websockloop.run_forever()

    async def handler(self, websocket, path):
        try:
            keepOpen = True
            while keepOpen:
                message = await websocket.recv()
                data = json.loads(message)

                if(not self.sessionToken or self.sessionToken == data['sessionToken']):
                    if (data['action'] == 'tabAlive'):
                        logging.info("Websocket:")
                        logging.info("  Tab registered")
                        logging.info("    TabID: " + str(data["tabId"]))
                        logging.info("    WindowID: " + str(data["windowId"]))
                        logging.info("------------------------------------------------------------")
                        tab = {
                            "tabId": data["tabId"],
                            "windowId": data["windowId"]
                        }
                        self.openSockets[websocket] = tab
                    if (data['action'] == 'register'):
                        logging.info("Websocket:")
                        logging.info("  Register:Return config")
                        logging.info("    Return config")
                        logging.info("    First Start - Closing all may opened Sessions")
                        self.closeInstance.emit(0,0)
                        logging.info("------------------------------------------------------------")
                        await websocket.send(json.dumps(self.config))
                        keepOpen = False;
                    elif(data['action'] == 'setTab'):
                        logging.info("Websocket:")
                        logging.info("  set Tab:")
                        logging.info("    TabID: " + str(data["tabId"]))
                        logging.info("    WindowID: " + str(data["windowId"]))
                        logging.info("    URL: " + data['url'])
                        logging.info("------------------------------------------------------------")
                        keepOpen = False;
                        self.configureInstance.emit(int(data["tabId"]), int(data["windowId"]), data['url'])
                    elif(data['action'] == 'setTabActive'):
                        logging.info("Websocket:")
                        logging.info("  set Tab Active:")
                        logging.info("    TabID: " + str(data["tabId"]))
                        logging.info("    WindowID: " + str(data["windowId"]))
                        logging.info("------------------------------------------------------------")
                        self.activateInstance.emit(int(data["tabId"]), int(data["windowId"]))
                    elif(data['action'] == 'closeTab'):
                        logging.info("Websocket:")
                        logging.info("  Closing Tab:")
                        logging.info("    TabID: " + str(data["tabId"]))
                        logging.info("    WindowID: " + str(data["windowId"]))
                        logging.info("------------------------------------------------------------")
                        try:
                            data["windowId"]["windowId"]
                            self.closeInstance.emit(int(data["tabId"]), int(data["windowId"]["windowId"]))
                        except:
                            self.closeInstance.emit(int(data["tabId"]), int(data["windowId"]))
                    elif(data['action'] == 'closeAllTabs'):
                        logging.info("Websocket:")
                        logging.info("  Closing All Tabs:")
                        logging.info("    WindowID: " + str(data["windowId"]))
                        logging.info("------------------------------------------------------------")
                        self.closeInstance.emit(0, int(data["windowId"]))
                    elif(data['action'] == 'moveTab'):
                        logging.debug("Websocket:")
                        logging.debug("  Moving Tab:")
                        logging.debug("    TabID: " + str(data["tabId"]))
                        logging.debug("    WindowID: " + str(data["windowId"]))
                        logging.debug("------------------------------------------------------------")
                        if (data['geometry'][1] < 0):
                            self.activateInstance.emit(0, int(data["windowId"]))
                        else:
                            self.moveInstance.emit(int(data["tabId"]), int(data["windowId"]), data['geometry'], float(data['zoomFactor']))
                    elif(data['action'] == 'changeTabWindow'):
                        logging.info("Websocket:")
                        logging.info("  change Tab Window:")
                        logging.info("    TabID: " + str(data["tabId"]))
                        logging.info("    oldWindowId: " + str(data["oldWindowId"]))
                        logging.info("    newWindowId: " + str(data['newWindowId']))
                        logging.info("------------------------------------------------------------")
                        self.changeTabWindow.emit(int(data["tabId"]), int(data["oldWindowId"]), int(data['newWindowId']))
                        self.openSockets[websocket]["windowId"] = data['newWindowId']
                else:
                    await websocket.send(json.dumps({"ErrorCode": 1}))
                    logging.warning("Websocket:")
                    logging.warning("  Invalid Session Token Received:")
                    logging.warning("------------------------------------------------------------")
        except Exception as e:
            try:
                self.closeInstance.emit(self.openSockets[websocket]["tabId"], self.openSockets[websocket]["windowId"])
                logging.info("Websocket:")
                logging.info("  Connection to Tab lost. Closing")
                logging.info(self.openSockets[websocket]["tabId"])
                logging.info(self.openSockets[websocket]["windowId"])
            except Exception as e2:
                logging.warning(e2)
            if(e == websockets.exceptions.ConnectionClosedError):
                logging.warning("Websocket:")
                logging.warning("  Connection closed with error - Closing all Windows")
                logging.warning("------------------------------------------------------------")
                self.closeInstance.emit(0, 0)
            elif(e.__class__ != websockets.exceptions.ConnectionClosedOK):
                logging.info("Websocket:")
                logging.info("  Connection closed cleanly")
                logging.info("------------------------------------------------------------")
            else:
                logging.warning(e)





