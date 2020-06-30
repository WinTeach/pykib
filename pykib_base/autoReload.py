import psutil
import time
import os
import logging
import platform

from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal

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
                logging.info(
                    str(secondsLeft))
                time.sleep(1)
            else:
                self.autoRefresh.emit()
                secondsLeft = self.autoReloadTimer;
                time.sleep(1);