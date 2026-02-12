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
import os
import logging

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal


class OAuthFileHandler(QtCore.QThread):
    oAuthFileChanged = pyqtSignal(str)
    monitorFile = ""
    def __init__(self, monitorFile):
        super(OAuthFileHandler, self).__init__()
        self.monitorFile = monitorFile
        logging.debug("Looking for '" + self.monitorFile + "'")

    def run(self):
        while(True):
            logging.debug("Looking for '" + self.monitorFile + "'")
            if(os.path.isfile(self.monitorFile) and os.path.getsize(self.monitorFile) > 0):
                logging.debug("Read File for '" + self.monitorFile + "'")
                with open(self.monitorFile, 'r') as f:
                    data = f.read()
                    #check if data is a valid url
                    if(data.startswith("http://") or data.startswith("https://")):
                        self.oAuthFileChanged.emit(data)
                    else:
                        logging.error("Invalid URL in '" + self.monitorFile + "'")
                    f.close()
                    ##clear File after Reading
                    with open(self.monitorFile, 'w') as f:
                        f.write("")
                        f.close()
            time.sleep(1)