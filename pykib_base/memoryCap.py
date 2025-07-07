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

import psutil
import time
import os
import logging
import platform

from datetime import datetime

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal


class MemoryCap(QtCore.QThread):
    memoryCapExceeded = pyqtSignal(int, int)
    memoryLimit = 0
    def __init__(self, memoryLimit):
        super(MemoryCap, self).__init__()
        self.memoryLimit = memoryLimit

    def run(self):
        process = psutil.Process(os.getpid())
        counter = 1
        is_running = True
        while(is_running):
            if (platform.system().lower() == "linux"):
                currentUsage = (process.memory_full_info().rss + process.memory_full_info().swap) / 1024 / 1024
            else:
                currentUsage = process.memory_info().rss / 1024 / 1024
            if(currentUsage > self.memoryLimit):
                now = datetime.now()
                timestamp = now.strftime("%m/%d/%Y, %H:%M:%S")
                logging.warning(timestamp + ": Memory limit exeeded with current Usage of " + str(currentUsage) + "MB for the " + str(
                    counter) + " time. Will close the Application after 5 Times in a row")
                if(counter >= 5):
                    logging.error(timestamp + ": Memory limit exeeded with current Usage of " + str(currentUsage) + "MB for the " + str(
                        counter) + " time. Closing Application")
                    self.closeWithGraceTime()
                    is_running = False
                else:
                    counter = counter + 1
            elif(counter > 0):
                now = datetime.now()
                timestamp = now.strftime("%m/%d/%Y, %H:%M:%S")
                logging.info(timestamp + ": Memory usage is normal again, resetting counter")
                counter = 0
            time.sleep(5)

    def closeWithGraceTime(self):
        time_to_close = 180
        remaining_time_to_close = time_to_close

        while(remaining_time_to_close > 0):
            self.memoryCapExceeded.emit(time_to_close, remaining_time_to_close)
            remaining_time_to_close = remaining_time_to_close -1
            time.sleep(1)
        os._exit(1)