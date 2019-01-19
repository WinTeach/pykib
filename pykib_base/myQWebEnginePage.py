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

import subprocess
import os
from functools import partial
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile
from PyQt5 import QtCore, QtWebEngineWidgets, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtCore import QSize, QUrl, QFile

from pprint import pprint

class myQWebEnginePage(QWebEnginePage):
    args = 0
    dirname = 0
    def __init__(self, argsparsed, currentdir):
        global args 
        args = argsparsed
        global dirname
        dirname = currentdir
        QtWebEngineWidgets.QWebEnginePage.__init__(self)
        
        self.profile().downloadRequested.connect(self.on_downloadRequested)
        #Do not persist Cookies
        self.profile().setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
       
        
     #Overrite the default Upload Dialog with a smaller, more limited one   
    def chooseFiles(self, mode, oldFiles, acceptedMimeTypes):            
        #Format acceptedMimeTypes
        nameFiltersString = ""
        for x in acceptedMimeTypes:
            nameFiltersString += "*"+x+" "
        uploadDialog = QFileDialog()
        
        if(args.downloadPath):
            uploadDialog.setDirectory(args.downloadPath)
            
        uploadDialog.setNameFilters([nameFiltersString])
        uploadDialog.setFileMode(QFileDialog.ExistingFile)
        uploadDialog.setAcceptMode(QFileDialog.AcceptOpen)
        
        options = QFileDialog.Options()
        options |= QFileDialog.ReadOnly
        options |= QFileDialog.DontUseNativeDialog
        
        uploadDialog.setOptions(options)
        
        if uploadDialog.exec_():
            fileName = uploadDialog.selectedFiles()
            return fileName            
            
        return [""]

        
        
    def javaScriptConsoleMessage(self, msg, lineNumber, sourceID, category):
        #Ignore JS Failures
        pass
        
    #Certificate Error handling
    def certificateError(self, error):
        if(args.ingoreCertificates):
            print("Certificate Error")
            return True
        else:
            return False
    
    #Download Handle
    @QtCore.pyqtSlot(QtWebEngineWidgets.QWebEngineDownloadItem)
    def on_downloadRequested(self, download):
        downloadHandleHit = False
        old_path = download.path()
        suffix = QtCore.QFileInfo(old_path).suffix()
        if(args.downloadHandle):
            for x in args.downloadHandle:
                handle = x.split("|")
                if(suffix == handle[0]):    
                    downloadHandleHit = True
                    if os.name == 'nt':
                        print(handle[1])
                        filepath = handle[2]+"\\tmp."+suffix    
                    else:
                        filepath = handle[2]+"/tmp."+suffix  
                    download.setPath(filepath)
                    download.accept()
                    download.finished.connect(partial(self.runProcess, handle, filepath, download))                
                
        if(args.download and not downloadHandleHit):            
            #path, _ = QtWidgets.QFileDialog.getSaveFileName(self.view(), "Save File", old_path, "*."+suffix)
            path = ""
            suffix = QtCore.QFileInfo(old_path).suffix()
            downloadDialog = QFileDialog()
                        
            if(args.downloadPath):
                downloadDialog.setDirectory(args.downloadPath)
                downloadDialog.selectFile(os.path.basename(old_path))
            else:
                downloadDialog.selectFile(old_path)
            
            downloadDialog.setFileMode(QFileDialog.AnyFile)
            downloadDialog.setAcceptMode(QFileDialog.AcceptSave)
            downloadDialog.setNameFilters(["*."+suffix])
            
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog            
            downloadDialog.setOptions(options)
                                   
            # dialogLabel = QFileDialog.DialogLabel()
            # dialogLabel |= QFileDialog.FileName
            # downloadDialog.setLabelText(dialogLabel, "Download")
        
            if downloadDialog.exec_():
                path = downloadDialog.selectedFiles()[0]                
                        
            if path:
                download.setPath(path)
                download.accept()
                
    def runProcess(self, handle, filepath, download):
        print(download.isFinished())
        print("Executing:" + "\""+handle[1] +"\" "+filepath);
        subprocess.Popen("\""+handle[1] +"\" "+filepath, shell=True)
    
    def acceptNavigationRequest(self, url: QUrl, typ: QWebEnginePage.NavigationType, is_main_frame: bool):
        if(args.whiteList):
            return self.checkWhitelist(url)
        else:
            return True
        
    def checkWhitelist(self, url:QUrl): 
        global dirname
        currentUrl = url.toString()
        for x in args.whiteList:
            if(currentUrl.startswith(x)):
                return True;
        print("Site "+ currentUrl +" is not whitelisted")       
        
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText( "Site "+ currentUrl +" is not white-listed")
        msg.setWindowTitle("Whitelist Error")
        
            
        backButton = QtWidgets.QPushButton("Go Back")
        backButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')));
        backButton.setIconSize(QSize(24, 24));
        backButton.setObjectName("backButton")
        
        msg.addButton(backButton, QtWidgets.QMessageBox.NoRole )
        
        homeButton = QtWidgets.QPushButton("Go Home")
        homeButton.setIcon(QIcon(os.path.join(dirname, 'icons/home.png')));
        homeButton.setIconSize(QSize(24, 24));
        homeButton.setObjectName("homeButton")
        
        msg.addButton(homeButton, QtWidgets.QMessageBox.NoRole )
        
        msg.show()
        retval = msg.exec_()
        
        if(retval == 0):            
            self.view().stop()
        else:
            self.view().load(args.url)
        
        return False
