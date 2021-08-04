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

import os

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import QSize


from pykib_base.myQWebEngineView import myQWebEngineView
from pykib_base.myQWebEnginePage import myQWebEnginePage
from pykib_base.myQProgressBar import myQProgressBar

def setupUi(form, args, dirname):        
    form.setWindowTitle(args.title)        
    form.setWindowIcon(QIcon(os.path.join(dirname, 'icons/pykib.png'))) 
    font = QFont("arial", 10)
    form.setFont(font)
    #form.setStyleSheet("background-color: rgb(77, 77, 77);")
    form.pageGridLayout = QtWidgets.QGridLayout(form)                
    form.pageGridLayout.setObjectName("pageGridLayout")
    form.pageGridLayout.setContentsMargins(0, 0, 0, 0)
       
    #Create Navbar
    form.navbar = QtWidgets.QWidget(form)
    form.navbar.setMaximumHeight(40)
    form.navbar.setObjectName("navbar")

    #Create Navbar Grid Layout
    form.navGridLayout = QtWidgets.QGridLayout(form.navbar)
    form.navGridLayout.setContentsMargins(9, 9, 9, 0)
    form.navGridLayout.setObjectName("navGridLayout")

    if(args.enablepdfsupport):
        #Create PDF Navbar
        form.PDFnavbar = QtWidgets.QWidget(form)
        form.PDFnavbar.setMaximumHeight(40)
        form.PDFnavbar.setObjectName("PDFnavbar")
        
         #Create PDF Navbar Grid Layout
        form.PDFGridLayout = QtWidgets.QGridLayout(form.PDFnavbar)
        form.PDFGridLayout.setContentsMargins(3, 0, 3, 3)
        form.PDFGridLayout.setObjectName("PDFGridLayout")      

    if(args.addMemoryCap):
        # Create memoryCapBar
        form.memoryCapBar = QtWidgets.QWidget(form)
        form.memoryCapBar.setMaximumHeight(40)
        form.memoryCapBar.setObjectName("memoryCapBar")

        form.memoryCapGridLayout = QtWidgets.QGridLayout(form.memoryCapBar)
        form.memoryCapGridLayout.setContentsMargins(0, 5, 0, 0)
        form.memoryCapGridLayout.setObjectName("memoryCapGridLayout")

    # form.web = myQWebEngineView(args, dirname)
    # form.web.setObjectName("view")
    #
    # form.page = myQWebEnginePage(args, dirname, form)
    # form.web.setPage(form.page)
    #
    # #Added progress Handling
    # form.web.loadProgress.connect(form.loadingProgressChanged)

    form.pageGridLayout.addWidget(form.web, 2, 0, 1, 0)

    navGridLayoutHorizontalPosition = 0
    if (args.showNavigationButtons):
        form.backButton = QtWidgets.QPushButton(form)
        form.backButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')))
        form.backButton.setIconSize(QSize(24, 24))
        form.backButton.setObjectName("backButton")
        form.backButton.clicked.connect(form.web.back)
        
        form.navGridLayout.addWidget(form.backButton, 0, navGridLayoutHorizontalPosition, 1, 1)
        navGridLayoutHorizontalPosition += 1
        
        form.forwardButton = QtWidgets.QPushButton(form)
        form.forwardButton.setIcon(QIcon(os.path.join(dirname, 'icons/forward.png')));
        form.forwardButton.setIconSize(QSize(24, 24));
        form.forwardButton.setObjectName("forwardButton")
        form.forwardButton.clicked.connect(form.web.forward)
        
        form.navGridLayout.addWidget(form.forwardButton, 0, navGridLayoutHorizontalPosition, 1, 1)
        navGridLayoutHorizontalPosition += 1            
 
        form.homeButton = QtWidgets.QPushButton(form)
        form.homeButton.setIcon(QIcon(os.path.join(dirname, 'icons/home.png')));
        form.homeButton.setIconSize(QSize(24, 24));
        form.homeButton.setObjectName("homeButton")
        form.homeButton.clicked.connect(form.web.load)
        
        form.navGridLayout.addWidget(form.homeButton, 0, navGridLayoutHorizontalPosition, 1, 1)
        navGridLayoutHorizontalPosition += 1
    
    if (args.showAddressBar):
        form.addressBar = QtWidgets.QLineEdit(form)
        form.addressBar.setObjectName("addressBar")
        form.web.urlChanged['QUrl'].connect(form.adjustAdressbar)
        form.navGridLayout.addWidget(form.addressBar, 0, navGridLayoutHorizontalPosition, 1, 1)
        form.addressBar.returnPressed.connect(form.pressed)

    if (args.showNavigationButtons or args.showAddressBar):
        form.pageGridLayout.addWidget(form.navbar, 0, 0, 1, 0)
    
    if(args.removeTitleBar):
            form.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    elif(args.dynamicTitle):
        form.web.titleChanged.connect(form.adjustTitle)
        form.web.iconUrlChanged.connect(form.adjustTitleIcon)

    # Closing Browser because Memory Cap Bar
    if (args.addMemoryCap):
        form.memoryCapCloseBar = myQProgressBar(form)
        form.memoryCapCloseBar.setMaximum(100)
        form.memoryCapCloseBar.setTextVisible(True)
        form.memoryCapCloseBar.setFixedHeight(40)

        form.memoryCapCloseBar.setLayoutDirection(1)
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
        form.pageGridLayout.addWidget(form.memoryCapBar, 1, 0, 1, 0)

        form.memoryCapBar.hide()

    # Download Progress Bar
    form.downloadProgress = myQProgressBar(form)
    form.downloadProgress.setMaximum(100)
    form.downloadProgress.setTextVisible(True)
    form.downloadProgress.changeStyle("download")

    form.downloadProgress.hide()
    form.pageGridLayout.addWidget(form.downloadProgress, 3, 0, 1, 0)

    # Loading Progress Bar
    form.progress = myQProgressBar(form)
    form.progress.setMaximum(100)
    form.progress.setTextVisible(False)
    form.pageGridLayout.addWidget(form.progress, 4, 0, 1, 0)

    ##Buttons for PDF Support
    if(args.enablepdfsupport):
        form.PDFbackButton = QtWidgets.QPushButton(form)
        form.PDFbackButton.setObjectName("PDFbackButton")
        if (args.pdfreadermode):
            form.PDFbackButton.setText("Close")
        else:
            form.PDFbackButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')))
            form.PDFbackButton.setIconSize(QSize(24, 24))
            form.PDFbackButton.setText("Close PDF")
        form.PDFbackButton.clicked.connect(form.page.closePDFPage)
        form.PDFGridLayout.addWidget(form.PDFbackButton, 0, 0, 1, 1)
        if(args.download):
            form.PDFDownloadButton = QtWidgets.QPushButton(form)
            form.PDFDownloadButton.setObjectName("PDFDownloadButton")
            if (args.pdfreadermode):
                form.PDFDownloadButton.setText("Save")
            else:
                form.PDFDownloadButton.setText("Download")
                form.PDFDownloadButton.setIcon(QIcon(os.path.join(dirname, 'icons/download.png')))
                form.PDFDownloadButton.setIconSize(QSize(24, 24))
            form.PDFDownloadButton.clicked.connect(form.page.pdfDownloadAction)   
            form.PDFGridLayout.addWidget(form.PDFDownloadButton, 0, 1, 1, 1) 
        form.pageGridLayout.addWidget(form.PDFnavbar, 5, 0, 1, 0)
        form.PDFnavbar.hide()

    # ###########################################################
    # Create Search Bar
    form.searchBar = QtWidgets.QWidget(form)
    form.searchBar.setMaximumHeight(40)
    form.searchBar.setObjectName("searchBar")

    #Create Search Bar Grid Layout
    form.searchBarGridLayout = QtWidgets.QGridLayout(form.searchBar)
    form.searchBarGridLayout.setContentsMargins(9, 0, 9, 9)
    form.searchBarGridLayout.setObjectName("searchBarLayout")

    #Add Search Field
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

    #Add Spacer Item
    spacerItem = QtWidgets.QSpacerItem(24, 24, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
    form.searchBarGridLayout.addItem(spacerItem, 0, 3, 1, 1)

    #Add Close Button
    form.closeSearchButton = QtWidgets.QPushButton(form)
    form.closeSearchButton.setObjectName("closeSearchButton")
    form.closeSearchButton.setIcon(QIcon(os.path.join(dirname, 'icons/close.png')))
    form.closeSearchButton.setIconSize(QSize(24, 24))
    form.closeSearchButton.clicked.connect(form.closeSearchBar)

    form.searchBarGridLayout.addWidget(form.closeSearchButton, 0, 4, 1, 1)

    # ###########################################################
    #Context Menu
    if(not args.enableContextMenu):
        form.web.setContextMenuPolicy(QtCore.Qt.NoContextMenu)

    # ###########################################################

    form.pageGridLayout.addWidget(form.searchBar, 6, 0, 1, 0)
    form.searchBar.hide()

    #Add the memory Debug bar
    if(args.memoryDebug):
        # Loading Progress Bar
        form.memoryDebug = myQProgressBar(form)
        form.memoryDebug.setMaximum(100)
        form.memoryDebug.setValue(100)
        form.memoryDebug.setTextVisible(True)
        form.pageGridLayout.addWidget(form.memoryDebug, 7, 0, 1, 0)
        form.memoryDebug.changeStyle("loading")

    retranslateUi(form)
    QtCore.QMetaObject.connectSlotsByName(form)

def retranslateUi(form):
    _translate = QtCore.QCoreApplication.translate
    #Form.setWindowTitle(_translate("Form", "Form"))