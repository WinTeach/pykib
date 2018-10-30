# pykib - A PyQt5 based kiosk browser with a minimum set of functionality
# Copyright (C) 2018 Tobias Wintrich
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

import sys
import subprocess
import os
import textwrap
from functools import partial
from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets
from PyQt5.QtCore import QSize, QUrl
from PyQt5.QtGui import QIcon, QKeyEvent
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineProfile
from PyQt5.QtWidgets import QApplication, QWidget 
from argparse import ArgumentParser, RawDescriptionHelpFormatter

__version_info__ = ('beta', '0.9')
__version__ = '-'.join(__version_info__)

class MainWindow(QWidget):
    def __init__(self, parent=None): 
        super(MainWindow, self).__init__(parent)
        
        self.setupUi(self)
        self.web.setGeometry(0,0,400,500)
        self.setWindowTitle(args.title)
        #self.setWindowIcon(QIcon("icons/home.png"))  
        
        if(args.removeTitleBar):
            self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        elif(args.dynamicTitle):
            self.web.titleChanged.connect(self.adjustTitle)
          
        self.web.load(args.url)         
      
    def setupUi(self, Form):        
        self.pageGridLayout = QtWidgets.QGridLayout(Form)                
        self.pageGridLayout.setObjectName("pageGridLayout")
        
        self.pageGridLayout.setContentsMargins(0, 0, 0, 0)
        
        #Create Navbar
        self.navbar = QtWidgets.QWidget(Form)
        self.navbar.setMaximumHeight(40)
        self.navbar.setObjectName("navbar")
        
        #Create Navbar Grid Layout
        self.navGridLayout = QtWidgets.QGridLayout(self.navbar)
        self.navGridLayout.setContentsMargins(9, 9, 9, 0)
        self.navGridLayout.setObjectName("navGridLayout")        
        
        self.web = WebView()
        self.web.setObjectName("view")
        
        self.page = WebViewPage(self.web)
        
        self.web.setPage(self.page)
        #self.page.setView(self.web)
        
              
        navGridLayoutHorizontalPosition = 0;
        if (args.showNavigationButtons):
            self.backButton = QtWidgets.QPushButton(Form)
            self.backButton.setIcon(QIcon("icons/back.png"));
            self.backButton.setIconSize(QSize(24, 24));
            self.backButton.setObjectName("backButton")
            self.backButton.clicked.connect(self.web.back)
            
            self.navGridLayout.addWidget(self.backButton, 0, navGridLayoutHorizontalPosition, 1, 1)
            navGridLayoutHorizontalPosition += 1
            
            self.forwardButton = QtWidgets.QPushButton(Form)
            self.forwardButton.setIcon(QIcon("icons/forward.png"));
            self.forwardButton.setIconSize(QSize(24, 24));
            self.forwardButton.setObjectName("forwardButton")
            self.forwardButton.clicked.connect(self.web.forward)
            
            self.navGridLayout.addWidget(self.forwardButton, 0, navGridLayoutHorizontalPosition, 1, 1)
            navGridLayoutHorizontalPosition += 1            
     
            self.homeButton = QtWidgets.QPushButton(Form)
            self.homeButton.setIcon(QIcon("icons/home.png"));
            self.homeButton.setIconSize(QSize(24, 24));
            self.homeButton.setObjectName("homeButton")
            self.homeButton.clicked.connect(self.web.load)
            
            self.navGridLayout.addWidget(self.homeButton, 0, navGridLayoutHorizontalPosition, 1, 1)
            navGridLayoutHorizontalPosition += 1
        
        if (args.showAddressBar):
            self.addressBar = QtWidgets.QLineEdit(Form)
            self.addressBar.setObjectName("addressBar")
            self.web.urlChanged['QUrl'].connect(self.adjustAdressbar)
            self.navGridLayout.addWidget(self.addressBar, 0, navGridLayoutHorizontalPosition, 1, 1)
            self.addressBar.returnPressed.connect(self.pressed)

        if (args.showNavigationButtons or args.showAddressBar):
            self.pageGridLayout.addWidget(self.navbar, 0, 0, 1, 0)
        
        self.pageGridLayout.addWidget(self.web, 1, 0, 1, 0)
        
        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        #Form.setWindowTitle(_translate("Form", "Form"))

    
    def pressed(self):
        self.web.load(self.addressBar.displayText())
        
    #ctach defined Shortcuts
    def keyPressEvent(self, event):
        keyEvent = QKeyEvent(event)
        shift = event.modifiers() & QtCore.Qt.ShiftModifier
        ctrl = event.modifiers() & QtCore.Qt.ControlModifier
        alt = event.modifiers() & QtCore.Qt.AltModifier
        if (shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key_B):
            print("leave by shortcut")
            sys.exit(app.exec_())
        if (args.adminKey and shift and ctrl and alt and keyEvent.key() == QtCore.Qt.Key_A):
            print("Hit admin key")
            subprocess.Popen([args.adminKey, ""])
        if (keyEvent.key() == QtCore.Qt.Key_F4):	
            print("Alt +F4 is disabled")	
            
    def closeEvent(self, event):
        if (args.fullscreen):
            event.ignore()

    def adjustTitle(self):
        self.setWindowTitle(self.web.title())    
        
        # icon = self.web.icon()
        # self.setWindowIcon(self.web.icon())      
        
    def adjustAdressbar(self):
        self.addressBar.setText(self.web.url().toString())
        
   
class WebView(QWebEngineView):
    def __init__(self):
        self.browser = QWebEngineView.__init__(self)        
        self.setContextMenuPolicy( QtCore.Qt.NoContextMenu )
        
    def load(self,url):
        if not url:
            url = args.url
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('file:///')):
            url = 'http://' + url        
        self.setUrl(QUrl(url))      
    

class WebViewPage(QWebEnginePage):
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
        backButton.setIcon(QIcon("icons/back.png"));
        backButton.setIconSize(QSize(24, 24));
        backButton.setObjectName("backButton")
        
        msg.addButton(backButton, QtWidgets.QMessageBox.NoRole )
        
        homeButton = QtWidgets.QPushButton("Go Home")
        homeButton.setIcon(QIcon("icons/home.png"));
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

parser = ArgumentParser(
      prog='pykib',
      formatter_class= RawDescriptionHelpFormatter,
      epilog=textwrap.dedent('''\
example Usage:
        Save all .rdp files to /tmp/tmp.rdp and execute the script"/home/xfreerdp.sh /tmp/tmp.rdp", after that the file will be deleted:
            python3 pykib.py -df "rdp|/home/xfreerdp.sh|/tmp" "rdp|rm|/tmp"
        Open the site www.winteach.de in fullscreen. With the Whiteliste Option no one will be able to leave this site
            python3 pykib.py -u https://www.winteach.de -f -wl "https://www.winteach.de"
        Open the site www.winteach.de maximized and show Addressbar and navigation Buttons.
            python3 pykib.py -u https://www.winteach.de -m -sn -sa
         '''))
parser.add_argument("-u", "--url", dest="url", help="Start and Home URL", default="https://github.com/WinTeach/pykib")
parser.add_argument("-d", "--download", dest="download", nargs='?', const=True, default=False, help="Enables download function")
parser.add_argument("-dh", "--downloadHandle", dest="downloadHandle", nargs='+', help="With this option, default behaviour for special file extensions can be defined, this will also work when -d is not defined. Format: #extension#|#app_to_start#|#tmpdownloadpath#")

parser.add_argument("-t", "--title", dest="title", help="Defines the Window Title", default="pykib")
parser.add_argument("-dt", "--dynamicTitle", dest="dynamicTitle", nargs='?', const=True, default=False, help="When enabled the window title will display the current websites title")
parser.add_argument("-rt", "--removeTitleBar", dest="removeTitleBar", nargs='?', const=True, default=False, help="Removes the window title bar")
parser.add_argument("-f", "--fullscreen", dest="fullscreen", nargs='?', const=True, default=False, help="Start browser in fullscreen mode")
parser.add_argument("-ic", "--ingoreCertificates", dest="ingoreCertificates", nargs='?', const=True, default=False, help="with this option HTTPS Warninigs will be ignored")
parser.add_argument("-m", "--maximized", dest="maximized", nargs='?', const=True, default=False, help="Start browser in a maximized window")
parser.add_argument("-v", "--version", action="version", version='%(prog)s {version}'.format(version=__version__))
parser.add_argument("--no-sandbox", dest="no-sandbox", nargs='?', const=True, default=False, help="Allows to run as root")
parser.add_argument("-sa", "--showAddressBar", dest="showAddressBar", nargs='?', const=True, default=False, help="Shows a Address Bar when set")
parser.add_argument("-sn", "--showNavigationButtons", dest="showNavigationButtons", nargs='?', const=True, default=False, help="Shows Navigation Buttons when set")
parser.add_argument("-g", "--geometry", dest="geometry", default=[100,100,1024,600], nargs="+", type=int, help="Set window geomety #left# #top# #width# #height#")

parser.add_argument("-a", "--enableAdminKey",  dest="adminKey", help="Enables the admin key SHIFT+STRG+ALT+A and defines a Application which will be started when pushed")
parser.add_argument("-wl", "--whiteList",  dest="whiteList", nargs="+", help="Enables the white List function. Only Urls which start with elemtens from this list could be opend")
parser.add_argument("-l", "--logFile", dest="logFile", help="Dummy Argument for LogFile Path")

args = parser.parse_args()

if(len(args.geometry) is not 4):
    print("When geometry ist set, you have to define the whole position an screen #left# #top# #width# #height#")
    sys.exit()
    
app = QApplication(sys.argv)
 
view = MainWindow ()

#Set Dimensions
if (args.fullscreen):
    view.showFullScreen()
elif(args.maximized):
    view.showMaximized()
else:    
    view.show()     
    view.setGeometry(args.geometry[0], args.geometry[1], args.geometry[2], args.geometry[3])
  
sys.exit(app.exec_())