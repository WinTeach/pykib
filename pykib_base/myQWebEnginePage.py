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
import urllib.parse
import tempfile

from functools import partial
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5 import QtCore, QtWebEngineWidgets, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QWidget, QFileDialog
from PyQt5.QtCore import QSize, QUrl, QFile, QMimeType, pyqtSignal
from pykib_base.myQWebEngineView import myQWebEngineView

from pprint import pprint

class myQWebEnginePage(QWebEnginePage):
    args = 0
    dirname = 0
    #downloadProgressChange = pyqtSignal(QWidget)
    
    def __init__(self, argsparsed, currentdir, form):
        global args 
        args = argsparsed
        global dirname
        dirname = currentdir
        self.form = form
        QtWebEngineWidgets.QWebEnginePage.__init__(self)
        
        self.profile().downloadRequested.connect(self.on_downloadRequested)
        
        #Do not persist Cookies
        self.profile().setPersistentCookiesPolicy(QWebEngineProfile.NoPersistentCookies)
        
        
        if(args.enablepdfsupport):
            self.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, 1)
            self.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, 1)
        
        
        #When Autologin is enabled, se Opera User Agent is set. This is a Workaround for Citrix Storefront Webinterfaces which will otherwise show the Client detection which fails.
        if(args.enableAutoLogon):
            self.profile().setHttpUserAgent("Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27")
        
        
        #Clears the Cache on Load
        self.profile().clearHttpCache();
                
        if(args.enableSpellcheck):       
            self.profile().setSpellCheckEnabled(True)
            self.profile().setSpellCheckLanguages({args.spellCheckingLanguage})
 
    def createWindow(self, _type):
        page = QWebEnginePage(self) 
        if(args.enablepdfsupport):
            self.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, 1)
            
        page.urlChanged.connect(self.openInSameWindow)
        return page;
    
    @QtCore.pyqtSlot(QtCore.QUrl)
    def openInSameWindow(self, url):
        page = self.sender()
        self.form.web.load(url.toString())
        
        page.deleteLater()    
        
    #Overrite the default Upload Dialog with a smaller, more limited one   
    def chooseFiles(self, mode, oldFiles, acceptedMimeTypes):       
        #Format acceptedMimeTypes
        mimeFiltersString = []
        nameFiltersString = []
        
        for x in acceptedMimeTypes:
             if('/' in x):
                mimeFiltersString.append(x)
             else:
                nameFiltersString.append("*"+x)
                
        uploadDialog = QFileDialog()        
        
        
        if(args.downloadPath):
            uploadDialog.setDirectory(args.downloadPath)
        
        print(len(mimeFiltersString));
        if(len(mimeFiltersString) != 0):
            mimeFiltersString.append("application/octet-stream");        
            uploadDialog.setMimeTypeFilters(mimeFiltersString) 
        else:       
            nameFiltersString.append("All files (*.*)");
            uploadDialog.setNameFilters(nameFiltersString)
                    
        
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
        # # #Ignore JS Failures
        pass
        
    #Certificate Error handling
    def certificateError(self, error):
        if(args.ignoreCertificates):
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
        #If PDF Support is enabled        
        if(args.enablepdfsupport and suffix == 'pdf' and not download.url().toString().startswith("blob:file://") and not download.url().toString().endswith("?downloadPdfFromPykib")): 
            print("Loading PDF: "+os.path.basename(old_path))
            global dirname
            tempfolder = dirname+"/tmp"
            if os.path.exists(tempfolder):
                for the_file in os.listdir(tempfolder):
                    file_path = os.path.join(tempfolder, the_file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        print(e)
            else:
                os.makedirs(tempfolder)
            
            self.pdfFile = download.url().toString()
            
            if(download.url().toString().startswith("blob:")):
                download.setPath(tempfolder+"/"+os.path.basename(old_path).replace("////","///"))
                download.accept() 
                self.pdfFile = "file:///"+download.path()   
            
            f = { 'file' : self.pdfFile}
            pdfjsargs = urllib.parse.urlencode(f)
            
            pdfjsurl = "file:///"+dirname.replace("\\","/")+"/plugins/pdf.js/web/viewer.html?"+pdfjsargs.replace("+"," ")  
             
            self.loadPDFPage(pdfjsurl)               
            return True     
            
        
        #If Download Handle is hit
        if(args.downloadHandle):
            print("Download Handle Hit "+os.path.basename(old_path))
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
            
                
        if(args.download and not downloadHandleHit and download.state() == 0):   
            print("File Download Request "+os.path.basename(old_path))
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
        
            if downloadDialog.exec_():
                path = downloadDialog.selectedFiles()[0]                
                        
            if path:
                download.setPath(path)
                download.accept()
                download.downloadProgress.connect(self.onDownloadProgressChange)
                download.finished.connect(self.onDownloadFinished)
            else:
                download.cancel()
            return True 
            
                 
    def onDownloadProgressChange(self, bytesReceived, bytesTotal):
        self.form.downloadProgressChanged(bytesReceived, bytesTotal)
        
    def onDownloadFinished(self):
        self.form.downloadFinished()
        print("Download finished")
        
    def runProcess(self, handle, filepath, download):
        print(download.isFinished())
        print("Executing:" + "\""+handle[1] +"\" "+filepath);
        subprocess.Popen("\""+handle[1] +"\" "+filepath, shell=True)
    
    def acceptNavigationRequest(self, url: QUrl, typ: QWebEnginePage.NavigationType, is_main_frame: bool):
        if(args.whiteList):
            if(self.checkWhitelist(url)):
                return True
            else:
                return False
        else:
            return True
            
    def loadPDFPage(self, pdfjsurl):
        global dirname
        self.form.pdfpage = myQWebEnginePage(args, dirname, self.form)
        
        self.form.web.setPage(self.form.pdfpage)
        self.form.web.load(pdfjsurl)
        self.form.PDFnavbar.show()  
        #self.form.navbar.hide()  
        self.form.progress.disabled = True  
        
    def closePDFPage(self):        
        self.form.web.setPage(self.form.page)
        self.form.PDFnavbar.hide() 
        if(args.showNavigationButtons or args.showAddressBar):
            self.form.navbar.show() 
        try:
            if(self.form.pdfpage):
                self.form.pdfpage.deleteLater()
        except:
            pass
        self.form.progress.disabled = False        
            
    def pdfDownloadAction(self):       
        #Remove Extension From URL
        try:              
            self.form.web.load((self.pdfFile+"?downloadPdfFromPykib").replace("\\","/").replace("////","///"))  
            print("Downloading: "+ (self.pdfFile+"?downloadPdfFromPykib").replace("\\","/").replace("////","///"))             
        except:
            # self.form.web.load(self.pdfFile.replace("\\","/")+"?downloadPdfFromPykib") 
            print("An exception while downloading a pdf occurred")        
        
    def checkWhitelist(self, url:QUrl): 
        global dirname
        currentUrl = url.toString()      
                        
        for x in args.whiteList:            
            if(currentUrl.startswith(x)):                
                return True;
            elif(args.enablepdfsupport):  
                global dirname
                #Because of Crossplatform compatibility all the slashs and backslashes of local paths are removes           
                pdfjsviewer_checkstring = ("file:///"+dirname+"/plugins/pdf.js/web/viewer.html?").replace("\\","/").replace("/","")               
                checkurl_checkstring = currentUrl.replace("\\","/").replace("/","")
                if(checkurl_checkstring.startswith(pdfjsviewer_checkstring) or (currentUrl.startswith("file:///") and currentUrl.endswith("?downloadPdfFromPykib"))):
                    return True
                else:
                    self.closePDFPage()
                
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
