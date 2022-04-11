#!/usr/bin/env python3
# pykib - A PyQt5 based kiosk browser with a minimum set of functionality
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

import subprocess
import os
import urllib.parse
import tempfile
import logging

from functools import partial

from PyQt5.QtNetwork import QAuthenticator
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt5 import QtCore, QtWebEngineWidgets, QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtCore import QSize, QUrl, Qt

class myQWebEnginePage(QWebEnginePage):
    args = 0
    dirname = 0

    # downloadProgressChange = pyqtSignal(QWidget)

    def __init__(self, argsparsed, currentdir, form, createPrivateProfile = True):
        global args
        args = argsparsed
        global dirname
        dirname = currentdir
        self.form = form


        # Profile Handling
        if (args.persistentProfilePath):
            profile = QWebEngineProfile('/', self.form.web)
            QWebEnginePage.__init__(self, profile)

            logging.info("Using persistent Profile stored in " + args.persistentProfilePath)
            self.profile().setPersistentStoragePath(args.persistentProfilePath)
            # Set Cache to Memory
            self.profile().setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
            # Do persist Cookies
            self.profile().setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)

            logging.info("Is profile in private mode:" + str(self.profile().isOffTheRecord()))

        elif(createPrivateProfile):
            # Create Empty (private) profile
            logging.info("Create new private Profile")
            profile = QtWebEngineWidgets.QWebEngineProfile(self.form.web)
            QtWebEngineWidgets.QWebEnginePage.__init__(self, profile, self.form.web)
            logging.info("Is profile in private mode:" + str(profile.isOffTheRecord()))
        else:
            logging.info("Create no new Profile")
            QtWebEngineWidgets.QWebEnginePage.__init__(self)
            profile = self.profile()
            logging.info("Is profile in private mode:" + str(profile.isOffTheRecord()))

        self.authenticationRequired.connect(self.webAuthenticationRequired)

        #Modify Profile
        #*********************************************************************

        #Connect to Download Handler
        self.profile().downloadRequested.connect(self.on_downloadRequested)

        # Enable Spell Checking
        if (args.enableSpellcheck):
            self.profile().setSpellCheckEnabled(True)
            self.profile().setSpellCheckLanguages({args.spellCheckingLanguage})

        if (args.setBrowserLanguage):
            self.profile().setHttpAcceptLanguage(args.setBrowserLanguage)

        # When Autologin is enabled, se Opera User Agent is set. This is a Workaround for Citrix Storefront Webinterfaces which will otherwise show the Client detection which fails.
        if (args.enableAutoLogon or args.setCitrixUserAgent):
            if (args.setBrowserLanguage):
                self.profile().setHttpUserAgent(
                    "Mozilla/5.0 (Windows; U; Windows NT 6.1; de) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27")
            else:
                self.profile().setHttpUserAgent(
                    "Mozilla/5.0 (Windows; U; Windows NT 6.1; " + args.setBrowserLanguage + ") AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27")

        # Modify Settings
        # *********************************************************************

        #Allow Fullscreen
        self.settings().setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)

        if (args.allowDesktopSharing):
            self.settings().setAttribute(QWebEngineSettings.ScreenCaptureEnabled, True)

        if (args.enablepdfsupport):
            self.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, 1)
            self.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessFileUrls, 1)


    def createWindow(self, _type):
        page = QWebEnginePage(self)
        if (args.enablepdfsupport):
            self.settings().setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, 1)

        page.urlChanged.connect(self.openInSameWindow)
        return page;

    @QtCore.pyqtSlot(QtCore.QUrl)
    def openInSameWindow(self, url):
        page = self.sender()
        self.form.web.load(url.toString())

        page.deleteLater()

        # Overrite the default Upload Dialog with a smaller, more limited one

    def chooseFiles(self, mode, oldFiles, acceptedMimeTypes):
        # Format acceptedMimeTypes
        mimeFiltersString = []
        nameFiltersString = []

        for x in acceptedMimeTypes:
            if ('/' in x):
                mimeFiltersString.append(x)
            else:
                nameFiltersString.append("*" + x)

        uploadDialog = QFileDialog()

        if (args.downloadPath):
            uploadDialog.setDirectory(args.downloadPath)

        print(len(mimeFiltersString));
        if (len(mimeFiltersString) != 0):
            mimeFiltersString.append("application/octet-stream");
            uploadDialog.setMimeTypeFilters(mimeFiltersString)
        else:
            nameFiltersString.append("All files (*.*)");
            uploadDialog.setNameFilters(nameFiltersString)

        uploadDialog.setFileMode(QFileDialog.ExistingFiles)
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
        #print(msg);
        #print(category);
        #print(lineNumber);
        #print(sourceID);
        # # #Ignore JS Failures
        pass

    # Certificate Error handling
    def certificateError(self, error):
        if (args.ignoreCertificates):
            print("Certificate Error")
            return True
        else:
            return False

    # Download Handle
    @QtCore.pyqtSlot(QtWebEngineWidgets.QWebEngineDownloadItem)
    def on_downloadRequested(self, download):
        downloadHandleHit = False
        old_path = download.path()
        suffix = QtCore.QFileInfo(old_path).suffix()
        # If PDF Support is enabled
        if (args.enablepdfsupport and suffix == 'pdf' and not download.url().toString().startswith(
                "blob:file://") and not download.url().toString().endswith("?downloadPdfFromPykib")):
            print("Loading PDF: " + os.path.basename(old_path))
            global dirname
            tempfolder = tempfile.gettempdir()+"/pykib/"
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

            if (download.url().toString().startswith("blob:")):
                download.setPath(tempfolder + "/" + os.path.basename(old_path).replace("////", "///"))
                download.accept()
                self.pdfFile = "file:///" + download.path()

            f = {'file': self.pdfFile}
            pdfjsargs = urllib.parse.urlencode(f)

            pdfjsurl = "file:///" + dirname.replace("\\", "/") + "/plugins/pdf.js/web/viewer.html?" + pdfjsargs.replace(
                "+", " ")

            self.loadPDFPage(pdfjsurl)
            return True

            # If Download Handle is hit
        if (args.downloadHandle):
            print("Download Handle Hit " + os.path.basename(old_path))
            for handle in args.downloadHandle:
                if (suffix == handle[0]):
                    downloadHandleHit = True
                    if os.name == 'nt':
                        filepath = os.path.expandvars(handle[2]) + "\\tmp." + suffix
                    else:
                        filepath = handle[2] + "/tmp." + suffix
                    download.setPath(filepath)
                    download.accept()
                    download.finished.connect(partial(self.runProcess, handle, filepath, download))

        if (args.download and not downloadHandleHit and download.state() == 0):
            print("File Download Request " + os.path.basename(old_path))
            # path, _ = QtWidgets.QFileDialog.getSaveFileName(self.view(), "Save File", old_path, "*."+suffix)
            path = ""
            suffix = QtCore.QFileInfo(old_path).suffix()
            downloadDialog = QFileDialog()

            if (args.alwaysOnTop or args.remoteBrowserDaemon):
                downloadDialog.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.X11BypassWindowManagerHint)

            if (args.downloadPath):
                downloadDialog.setDirectory(args.downloadPath)
                downloadDialog.selectFile(os.path.basename(old_path))
            else:
                downloadDialog.selectFile(old_path)

            downloadDialog.setFileMode(QFileDialog.AnyFile)
            downloadDialog.setAcceptMode(QFileDialog.AcceptSave)
            downloadDialog.setNameFilters(["*." + suffix])

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
        print("Executing:" + "\"" + handle[1] + "\" " + filepath);
        subprocess.Popen("\"" + handle[1] + "\" " + filepath, shell=True)

    def acceptNavigationRequest(self, url: QUrl, typ: QWebEnginePage.NavigationType, is_main_frame: bool):
        if (args.whiteList):
            if (self.checkWhitelist(url)):
                return True
            else:
                return False
        else:
            return True

    def loadPDFPage(self, pdfjsurl):
        global dirname
        #Creates a new myQWebEnginePage
        #if args.singleProcess ist set, the old "profile" will be reused and no additional private profil will be created
        # --single-process supports only one active profile on linux
        if(args.singleProcess):
            self.form.pdfpage = myQWebEnginePage(args, dirname, self.form, False)
        else:
            self.form.pdfpage = myQWebEnginePage(args, dirname, self.form, True)

        self.form.web.setPage(self.form.pdfpage)
        self.form.web.load(pdfjsurl)
        self.form.PDFnavbar.show()
        # self.form.navbar.hide()
        self.form.progress.disabled = True

    def closePDFPage(self):
        if(args.pdfreadermode):
            self.form.closeWindow()
        self.form.web.setPage(self.form.page)
        self.form.PDFnavbar.hide()
        if (args.showNavigationButtons or args.showAddressBar):
            self.form.navbar.show()
        try:
            if (self.form.pdfpage):
                self.form.pdfpage.deleteLater()
        except:
            pass
        self.form.progress.disabled = False

    def pdfDownloadAction(self):
        # Remove Extension From URL
        try:
            self.form.web.load((self.pdfFile + "?downloadPdfFromPykib").replace("\\", "/").replace("////", "///"))
            print("Downloading: " + (self.pdfFile + "?downloadPdfFromPykib").replace("\\", "/").replace("////", "///"))
        except:
            # self.form.web.load(self.pdfFile.replace("\\","/")+"?downloadPdfFromPykib")
            print("An exception while downloading a pdf occurred")

    def checkWhitelist(self, url: QUrl):
        global dirname
        currentUrl = url.toString()

        for x in args.whiteList:
            if (currentUrl.startswith(x)):
                return True;
            elif (args.enablepdfsupport):
                global dirname
                # Because of Crossplatform compatibility all the slashs and backslashes of local paths are removes
                pdfjsviewer_checkstring = ("file:///" + dirname + "/plugins/pdf.js/web/viewer.html?").replace("\\",
                                                                                                              "/").replace(
                    "/", "")
                checkurl_checkstring = currentUrl.replace("\\", "/").replace("/", "")
                if (checkurl_checkstring.startswith(pdfjsviewer_checkstring) or (
                        currentUrl.startswith("file:///") and currentUrl.endswith("?downloadPdfFromPykib"))):
                    return True
                else:
                    self.closePDFPage()

        logging.info("Site " + currentUrl + " is not whitelisted")

        #If Remote Browser is used we will show no warning an won't open the page
        if (args.remoteBrowserDaemon):
            return False;

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Warning)
        msg.setText("Site " + currentUrl + " is not white-listed")
        msg.setWindowTitle("Whitelist Error")

        backButton = QtWidgets.QPushButton("Go Back")
        backButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')));
        backButton.setIconSize(QSize(24, 24));
        backButton.setObjectName("backButton")

        msg.addButton(backButton, QtWidgets.QMessageBox.NoRole)

        homeButton = QtWidgets.QPushButton("Go Home")
        homeButton.setIcon(QIcon(os.path.join(dirname, 'icons/home.png')));
        homeButton.setIconSize(QSize(24, 24));
        homeButton.setObjectName("homeButton")

        msg.addButton(homeButton, QtWidgets.QMessageBox.NoRole)

        msg.show()
        retval = msg.exec_()

        if (retval == 0):
            self.view().stop()
        else:
            self.view().load(args.url)

        return False

    def webAuthenticationRequired(self, uri: QUrl, cred: QAuthenticator):
        print("Authentication Request from " + uri.toString())
        if(args.enableAutoLogon):
            print("Using autologin credentials")
            cred.setUser(args.autoLogonUser)
            cred.setPassword(args.autoLogonPassword)