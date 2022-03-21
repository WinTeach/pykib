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
import platform

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal


class MemoryDebug(QtCore.QThread):
    memoryDebugTick = pyqtSignal(int, int)

    def __init__(self):
        super(MemoryDebug, self).__init__()

    def run(self):
        process = psutil.Process(os.getpid())
        is_running = True
        while(is_running):
            if (platform.system().lower() == "linux"):
                self.memoryDebugTick.emit(int(process.memory_full_info().rss / 1024 / 1024), int(process.memory_full_info().swap / 1024 / 1024));
            else:
                self.memoryDebugTick.emit(int(process.memory_info().rss / 1024 / 1024), 0)
            time.sleep(5)
