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
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

from pykib_base.myQWebEngineView import myQWebEngineView
from pykib_base.myQWebEnginePage import myQWebEnginePage

def setupUi(form, args, dirname):        
    form.setWindowTitle(args.title)        
    form.setWindowIcon(QIcon(os.path.join(dirname, 'icons/pykib.png')))  
    
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
    
    form.web = myQWebEngineView(args)
    form.web.setObjectName("view")
    
    form.page = myQWebEnginePage(args, dirname)
    
    form.web.setPage(form.page)
    #form.page.setView(form.web)
    
          
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
            
    form.pageGridLayout.addWidget(form.web, 1, 0, 1, 0)
    
    retranslateUi(form)
    QtCore.QMetaObject.connectSlotsByName(form)

def retranslateUi(form):
    _translate = QtCore.QCoreApplication.translate
    #Form.setWindowTitle(_translate("Form", "Form"))