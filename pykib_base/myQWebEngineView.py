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

from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5 import QtCore
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QTextEdit


class myQWebEngineView(QWebEngineView):
    

    def __init__(self, argsparsed):
        global args
        args = argsparsed
        self.browser = QWebEngineView.__init__(self)        
        self.setContextMenuPolicy( QtCore.Qt.NoContextMenu )
        
        # self.setContextMenuPolicy( QtCore.Qt.CustomContextMenu )
        # self.customContextMenuRequested.connect(self.show_custom_context_menu)
        
        
    def load(self,url):
        if not url:
            url = args.url
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('file:///') or url.startswith('chrome-extension://')):
            url = 'http://' + url        
        self.setUrl(QUrl(url))
        