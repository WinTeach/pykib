import psutil
import time
import os
import logging
import platform

from datetime import datetime

from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal


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
