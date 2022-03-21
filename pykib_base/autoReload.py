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

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal

class AutoReload(QtCore.QThread):
    autoRefresh = pyqtSignal()
    autoReloadTimer = 0

    def __init__(self, autoReloadTimer):
        super(AutoReload, self).__init__()
        self.autoReloadTimer = autoReloadTimer

    def run(self):
        secondsLeft = self.autoReloadTimer;
        while(True):
            if(secondsLeft > 0):
                secondsLeft = secondsLeft - 1;
                time.sleep(1)
            else:
                self.autoRefresh.emit()
                secondsLeft = self.autoReloadTimer;
                time.sleep(1);