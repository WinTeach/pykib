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

from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QAction
from PyQt6 import QtNetwork

from functools import partial

import os
import logging
import socket

class myQWebEngineView(QWebEngineView):

    def __init__(self, argsparsed, dirnameparsed, parent):
        global args
        args = argsparsed

        global dirname
        dirname = dirnameparsed
        self.parent = parent;
        self.browser = QWebEngineView.__init__(self)

    def load(self, url):
        logging.debug("Load URL:" + url)
        if not url:
             url = args.url
        if not (url.startswith('http://') or url.startswith('https://') or url.startswith('file://')):
             url = 'http://' + url

        if (args.proxy):
            self.setProxy(url)

        self.setUrl(QUrl(url))

    def setProxy(self, url):
        # Set Proxy
        ip = socket.gethostbyname(url.split('/')[2])
        logging.debug("IP for " + url + " is " + ip)
        if (args.proxyDisabledForLocalIp and (ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.16.'))):
            # No Proxy for local IPs
            logging.debug("No Proxy for:" + url)
            QtNetwork.QNetworkProxy.setApplicationProxy(
                QtNetwork.QNetworkProxy(QtNetwork.QNetworkProxy.ProxyType.NoProxy))
            return

        logging.debug("Set Proxy for:" + url)
        proxy = QtNetwork.QNetworkProxy()
        proxy.setType(QtNetwork.QNetworkProxy.ProxyType.HttpProxy)
        proxy.setHostName(args.proxy)
        proxy.setPort(args.proxyPort)
        if (args.proxyUsername and args.proxyPassword):
            proxy.setUser(args.proxyUsername);
            proxy.setPassword(args.proxyPassword);
        elif (args.proxyUsername or args.proxyPassword):
            logging.error("It is not possible to use a proxy username without password")
        QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
        return

    def contextMenuEvent(self, event):
        self.menu = self.createStandardContextMenu()

        #Remove Menu Entryies by Id:
        #11 -> Paste and match Style
        #13 -> Open in New Tab
        #14 -> Open in New Window
        #16 -> Save Link
        #30 -> View Source
        #32 -> Save Page
        unwantedMenuEntries = {11, 16, 13, 14, 32, 30}

        iconMap = {
            0 : QIcon(os.path.join(dirname, 'icons/back.png')),
            1 : QIcon(os.path.join(dirname, 'icons/forward.png')),
            3 : QIcon(os.path.join(dirname, 'icons/refresh.png'))
        }

        for menuAction in self.menu.actions():
            #Remove Item From Default Menu
            #View Source
            if(menuAction.data() in unwantedMenuEntries):
                self.menu.removeAction(menuAction)
            else:
                logging.debug(str(menuAction.data()))
                try:
                    menuAction.setIcon(iconMap[menuAction.data()])
                except:
                    logging.debug('No Icon found for context menu entry ' + str(menuAction.data()))

        # Adding Close Button (for remoteDameonMode)
        if(args.remoteBrowserDaemon):
            closeButton = QAction(QIcon(os.path.join(dirname, 'icons/close.png')), 'Close Remote Tab', self)
            closeButton.setStatusTip('Close Remote Browser Tab')
            closeButton.triggered.connect(self.closeByMenu)
            self.menu.addSeparator()
            self.menu.addAction(closeButton)

        if(args.enableCleanupBrowserProfileOption):
            self.menu.addSeparator()
            advancedMenu = self.menu.addMenu(QIcon(os.path.join(dirname, 'icons/settings.png')), 'Advanced')

            # Delete All Cookies
            deleteAllCookiesButton = QAction(QIcon(os.path.join(dirname, 'icons/cleanup.png')),
                                             'Cleanup Browser Profile', self)
            deleteAllCookiesButton.setStatusTip('Delete Cookies for Current Site')
            deleteAllCookiesButton.triggered.connect(partial(self.parent.page.enableCleanupBrowserProfileOption))
            advancedMenu.addAction(deleteAllCookiesButton)

        self.menu.popup(event.globalPos())

    def closeByMenu(self):

        try:
            self.close()
        except:
            logging.debug('Nothing to close')

        try:
            self.parent.close()
            self.parent.deleteLater()
            self.deleteLater()
        except:
            logging.debug('No Parent to close found')

