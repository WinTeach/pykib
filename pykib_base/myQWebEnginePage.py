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

import subprocess
import os
import urllib.parse
import tempfile
import logging
import time

from functools import partial

from PyQt6.QtNetwork import QAuthenticator, QNetworkCookie
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings
from PyQt6 import QtCore, QtWebEngineWidgets, QtWidgets, QtWebEngineCore
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QSize, QUrl, Qt

from pykib_base.myUrlSchemeHandler import myUrlSchemeHandler
from pykib_base.notificationPopup import NotificationPopup

class myQWebEnginePage(QWebEnginePage):
    args = 0
    dirname = 0

    def __init__(self, argsparsed, currentdir, form, createPrivateProfile = True):
        global args
        args = argsparsed
        global dirname
        dirname = currentdir

        self.currentSiteCookies = []

        self.form = form

        self.initBrowserProfile(createPrivateProfile)


        # Modify Settings
        # *********************************************************************
        #Allow Fullscreen
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        if (args.allowDesktopSharing):
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)

        if (args.enablepdfsupport):
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, 1)
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, 1)

    def initBrowserProfile(self, createPrivateProfile):
        # Create Empty (private) profile
        if (args.persistentProfilePath):
            profile = QtWebEngineCore.QWebEngineProfile('/', self.form.web)
            QtWebEngineCore.QWebEnginePage.__init__(self, profile, self.form.web)

            logging.info("Using persistent Profile stored in " + args.persistentProfilePath)
            self.profile().setPersistentStoragePath(args.persistentProfilePath)
            # Set Cache to Memory
            self.profile().setHttpCacheType(QWebEngineProfile.HttpCacheType.MemoryHttpCache)
            # Do persist Cookies
            self.profile().setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

            logging.info("Is profile in private mode:" + str(profile.isOffTheRecord()))

        elif (createPrivateProfile):
            logging.info("Create new private Profile")
            profile = QtWebEngineCore.QWebEngineProfile(self.form.web)
            QtWebEngineCore.QWebEnginePage.__init__(self, profile, self.form.web)
            logging.info("Is profile in private mode:" + str(profile.isOffTheRecord()))
        else:
            logging.info("Create no new Profile")
            QtWebEngineCore.QWebEnginePage.__init__(self)
            logging.info("Is profile in private mode:" + str(self.profile().isOffTheRecord()))

        self.authenticationRequired.connect(self.webAuthenticationRequired)

        self.newWindowRequested.connect(self.openInSameWindow)
        self.certificateError.connect(self.validateCertificateError)

        # Modify Profile
        # *********************************************************************

        # Connect to Download Handler
        self.profile().downloadRequested.connect(self.on_downloadRequested)

        # Register Teams URL Handler
        self.profile().installUrlSchemeHandler(b'msteams', myUrlSchemeHandler(self))

        # Browser Notification Popup Handler
        if args.allowBrowserNotifications:
            popup = NotificationPopup(self.form)

            def presentNotification(notification):
                popup.present(notification)

            self.profile().setNotificationPresenter(presentNotification)

        # Enable Spell Checking
        if (args.enableSpellcheck):
            # Seems not to work with current Version - Further investigation neccessary
            logging.info("Enable spell checking language: " + args.spellCheckingLanguage)
            self.profile().setSpellCheckEnabled(True)

        if (args.setBrowserLanguage):
            self.profile().setHttpAcceptLanguage(args.setBrowserLanguage)

        # When setCitrixUserAgent is enabled, the Opera User Agent is set. This is a Workaround for Citrix Storefront Webinterfaces to skip Client detection.
        if (args.setCitrixUserAgent):
            if (args.setBrowserLanguage):
                self.profile().setHttpUserAgent(
                    "Mozilla/5.0 (Windows; U; Windows NT 6.1; de) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27")
            else:
                self.profile().setHttpUserAgent(
                    "Mozilla/5.0 (Windows; U; Windows NT 6.1; " + args.setBrowserLanguage + ") AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27")

    def openInSameWindow(self, newWindowsRequest):
        self.form.web.load(newWindowsRequest.requestedUrl().toString())

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

        uploadDialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        uploadDialog.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)

        options = QFileDialog.Option.ReadOnly
        options |= QFileDialog.Option.DontUseNativeDialog

        uploadDialog.setOptions(options)

        if uploadDialog.exec():
            fileName = uploadDialog.selectedFiles()
            return fileName

        return [""]

    def javaScriptConsoleMessage(self, msg, lineNumber, sourceID, category):
        if(args.showJsConsole):
            logging.debug(msg)
            logging.debug(category)
            logging.debug(lineNumber)
            logging.debug(sourceID)
        # # #Ignore JS Failures
        pass

    # Certificate Error handling
    def validateCertificateError(self, error):
        if (args.ignoreCertificates):
            print("Certificate Error")
            error.acceptCertificate()
            return True
        else:
            return False

    # Download Handle
    @QtCore.pyqtSlot(QtWebEngineCore.QWebEngineDownloadRequest)
    def on_downloadRequested(self, download):
        logging.info(download.mimeType())
        logging.info(download.suggestedFileName())
        downloadHandleHit = False

        suffix = QtCore.QFileInfo(download.suggestedFileName()).suffix()
        logging.info(suffix)
        # If PDF Support is enabled
        if (args.enablepdfsupport and suffix.lower() == 'pdf' and not download.url().toString().startswith(
                "blob:file://") and not download.url().toString().endswith("?downloadPdfFromPykib")):
            print("Loading PDF: " + os.path.basename(download.suggestedFileName()))
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

            self.pdfFile = tempfolder + "/" + os.path.basename(download.suggestedFileName()).replace("////", "///")

            #if (download.url().toString().startswith("blob:")):
            download.setDownloadFileName(self.pdfFile)
            download.accept()
            download.isFinishedChanged.connect(partial(self.openPdf, download.url().toString()))
            return True

            # If Download Handle is hit
        if (args.downloadHandle):
            print("Download Handle Hit " + os.path.basename(download.suggestedFileName()))
            for handle in args.downloadHandle:
                if (suffix == handle[0]):
                    downloadHandleHit = True
                    if os.name == 'nt':
                        filepath = os.path.expandvars(handle[2]) + "\\tmp." + suffix
                    else:
                        filepath = handle[2] + "/tmp." + suffix
                    download.setDownloadFileName(filepath)
                    download.accept()
                    download.isFinishedChanged.connect(partial(self.runProcess, handle, filepath, download))

        if (args.download and not downloadHandleHit and download.state() == QtWebEngineCore.QWebEngineDownloadRequest.DownloadState.DownloadRequested):
            print("File Download Request " + os.path.basename(download.suggestedFileName()))
            # path, _ = QtWidgets.QFileDialog.getSaveFileName(self.view(), "Save File", old_path, "*."+suffix)
            path = ""
            suffix = QtCore.QFileInfo(download.suggestedFileName()).suffix()
            downloadDialog = QFileDialog()

            if (args.alwaysOnTop or args.remoteBrowserDaemon):
                downloadDialog.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.X11BypassWindowManagerHint)

            if (args.downloadPath):
                downloadDialog.setDirectory(args.downloadPath)
                downloadDialog.selectFile(os.path.basename(download.suggestedFileName()))
            else:
                downloadDialog.selectFile(os.path.basename(download.suggestedFileName()))

            downloadDialog.setFileMode(QFileDialog.FileMode.AnyFile)
            downloadDialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            downloadDialog.setNameFilters(["*." + suffix])

            downloadDialog.setOption(QFileDialog.Option.DontUseNativeDialog)
            if downloadDialog.exec():
                path = downloadDialog.selectedFiles()[0]

            if path:
                download.setDownloadFileName(path)
                download.accept()
                download.receivedBytesChanged.connect(partial(self.onDownloadReceivedBytesChanged, download))
                download.isFinishedChanged.connect(self.onDownloadIsFinished)
            else:
                download.cancel()
            return True

    def onDownloadReceivedBytesChanged(self, downloadRequest):
        self.form.downloadProgressChanged(downloadRequest.receivedBytes(), downloadRequest.totalBytes())

    def onDownloadIsFinished(self):
        self.form.downloadFinished()
        print("Download finished")

    def runProcess(self, handle, filepath, download):
        print(download.isFinished())
        print("Executing:" + "\"" + handle[1] + "\" " + filepath + " " + str(os.getpid()));
        subprocess.Popen("\"" + handle[1] + "\" " + filepath + " " + str(os.getpid()), shell=True)

    def openPdf(self, origUrl):
        self.pdfFile = "file:///" + self.pdfFile
        f = {'file': self.pdfFile}
        pdfjsargs = urllib.parse.urlencode(f)

        pdfjsurl = "file:///" + dirname.replace("\\", "/") + "/plugins/pdf.js/web/viewer.html?" + pdfjsargs.replace(
            "+", " ")

        self.loadPDFPage(pdfjsurl, origUrl)


    def acceptNavigationRequest(self, url: QUrl, typ: QWebEnginePage.NavigationType, is_main_frame: bool):
        if (args.whiteList):
            logging.info("Whitlist Check in Main Frame: " + str(is_main_frame))
            if(args.whiteListMainFrameOnly):
                if(is_main_frame and self.checkWhitelist(url, is_main_frame)):
                    return True
                elif(not is_main_frame):
                    return True
                else:
                    return False
            elif (self.checkWhitelist(url, is_main_frame)):
                return True
            else:
                return False
        else:
            return True

    def loadPDFPage(self, pdfjsurl, origUrl):
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

        if args.showAddressBar:
            self.form.addressBar.setText(origUrl)

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

        #CleanUp Tempoary PDFs
        try:
            tempfolder = os.listdir(tempfile.gettempdir() + "/pykib/")
            for item in tempfolder:
                if item.lower().endswith(".pdf"):
                    os.remove(os.path.join(tempfile.gettempdir() + "/pykib/", item))
        except:
            logging.info("An exception while cleanup PDF TMP Folder")
    def pdfDownloadAction(self):
        # Remove Extension From URL
        try:
            self.form.web.load((self.pdfFile + "?downloadPdfFromPykib").replace("\\", "/").replace("////", "///"))
            print("Downloading: " + (self.pdfFile + "?downloadPdfFromPykib").replace("\\", "/").replace("////", "///"))
        except:
            # self.form.web.load(self.pdfFile.replace("\\","/")+"?downloadPdfFromPykib")
            print("An exception while downloading a pdf occurred")

    def checkWhitelist(self, url: QUrl, is_main_frame: bool):
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
        if (args.remoteBrowserDaemon or not is_main_frame):
            return False;

        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Icon.Warning)
        msg.setText("Site " + currentUrl + " is not white-listed")
        msg.setWindowTitle("Whitelist Error")

        backButton = QtWidgets.QPushButton("Go Back")
        backButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')));
        backButton.setIconSize(QSize(24, 24));
        backButton.setObjectName("backButton")

        msg.addButton(backButton, QtWidgets.QMessageBox.ButtonRole.NoRole)

        homeButton = QtWidgets.QPushButton("Go Home")
        homeButton.setIcon(QIcon(os.path.join(dirname, 'icons/home.png')));
        homeButton.setIconSize(QSize(24, 24));
        homeButton.setObjectName("homeButton")

        msg.addButton(homeButton, QtWidgets.QMessageBox.ButtonRole.NoRole)

        msg.show()
        retval = msg.exec()

        if (retval == 0):
            self.form.web.stop()
        else:
            self.form.web.load(args.url)

        return False

    def webAuthenticationRequired(self, uri: QUrl, cred: QAuthenticator):
        print("Authentication Request from " + uri.toString())
        if(args.enableAutoLogon):
            print("Using autologin credentials")
            cred.setUser(args.autoLogonUser)
            cred.setPassword(args.autoLogonPassword)

    def enableCleanupBrowserProfileOption(self):
        self.profile().clearAllVisitedLinks()
        self.profile().cookieStore().deleteAllCookies()
        self.profile().cookieStore().deleteSessionCookies()
        self.runJavaScript("localStorage.clear();")
        self.runJavaScript("sessionStorage.clear();")
        self.runJavaScript("location.reload();")
        logging.info("Cleanup Browser Profile")

