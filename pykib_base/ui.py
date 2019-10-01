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
    
    form.web = myQWebEngineView(args)
    form.web.setObjectName("view")
    
    form.page = myQWebEnginePage(args, dirname, form)    
    form.web.setPage(form.page)
    
    #Added progress Handling   
    form.web.loadProgress.connect(form.loadingProgressChanged)
    
          
    navGridLayoutHorizontalPosition = 0;
    if (args.showNavigationButtons):
        form.backButton = QtWidgets.QPushButton(form)
        form.backButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')));
        form.backButton.setIconSize(QSize(24, 24));
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
            
    ##Buttons for PDF Support
    if(args.enablepdfsupport):
        form.PDFbackButton = QtWidgets.QPushButton(form)
        form.PDFbackButton.setIcon(QIcon(os.path.join(dirname, 'icons/back.png')));
        form.PDFbackButton.setIconSize(QSize(24, 24));
        form.PDFbackButton.setObjectName("PDFbackButton")
        form.PDFbackButton.setText("Close PDF")
        form.PDFbackButton.clicked.connect(form.page.closePDFPage)
        form.PDFGridLayout.addWidget(form.PDFbackButton, 0, 0, 1, 1)        
        if(args.download):
            form.PDFDownloadButton = QtWidgets.QPushButton(form)
            form.PDFDownloadButton.setIcon(QIcon(os.path.join(dirname, 'icons/download.png')));
            form.PDFDownloadButton.setIconSize(QSize(24, 24));
            form.PDFDownloadButton.setObjectName("PDFDownloadButton")
            form.PDFDownloadButton.setText("Download")
            form.PDFDownloadButton.clicked.connect(form.page.pdfDownloadAction)   
            form.PDFGridLayout.addWidget(form.PDFDownloadButton, 0, 1, 1, 1) 
        form.pageGridLayout.addWidget(form.PDFnavbar, 4, 0, 1, 0)
        form.PDFnavbar.hide()
            
    
    form.progress = myQProgressBar(form)    
    form.progress.setMaximum(100)
    form.progress.setTextVisible(False)
    
    #Download Progress Bar
    form.downloadProgress = myQProgressBar(form)    
    form.downloadProgress.setMaximum(100)
    form.downloadProgress.setTextVisible(True)    
    form.downloadProgress.changeStyle("download")
    
    # form.downloadProgress.setValue(75)    
    # form.downloadProgress.setFormat("Download finished....")
    
    form.downloadProgress.hide()
    
    form.pageGridLayout.addWidget(form.web, 1, 0, 1, 0)    
    
    form.pageGridLayout.addWidget(form.downloadProgress, 2, 0, 1, 0)
    form.pageGridLayout.addWidget(form.progress, 3, 0, 1, 0)
    
    retranslateUi(form)
    QtCore.QMetaObject.connectSlotsByName(form)

def retranslateUi(form):
    _translate = QtCore.QCoreApplication.translate
    #Form.setWindowTitle(_translate("Form", "Form"))