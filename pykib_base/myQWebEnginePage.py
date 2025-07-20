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

import subprocess
import os
import urllib.parse
import tempfile
import logging
from functools import partial

from PyQt6.QtNetwork import QAuthenticator
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineProfile, QWebEngineSettings, QWebEngineDesktopMediaRequest
from PyQt6 import QtCore, QtWidgets, QtWebEngineCore
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtWidgets import QFileDialog
from PyQt6.QtCore import QSize, QUrl, Qt

from pykib_base.myUrlSchemeHandler import myUrlSchemeHandler
from pykib_base.notificationPopup import NotificationPopup

class myQWebEnginePage(QWebEnginePage):
    args = 0
    dirname = 0

    def __init__(self, argsparsed, currentdir, form, createPrivateProfile = True, browserProfile = None):
        global args
        args = argsparsed
        global dirname
        dirname = currentdir

        self.currentSiteCookies = []

        self.form = form

        self.initBrowserProfile(createPrivateProfile, browserProfile)

        # Modify Settings
        # *********************************************************************
        #Allow Fullscreen
        self.settings().setAttribute(QWebEngineSettings.WebAttribute.FullScreenSupportEnabled, True)
        if (args.allowDesktopSharing):
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.ScreenCaptureEnabled, True)
            self.desktopMediaRequested.connect(self.onDesktopMediaRequest)

        if (args.enablepdfsupport):
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, 1)
            self.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, 1)

    def initBrowserProfile(self, createPrivateProfile, browserProfile = None):
        # Create Empty (private) profile
        if args.persistentProfilePath or browserProfile:
            try:
                if browserProfile:
                    self.browserProfile = browserProfile
                else:
                    self.browserProfile = QtWebEngineCore.QWebEngineProfile('/')
                QtWebEngineCore.QWebEnginePage.__init__(self, self.browserProfile)
            except Exception as e:
                logging.info("Reuse of Profile failed: " + str(e))
                self.browserProfile = QtWebEngineCore.QWebEngineProfile('/')
                QtWebEngineCore.QWebEnginePage.__init__(self, self.browserProfile)

            #logging.info("Using persistent Profile stored in " + args.persistentProfilePath)
            self.profile().setPersistentStoragePath(args.persistentProfilePath)
            # Set Cache to Memory
            self.profile().setHttpCacheType(QWebEngineProfile.HttpCacheType.DiskHttpCache)
            # Do persist Cookies
            self.profile().setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.AllowPersistentCookies)

            logging.info("Is profile in private mode:" + str(self.browserProfile.isOffTheRecord()))
        elif (createPrivateProfile):
            logging.info("Create new private Profile")
            self.browserProfile = QtWebEngineCore.QWebEngineProfile()
            QtWebEngineCore.QWebEnginePage.__init__(self, self.browserProfile)
            logging.info("Is profile in private mode:" + str(self.browserProfile.isOffTheRecord()))
        else:
            logging.info("Create no new Profile")
            QtWebEngineCore.QWebEnginePage.__init__(self)
            logging.info("Is profile in private mode:" + str(self.profile().isOffTheRecord()))

        self.authenticationRequired.connect(self.webAuthenticationRequired)


        self.newWindowRequested.connect(self.windowRequested)
        self.certificateError.connect(self.validateCertificateError)

        # Modify Profile
        # *********************************************************************

        # Connect to Download Handler
        self.profile().downloadRequested.connect(self.on_downloadRequested)

        # Register workspaces URL Handler
        #self.profile().installUrlSchemeHandler(b'workspaces', myUrlSchemeHandler(self))

        #Register all URL Handlers given by parameters
        if (args.addUrlSchemeHandler):
            for handler in args.addUrlSchemeHandler:
                logging.info("Registering URL Scheme Handler: " + handler)
                self.profile().installUrlSchemeHandler(handler.encode('utf-8'), myUrlSchemeHandler(self))

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
            # Setze Sprache
            logging.info(args.setBrowserLanguage)
            self.profile().setHttpAcceptLanguage(args.setBrowserLanguage)

        # When setCitrixUserAgent is enabled, the Opera User Agent is set. This is a Workaround for Citrix Storefront Webinterfaces to skip Client detection.
        if (args.setCitrixUserAgent):
            if (args.setBrowserLanguage):
                self.profile().setHttpUserAgent(
                    "Mozilla/5.0 (Windows; U; Windows NT 6.1; de) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27")
            else:
                self.profile().setHttpUserAgent(
                    "Mozilla/5.0 (Windows; U; Windows NT 6.1; " + args.setBrowserLanguage + ") AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27")

    def windowRequested(self, newWindowsRequest):
        if(args.allowManageTabs):
            # If Tabs are enabled, we will open the new window in a new tab
            logging.info("New Window Request: " + newWindowsRequest.requestedUrl().toString())
            self.form.addTab(newWindowsRequest.requestedUrl().toString())
        else:
            self.form.tabs[self.form.currentTabIndex]['web'].load(newWindowsRequest.requestedUrl().toString())

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
            logging.info(msg)
            logging.info(category)
            logging.info(lineNumber)
            logging.info(sourceID)
        # # #Ignore JS Failures
        pass

    # Certificate Error handling
    def validateCertificateError(self, error):
        if (args.ignoreCertificates):
            logging.info("Certificate Error ignored: " + error.description())
            error.acceptCertificate()
            return True
        elif not args.remoteBrowserDaemon:
            if not error.isMainFrame():
                logging.info("Certificate Error outside of Main Frame: " + error.url().toString())
                return False
            else:
                logging.info("Certificate Error in Main Frame: " + error.url().toString())
                # Ask user whether to accept the certificate
                details = f"Error: {error.description()}\nURL: {error.url().toString()}"
                try:
                    certificateChain = error.certificateChain()
                    certinfo = ""
                    for idx, cert in enumerate(certificateChain):
                        cert_details = f"Certificate {idx + 1}:\n"
                        cert_details += f"  Issuer: {cert.issuerDisplayName()}\n"
                        cert_details += f"  Subject: {cert.subjectDisplayName()}\n"
                        cert_details += f"  Valid from: {cert.effectiveDate().toString()}\n"
                        cert_details += f"  Valid until: {cert.expiryDate().toString()}\n"
                        certinfo += cert_details + "\n"

                    details += "\n\nCertificate chain:\n" + certinfo

                except Exception as e:
                    logging.error("Error getting additional information: " + str(e))
                    pass


                dialog = QtWidgets.QDialog()
                dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
                dialog.setModal(True)

                dialog.setWindowTitle("Certificate Error")

                try:
                    favicon = self.form.windowIcon()
                    if not favicon.isNull():
                        dialog.setWindowIcon(favicon)
                    else:
                        dialog.setWindowIcon(QIcon(os.path.join(dirname, 'icons/pykib.png')))
                except Exception as e:
                    logging.error("Error setting window icon: " + str(e))
                    pass
                layout = QtWidgets.QVBoxLayout(dialog)
                icon_label = QtWidgets.QLabel()
                icon_label.setPixmap(dialog.windowIcon().pixmap(64, 64))
                icon_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                layout.addWidget(icon_label)
                title_label = QtWidgets.QLabel("Certificate error: Do you want to proceed anyway?")
                title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
                title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                layout.addWidget(title_label)
                details_label = QtWidgets.QLabel(details)
                details_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                #details_label.setStyleSheet("font-size: 16px;")
                details_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                layout.addWidget(details_label)
                button_layout = QtWidgets.QHBoxLayout()
                acceptButton = QtWidgets.QPushButton("Proceed anyway")
                rejectButton = QtWidgets.QPushButton("Cancel")
                acceptButton.setMinimumSize(180, 50)
                rejectButton.setMinimumSize(180, 50)
                acceptButton.setStyleSheet("font-size: 18px; background: #4caf50; color: white;")
                rejectButton.setStyleSheet("font-size: 18px; background: #c00; color: white;")
                button_layout.addWidget(acceptButton)
                button_layout.addWidget(rejectButton)
                layout.addLayout(button_layout)
                result = {'accepted': False}
                def accept():
                    result['accepted'] = True
                    dialog.accept()
                def reject():
                    result['accepted'] = False
                    dialog.reject()
                acceptButton.clicked.connect(accept)
                rejectButton.clicked.connect(reject)
                dialog.setModal(True)
                dialog.exec()
                if result['accepted']:
                    error.acceptCertificate()
                    return True
                else:
                    error.rejectCertificate()
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

            if ((args.alwaysOnTop or args.remoteBrowserDaemon) and args.remoteBrowserIgnoreX11):
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

    def onDesktopMediaRequest(self, request: QWebEngineDesktopMediaRequest):
        # Check if desktop sharing is allowed, otherwise cancel the request
        if not args.allowDesktopSharing:
            request.cancel()
            return

        # Get models for available screens and application windows
        screens_model = request.screensModel()
        windows_model = request.windowsModel()
        # If neither screens nor windows are available, cancel the request
        if (not screens_model or screens_model.rowCount() == 0) and (
                not windows_model or windows_model.rowCount() == 0):
            request.cancel()
            return

        # Create the selection dialog
        dialog = QtWidgets.QDialog()
        # Set the window icon (fallback to default if not available)
        try:
            dialog.setWindowIcon(self.form.windowIcon())
        except Exception as e:
            logging.error("Error setting window icon: " + str(e))
            dialog.setWindowIcon(QIcon(os.path.join(dirname, 'icons/pykib.png')))

        dialog.setWindowTitle("Share screen or application")
        layout = QtWidgets.QVBoxLayout(dialog)
        label = QtWidgets.QLabel("Please select a screen or application:")
        layout.addWidget(label)

        # Create tab widget for screens and applications
        tab_widget = QtWidgets.QTabWidget()
        # --- Screens Tab ---
        screen_tab = QtWidgets.QWidget()
        screen_layout = QtWidgets.QVBoxLayout(screen_tab)
        screen_list = QtWidgets.QListView()
        screen_list.setModel(screens_model)
        screen_layout.addWidget(screen_list)
        # Preview label for screen screenshot
        screen_preview = QtWidgets.QLabel()
        screen_preview.setFixedSize(320, 180)
        screen_layout.addWidget(screen_preview)
        tab_widget.addTab(screen_tab, "Screens")

        # Prepare screenshots for all available screens
        screen_pixmaps = []
        for screen in QGuiApplication.screens():
            pixmap = screen.grabWindow(0)
            screen_pixmaps.append(pixmap)

        # Update the preview when a screen is selected
        def updateScreenPreview(index):
            if index.isValid():
                screen_idx = index.row()
                if 0 <= screen_idx < len(screen_pixmaps):
                    screen_preview.setPixmap(screen_pixmaps[screen_idx].scaled(
                        screen_preview.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))
                else:
                    screen_preview.clear()
            else:
                screen_preview.clear()

        screen_list.selectionModel().currentChanged.connect(updateScreenPreview)

        # --- Applications Tab ---
        window_tab = QtWidgets.QWidget()
        window_layout = QtWidgets.QVBoxLayout(window_tab)
        window_list = QtWidgets.QListView()
        window_list.setModel(windows_model)
        window_layout.addWidget(window_list)
        tab_widget.addTab(window_tab, "Applications")

        layout.addWidget(tab_widget)

        # Dialog buttons (OK/Cancel)
        button_box = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok | QtWidgets.QDialogButtonBox.StandardButton.Cancel)
        layout.addWidget(button_box)

        # Handle OK/Cancel actions
        def accept():
            current_tab = tab_widget.currentIndex()
            if current_tab == 0:
                index = screen_list.currentIndex()
                if index.isValid():
                    request.selectScreen(index)
                    dialog.accept()
                    return
            elif current_tab == 1:
                index = window_list.currentIndex()
                if index.isValid():
                    request.selectWindow(index)
                    dialog.accept()
                    return
            # Show warning if nothing is selected
            QtWidgets.QMessageBox.warning(dialog, "No selection", "Please select a screen or application.")

        def reject():
            request.cancel()
            dialog.reject()

        button_box.accepted.connect(accept)
        button_box.rejected.connect(reject)

        # Show the dialog and handle cancellation
        if not dialog.exec():
            request.cancel()

    def runProcess(self, handle, filepath, download):
        print(download.isFinished())
        print("Executing:" + "\"" + handle[1] + "\" " + filepath);
        subprocess.Popen("\"" + handle[1] + "\" " + filepath, shell=True)

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

        self.form.tabs[self.form.currentTabIndex]['web'].setPage(self.form.pdfpage)
        self.form.tabs[self.form.currentTabIndex]['web'].load(pdfjsurl)
        self.form.PDFnavbar.setVisible(True)
        # self.form.navbar.hide()
        self.form.progressModal.disabled = True

        if args.showAddressBar:
            self.form.addressBar.setText(origUrl)

    def closePDFPage(self):
        if(args.pdfreadermode):
            self.form.closeWindow()
        self.form.tabs[self.form.currentTabIndex]['web'].setPage(self.form.tabs[self.form.currentTabIndex]['page'])
        self.form.PDFnavbar.hide()
        if (args.showNavigationButtons or args.showAddressBar):
            self.form.navbar.show()
        try:
            if (self.form.pdfpage):
                self.form.pdfpage.deleteLater()
        except:
            pass
        self.form.progressModal.disabled = False

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
            self.form.tabs[self.form.currentTabIndex]['web'].load((self.pdfFile + "?downloadPdfFromPykib").replace("\\", "/").replace("////", "///"))
            print("Downloading: " + (self.pdfFile + "?downloadPdfFromPykib").replace("\\", "/").replace("////", "///"))
        except:
            # self.form.tabs[self.form.currentTabIndex]['web'].load(self.pdfFile.replace("\\","/")+"?downloadPdfFromPykib")
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
            self.form.tabs[self.form.currentTabIndex]['web'].stop()
        else:
            self.form.tabs[self.form.currentTabIndex]['web'].load(args.url[0])

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

