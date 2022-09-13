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

import time
import logging

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal, pyqtSlot


class RemotePykibUnixSocketKeepAlive(QtCore.QThread):
    keepAliveExeeded = pyqtSignal()
    keepAliveCounter = 5
    keepAliveCounterInit = 5
    keepAliveTimeout = 1000

    def __init__(self, keepAliveTimeout, keepAliveCounter):
        self.keepAliveCounterInit = keepAliveCounter
        self.keepAliveCounter = keepAliveCounter
        self.keepAliveTimeout = keepAliveTimeout/1000

        super(RemotePykibUnixSocketKeepAlive, self).__init__()

    def run(self):
        keepRunning = True
        while(keepRunning):
            logging.debug("------------------------------"+str(self.keepAliveCounter)+"------------------------------")
            if(self.keepAliveCounter > 0):
                self.keepAliveCounter = self.keepAliveCounter - 1;
                time.sleep(self.keepAliveTimeout)
            else:
                self.keepAliveExeeded.emit()
                self.keepAliveCounter = self.keepAliveCounterInit
                keepRunning = False
                self.exit()

    @pyqtSlot()
    def resetKeepAliveTimer(self):
        self.keepAliveCounter = self.keepAliveCounterInit
        logging.debug("UnixSocketKeepAlive Signal received")
