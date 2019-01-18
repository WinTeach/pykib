#!/usr/bin/env python3
# pykib - A PyQt5 based kiosk browser with a minimum set of functionality
# Copyright (C) 2018 Tobias Wintrich
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

import sys
import signal
import os
import subprocess
import pykib_base.ui
import pykib_base.arguments

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QSize, QUrl, QCoreApplication, QTimer
from PyQt5.QtGui import QIcon, QKeyEvent
from PyQt5.QtWidgets import QApplication, QWidget

#Workaround for Problem with relative File Paths

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    dirname = os.path.dirname(sys.executable)
elif __file__:
    dirname = os.path.dirname(os.path.realpath(__file__))
    
# def signal_handler(signal, frame):
    # os.kill()
# signal.signal(signal.SIGINT, signal_handler)  
#signal.signal(signal.SIGINT, signal.SIG_DFL)  



class MainWindow(QWidget):


    def __init__(self, transferargs, parent=None): 
        global args 
        args = transferargs
        super(MainWindow, self).__init__(parent)
        
        pykib_base.ui.setupUi(self, args, dirname)
        
        self.web.load(args.url)               
        
    def pressed(self):
        self.web.load(self.addressBar.displayText())
    
    #catch defined Shortcuts
    def keyPressEvent(self, event):
        keyEvent = QKeyEvent(event)
        shift = event.modifiers() & QtCore.Qt.ShiftModifier
        ctrl = event.modifiers() & QtCore.Qt.ControlModifier
        alt = event.modifiers() & QtCore.Qt.AltModifier
        if (shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key_B):
            print("leave by shortcut")
            sys.exit()
        if (args.adminKey and shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key_A):
            print("Hit admin key")
            subprocess.Popen([args.adminKey])
        if (keyEvent.key() == QtCore.Qt.Key_F4):	
            print("Alt +F4 is disabled")	
            
    def closeEvent(self, event):
        if (args.fullscreen):
            event.ignore()

    def adjustTitle(self):
        self.setWindowTitle(self.web.title())   
        
    def adjustTitleIcon(self):
        self.setWindowIcon(self.web.icon()) 
        
    def adjustAdressbar(self):
        self.addressBar.setText(self.web.url().toString())

#Handle for Sigterm (CTRL+C)        
def sigint_handler(*args):
        """Handler for the SIGINT signal."""    
        QApplication.quit()
        
def startPykib():
    
    app = QApplication(sys.argv)   
    
    #Register Sigterm command
    signal.signal(signal.SIGINT, sigint_handler)
    
    #Timer for calling the python interpreter every 1000, without this the Sigterm command won't be handled while the QT Loop is running
    timer = QTimer()
    timer.start(1000)  # You may change this if you wish.
    timer.timeout.connect(lambda: None)

    parser = pykib_base.arguments.getArgumentParser()
    args = parser.parse_args()
    
    view = MainWindow (args)   
    
    if(args.downloadPath ):
        if(os.path.isdir(args.downloadPath) != True):
            print("The folder for downloadPath ("+args.downloadPath+") does not exists or is unreachable")
            sys.exit()    
        
 
    #Set Dimensions
    if (args.fullscreen):
        if(len(args.geometry) is not 2 and len(args.geometry) is not 4):
            print("When geometry is set with maximized or fullsreen only 2 parameters for starting point (#left# and #top#) is allowed")
            sys.exit()
        view.move(args.geometry[0], args.geometry[1])
        view.showFullScreen()
    elif(args.maximized):
        if(len(args.geometry) is not 2 and len(args.geometry) is not 4):
            print("When geometry is set with maximized or fullsreen only 2 parameters for starting point (#left# and #top#) is allowed")
            sys.exit()
        view.move(args.geometry[0], args.geometry[1])
        view.showMaximized()    
    else:    
        if(len(args.geometry) is not 4):
            print("When geometry without maximized or fullsreen is set, you have to define the whole position an screen #left# #top# #width# #height#")
            sys.exit()
        view.show()     
        view.setGeometry(args.geometry[0], args.geometry[1], args.geometry[2], args.geometry[3])
    
    sys.exit(app.exec_())   
  
    
startPykib()