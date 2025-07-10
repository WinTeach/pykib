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
import logging
import os

from PyQt6 import QtCore, QtWidgets
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import QSize, Qt
from functools import partial
from urllib.parse import urlparse
import requests
from PyQt6.QtGui import QIcon, QPixmap
from io import BytesIO

from pykib_base.myQProgressBar import myQProgressBar


def setupUi(form, args, dirname):
    form.setWindowTitle(args.title)
    form.setWindowIcon(QIcon(os.path.join(dirname, 'icons/pykib.png')))
    font = QFont("arial", 10)
    form.setFont(font)
    # form.setStyleSheet("background-color: rgb(77, 77, 77);")
    form.pageGridLayout = QtWidgets.QGridLayout(form)
    form.pageGridLayout.setVerticalSpacing(0)
    form.pageGridLayout.setObjectName("pageGridLayout")
    form.pageGridLayout.setContentsMargins(0, 0, 0, 0)

    # Create Navbar
    form.navbar = QtWidgets.QWidget(form)
    form.navbar.setMaximumHeight(40)
    form.navbar.setObjectName("navbar")

    # Create Navbar Grid Layout
    form.navGridLayout = QtWidgets.QGridLayout(form.navbar)
    #form.navGridLayout.setContentsMargins(9, 9, 9, 0)
    form.navGridLayout.setObjectName("navGridLayout")
    form.navGridLayout.setContentsMargins(0, 0, 0, 0)

    if (args.enablepdfsupport):
        # Create PDF Navbar
        form.PDFnavbar = QtWidgets.QWidget(form)
        form.PDFnavbar.setMaximumHeight(40)
        form.PDFnavbar.setObjectName("PDFnavbar")

        # Create PDF Navbar Grid Layout
        form.PDFGridLayout = QtWidgets.QGridLayout(form.PDFnavbar)
        form.PDFGridLayout.setContentsMargins(3, 0, 3, 3)
        form.PDFGridLayout.setObjectName("PDFGridLayout")

    if (args.addMemoryCap):
        # Create memoryCapBar
        form.memoryCapBar = QtWidgets.QWidget(form)
        form.memoryCapBar.setMaximumHeight(40)
        form.memoryCapBar.setObjectName("memoryCapBar")

        form.memoryCapGridLayout = QtWidgets.QGridLayout(form.memoryCapBar)
        form.memoryCapGridLayout.setContentsMargins(0, 5, 0, 0)
        form.memoryCapGridLayout.setObjectName("memoryCapGridLayout")

    navGridLayoutHorizontalPosition = 0
    if (args.showNavigationButtons):
        form.backButton = QtWidgets.QPushButton(form)
        form.backButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')))
        form.backButton.setIconSize(QSize(24, 24))
        form.backButton.setObjectName("backButton")

        form.navGridLayout.addWidget(form.backButton, 0, navGridLayoutHorizontalPosition, 1, 1)
        navGridLayoutHorizontalPosition += 1

        form.forwardButton = QtWidgets.QPushButton(form)
        form.forwardButton.setIcon(QIcon(os.path.join(dirname, 'icons/forward.png')));
        form.forwardButton.setIconSize(QSize(24, 24));
        form.forwardButton.setObjectName("forwardButton")

        form.navGridLayout.addWidget(form.forwardButton, 0, navGridLayoutHorizontalPosition, 1, 1)
        navGridLayoutHorizontalPosition += 1

        form.homeButton = QtWidgets.QPushButton(form)
        form.homeButton.setIcon(QIcon(os.path.join(dirname, 'icons/home.png')));
        form.homeButton.setIconSize(QSize(24, 24));
        form.homeButton.setObjectName("homeButton")

        form.navGridLayout.addWidget(form.homeButton, 0, navGridLayoutHorizontalPosition, 1, 1)
        navGridLayoutHorizontalPosition += 1

        # Connect Signals
        form.backButton.clicked.connect(form.goBack)
        form.forwardButton.clicked.connect(form.goForward)
        form.homeButton.clicked.connect(form.goHome)

    if (args.showAddressBar):
        form.addressBar = QtWidgets.QLineEdit(form)
        form.addressBar.setObjectName("addressBar")
        form.addressBar.returnPressed.connect(form.pressed)

        form.addressBar.setMaximumHeight(32)
        form.navGridLayout.addWidget(form.addressBar, 0, navGridLayoutHorizontalPosition, 1, 1)

        navGridLayoutHorizontalPosition += 1

    if (args.showPrintButton):
        form.printButton = QtWidgets.QPushButton(form)
        form.printButton.setIcon(QIcon(os.path.join(dirname, 'icons/print.png')));
        form.printButton.setIconSize(QSize(24, 24));
        form.printButton.setObjectName("printButton")
        form.printButton.clicked.connect(form.printSiteRequest)

        form.navGridLayout.addWidget(form.printButton, 0, navGridLayoutHorizontalPosition, 1, 1)

    if (args.showNavigationButtons or args.showAddressBar or args.showPrintButton):
        form.pageGridLayout.addWidget(form.navbar, 1, 0, 1, 0)

    if (args.enableTabs):
        # Create Navbar
        form.tabbar = QtWidgets.QWidget(form)
        form.tabbar.setMaximumHeight(40)
        form.tabbar.setObjectName("tabbar")

        # Create Navbar Grid Layout
        form.tabGridLayout = QtWidgets.QGridLayout(form.tabbar)
        #form.tabGridLayout.setContentsMargins(9, 9, 9, 0)
        form.tabGridLayout.setObjectName("tabGridLayout")
        form.tabGridLayout.setContentsMargins(0, 0, 0, 0)

        # Add Tab Button
        if(args.allowManageTabs):
            form.addTabButton = QtWidgets.QPushButton(form)
            form.addTabButton.setFixedWidth(32)
            form.addTabButton.setIcon(QIcon(os.path.join(dirname, 'icons/plus.png')))
            form.addTabButton.setIconSize(QSize(24, 24))
            form.addTabButton.setObjectName("addTabButton")
            form.addTabButton.clicked.connect(form.addTab)

            form.tabGridLayout.addWidget(form.addTabButton, 0, 0, 1, 1)

        form.tabWidget = QtWidgets.QTabBar(form)
        form.tabWidget.setMaximumHeight(40)
        form.tabWidget.setObjectName("tabBar")
        form.tabWidget.setExpanding(False)
        form.tabWidget.setDocumentMode(True)
        form.tabWidget.setTabsClosable(False)
        form.tabWidget.currentChanged.connect(form.onTabChanged)


        # set Tab height to 40px and fixed width to 60px
        form.tabWidget.setStyleSheet("QTabBar::tab {height: 32px; min-width:200px; max-width:200px;}")

        form.tabGridLayout.addWidget(form.tabWidget, 0, 1, 1, 1)
        form.pageGridLayout.addWidget(form.tabbar, 0, 0, 1, 0)

    #Bookmarks Bar
    if args.bookmarks and len(args.bookmarks) > 0:
        # Create Navbar
        form.bookmarksBar = QtWidgets.QWidget(form)
        form.bookmarksBar.setFixedHeight(32)
        form.bookmarksBar.setObjectName("bookmarksBar")
        form.bookmarksBar.setContentsMargins(0, -10, 0, 0)

        # Create Navbar Grid Layout
        form.bookmarksGridLayout = QtWidgets.QGridLayout(form.bookmarksBar)
        form.bookmarksGridLayout.setObjectName("bookmarksGridLayout")

        for idx, bookmark in enumerate(args.bookmarks):
            bookmarkButton = QtWidgets.QPushButton(form)
            bookmarkButton.setFixedHeight(28)
            bookmarkButton.setIconSize(QSize(16, 16))
            bookmarkButton.setStyleSheet("text-align: left; padding-left: 8px; padding-right: 11px;")
            if len(bookmark) == 2:
                bookmarkButton.setText(bookmark[0])
                url = bookmark[1]
            elif len(bookmark) == 1:
                url=bookmark[0]
                bookmarkButton.setText(bookmark[0])
            else:
                break
            bookmarkButton.setToolTip(url)

            # Favicon laden und setzen
            favicon = get_favicon_from_url(url)
            if favicon:
                bookmarkButton.setIcon(favicon)

            bookmarkButton.clicked.connect(partial(form.openBookmark, url))
            form.bookmarksGridLayout.addWidget(bookmarkButton, 0, idx, 1, 1)

        # Add  SpacerItem
        form.bookmarksGridLayout.addItem(
            QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum),
            0, len(args.bookmarks), 1, 1)

        form.pageGridLayout.addWidget(form.bookmarksBar, 2, 0, 1, 0)

    if (args.removeTitleBar):
        form.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint)

    # Closing Browser because Memory Cap Bar
    if (args.addMemoryCap):
        form.memoryCapCloseBar = myQProgressBar(form)
        form.memoryCapCloseBar.setMaximum(100)
        form.memoryCapCloseBar.setTextVisible(True)
        form.memoryCapCloseBar.setFixedHeight(40)

        form.memoryCapCloseBar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        alertFont = QFont("arial", 16)
        form.memoryCapCloseBar.setFont(alertFont)
        form.memoryCapCloseBar.changeStyle("memorycap")

        #
        form.memoryCapGridLayout.addWidget(form.memoryCapCloseBar, 0, 0, 1, 1)

        form.MemoryCapCloseButton = QtWidgets.QPushButton(form)
        form.MemoryCapCloseButton.setFixedHeight(35)
        form.MemoryCapCloseButton.setObjectName("MemoryCapCloseButton")
        form.MemoryCapCloseButton.setText("Browser schließen")
        form.MemoryCapCloseButton.clicked.connect(form.closeWindow)

        form.memoryCapGridLayout.addWidget(form.MemoryCapCloseButton, 0, 1, 1, 1)
        form.pageGridLayout.addWidget(form.memoryCapBar, 3, 0, 1, 0)

        form.memoryCapBar.setVisible(False)

    # Download Progress Bar
    form.downloadProgress = myQProgressBar(form)
    form.downloadProgress.setMaximum(100)
    form.downloadProgress.setTextVisible(True)
    form.downloadProgress.changeStyle("download")

    form.downloadProgress.setVisible(False)
    form.pageGridLayout.addWidget(form.downloadProgress, 5, 0, 1, 0)

    # Loading Progress Bar
    form.progress = myQProgressBar(form)
    form.progress.setMaximum(100)
    form.progress.setTextVisible(False)
    form.pageGridLayout.addWidget(form.progress, 6, 0, 1, 0)

    ##Buttons for PDF Support
    if (args.enablepdfsupport):
        form.PDFbackButton = QtWidgets.QPushButton(form)
        form.PDFbackButton.setObjectName("PDFbackButton")
        if (args.pdfreadermode):
            form.PDFbackButton.setText("Close")
        else:
            form.PDFbackButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')))
            form.PDFbackButton.setIconSize(QSize(24, 24))
            form.PDFbackButton.setText("Close PDF")

        form.PDFGridLayout.addWidget(form.PDFbackButton, 0, 0, 1, 1)
        if (args.download):
            form.PDFDownloadButton = QtWidgets.QPushButton(form)
            form.PDFDownloadButton.setObjectName("PDFDownloadButton")
            if (args.pdfreadermode):
                form.PDFDownloadButton.setText("Save")
            else:
                form.PDFDownloadButton.setText("Download")
                form.PDFDownloadButton.setIcon(QIcon(os.path.join(dirname, 'icons/download.png')))
                form.PDFDownloadButton.setIconSize(QSize(24, 24))

            form.PDFGridLayout.addWidget(form.PDFDownloadButton, 0, 1, 1, 1)
        form.pageGridLayout.addWidget(form.PDFnavbar, 7, 0, 1, 0)
        form.PDFnavbar.setVisible(False)

    # ###########################################################
    # Create Search Bar
    form.searchBar = QtWidgets.QWidget(form)
    form.searchBar.setFixedHeight(0)
    form.searchBar.setObjectName("searchBar")

    # Create Search Bar Grid Layout
    form.searchBarGridLayout = QtWidgets.QGridLayout(form.searchBar)
    form.searchBarGridLayout.setContentsMargins(9, 0, 9, 9)
    form.searchBarGridLayout.setObjectName("searchBarLayout")

    # Add Search Field
    form.searchText = QtWidgets.QLineEdit(form)
    form.searchText.setObjectName("lineEdit")
    form.searchText.setClearButtonEnabled(1)
    form.searchText.textChanged.connect(form.searchOnPage)
    form.searchText.returnPressed.connect(form.searchOnPage)
    form.searchBarGridLayout.addWidget(form.searchText, 0, 0, 1, 1)

    # Add Search Direction Buttons
    form.searchDown = QtWidgets.QPushButton(form)
    form.searchDown.setObjectName("searchDownButton")
    form.searchDown.setIcon(QIcon(os.path.join(dirname, 'icons/down.png')))
    form.searchDown.setIconSize(QSize(24, 24))
    form.searchDown.clicked.connect(form.searchOnPage)

    form.searchBarGridLayout.addWidget(form.searchDown, 0, 2, 1, 1)

    form.searchUp = QtWidgets.QPushButton(form)
    form.searchUp.setObjectName("searchUpButton")
    form.searchUp.setIcon(QIcon(os.path.join(dirname, 'icons/up.png')))
    form.searchUp.setIconSize(QSize(24, 24))
    form.searchUp.clicked.connect(form.searchOnPage)

    form.searchBarGridLayout.addWidget(form.searchUp, 0, 1, 1, 1)

    # Add Spacer Item
    spacerItem = QtWidgets.QSpacerItem(24, 24, QtWidgets.QSizePolicy.Policy.Expanding,
                                       QtWidgets.QSizePolicy.Policy.Minimum)
    form.searchBarGridLayout.addItem(spacerItem, 0, 3, 1, 1)

    # Add Close Button
    form.closeSearchButton = QtWidgets.QPushButton(form)
    form.closeSearchButton.setObjectName("closeSearchButton")
    form.closeSearchButton.setIcon(QIcon(os.path.join(dirname, 'icons/close.png')))
    form.closeSearchButton.setIconSize(QSize(24, 24))
    form.closeSearchButton.clicked.connect(form.closeSearchBar)

    form.searchBarGridLayout.addWidget(form.closeSearchButton, 0, 4, 1, 1)

    # ###########################################################

    form.pageGridLayout.addWidget(form.searchBar, 8, 0, 1, 0)
    form.searchBar.setVisible(False)

    # Add the memory Debug bar
    if (args.memoryDebug):
        # Loading Progress Bar
        form.memoryDebug = myQProgressBar(form)
        form.memoryDebug.setMaximum(100)
        form.memoryDebug.setValue(100)
        form.memoryDebug.setTextVisible(True)
        form.pageGridLayout.addWidget(form.memoryDebug, 9, 0, 1, 0)
        form.memoryDebug.changeStyle("loading")

    retranslateUi(form)
    QtCore.QMetaObject.connectSlotsByName(form)


def retranslateUi(form):
    _translate = QtCore.QCoreApplication.translate
    # Form.setWindowTitle(_translate("Form", "Form"))


def get_favicon_from_url( url):
    try:
        # URL parsen, um die Domain zu extrahieren
        parsed_url = urlparse(url)
        logging.debug(parsed_url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Standard-Favicon-Pfad probieren
        favicon_url = f"{domain}/favicon.ico"
        response = requests.get(favicon_url, timeout=2)

        # Wenn erfolgreich, Favicon als QIcon zurückgeben
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            pixmap = QPixmap()
            if pixmap.loadFromData(response.content):
                return QIcon(pixmap)
    except Exception as e:
        print(f"Fehler beim Laden des Favicons: {e}")

    # Standardicon zurückgeben, wenn kein Favicon geladen werden konnte
    return None
