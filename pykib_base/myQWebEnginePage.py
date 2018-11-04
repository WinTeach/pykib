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

from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile
from PyQt5 import QtCore, QtWebEngineWidgets
from PyQt5.QtCore import QSize, QUrl, QFile

class myQWebEnginePage(QWebEnginePage):
    def __init__(self, *args, **kwargs):
        QtWebEngineWidgets.QWebEnginePage.__init__(self, *args, **kwargs)
        self.profile().downloadRequested.connect(self.on_downloadRequested)
        #Do not persist Cookies
        self.profile().setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
    
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
        for x in args.downloadHandle:
            handle = x.split("|")
            if(suffix == handle[0]):    
                downloadHandleHit = True
                filepath = handle[2]+"/tmp."+suffix                
                download.setPath(filepath)
                download.accept()
                download.finished.connect(partial(self.runProcess, handle, filepath, download))                
                
        if(args.download and not downloadHandleHit):            
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self.view(), "Save File", old_path, "*."+suffix)
            if path:
                download.setPath(path)
                download.accept()
                
    def runProcess(self, handle, filepath, download):
        print(download.isFinished())
        print("Executing:" +handle[1] +" "+filepath);
        subprocess.Popen(handle[1] +" "+filepath, shell=True)
    
    def acceptNavigationRequest(self, url: QUrl, typ: QWebEnginePage.NavigationType, is_main_frame: bool):
        if(args.whiteList):
            return self.checkWhitelist(url)
        else:
            return True
        
    def checkWhitelist(self, url:QUrl): 
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