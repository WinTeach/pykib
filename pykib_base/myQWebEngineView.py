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


class myQWebEngineView(QWebEngineView):
    def __init__(self):
        self.browser = QWebEngineView.__init__(self)        
        self.setContextMenuPolicy( QtCore.Qt.NoContextMenu )
        
    def load(self,url):
        if not url:
            url = args.url
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('file:///')):
            url = 'http://' + url        
        self.setUrl(QUrl(url))     