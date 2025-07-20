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

import time
import logging

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal

class ResetTimeout(QtCore.QThread):
    resetTimeoutExeeded = pyqtSignal()
    autoReloadTimer = 0

    def __init__(self, resetTimeout):
        super(ResetTimeout, self).__init__()
        self.resetTimeout = resetTimeout

    def run(self):
        self.secondsLeft = self.resetTimeout;
        while(True):
            if(self.secondsLeft > 0):
                self.secondsLeft = self.secondsLeft - 1;
                logging.debug("browserResetTimeout time left: " + str(self.secondsLeft))
                time.sleep(1)
            else:
                self.resetTimeoutExeeded.emit()
                logging.debug("browserResetTimeout exeeded")
                self.secondsLeft = self.resetTimeout;
                time.sleep(1);

    def resetTimer(self):
        self.secondsLeft = self.resetTimeout
        logging.debug("browserResetTimeout cleared")