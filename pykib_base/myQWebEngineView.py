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
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QIcon
from PyQt6.QtGui import QAction
from PyQt6 import QtNetwork
from urllib.parse import quote, urlparse

from functools import partial
import re
import os
import logging
import socket

class myQWebEngineView(QWebEngineView):

    def __init__(self, argsparsed, dirnameparsed, parent, tabIndex=0):
        self.args = argsparsed
        self.dirname = dirnameparsed
        self.parent = parent
        self.tabIndex = tabIndex

        #create random debug id
        self.randomId = str(os.urandom(8).hex())
        super().__init__()

    def load(self, url):
        # Prepare and load the given URL.
        # If a proxy is configured, set it before loading the URL.
        url = self.getUrl(url.strip())
        if (self.args.proxy):
            self.setProxy(url)
        self.setUrl(QUrl(url))

    def getUrl(self, url) -> str:
        # Returns a valid URL string.
        # If the input is already a valid URL, return it.
        # If it looks like a domain, prepend 'https://'.
        # Otherwise, use the configured search engine to build a search URL.
        parsed = urlparse(url)
        if bool(parsed.scheme and parsed.netloc) or (bool(parsed.scheme and parsed.path) and parsed.scheme == 'file'):
            return url

        if self.isUrl(url):
            return "https://" + url

        if (self.args.addressBarSearchEngine):
            # Search with search engine
            query = quote(url)
            url = self.args.addressBarSearchEngine.replace('{query}', query)
            logging.debug("Search with search engine: " + url)
            return url

        # If the input is not a valid URL or domain, prepend 'https://' and hope for the best.
        return "https://" + url

    def isUrl(self, url) -> bool:
        # Checks if the given string is a valid URL (domain format).
        # Returns True if it matches a domain pattern, otherwise False.
        if " " in url:
            return False

        return re.match(r"^[\w\-\.]+\.[a-z]{2,}(\/.*)?$", url, re.IGNORECASE) is not None

    def setProxy(self, url):
        # Set Proxy
        try:
            ip = socket.gethostbyname(url.split('/')[2])
            logging.debug("IP for " + url + " is " + ip)
            if (self.args.proxyDisabledForLocalIp and (ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.16.'))):
                # No Proxy for local IPs
                logging.debug("No Proxy for:" + url)
                QtNetwork.QNetworkProxy.setApplicationProxy(
                    QtNetwork.QNetworkProxy(QtNetwork.QNetworkProxy.ProxyType.NoProxy))
                return
        except socket.gaierror as e:
            logging.warning(f"Unable to resolve IP for {url}: {e}")

        logging.debug("Set Proxy for:" + url)
        proxy = QtNetwork.QNetworkProxy()
        proxy.setType(QtNetwork.QNetworkProxy.ProxyType.HttpProxy)
        proxy.setHostName(self.args.proxy)
        proxy.setPort(self.args.proxyPort)
        if (self.args.proxyUsername and self.args.proxyPassword):
            proxy.setUser(self.args.proxyUsername);
            proxy.setPassword(self.args.proxyPassword);
        elif (self.args.proxyUsername or self.args.proxyPassword):
            logging.error("It is not possible to use a proxy username without password")
        QtNetwork.QNetworkProxy.setApplicationProxy(proxy)
        return

    def contextMenuEvent(self, event):
        self.menu = self.createStandardContextMenu()

        #Remove Menu Entries:
        unwantedMenuEntries = {
            QWebEnginePage.WebAction.PasteAndMatchStyle.value,
            QWebEnginePage.WebAction.OpenLinkInNewWindow.value,
            QWebEnginePage.WebAction.DownloadLinkToDisk.value,
            QWebEnginePage.WebAction.SavePage.value,
            QWebEnginePage.WebAction.ViewSource.value
        }

        if (not self.args.allowManageTabs):
            unwantedMenuEntries.add(QWebEnginePage.WebAction.OpenLinkInNewTab.value)

        iconMap = {
            0 : QIcon(os.path.join(self.dirname, 'icons/back.png')),
            1 : QIcon(os.path.join(self.dirname, 'icons/forward.png')),
            3 : QIcon(os.path.join(self.dirname, 'icons/refresh.png'))
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
        if(self.args.remoteBrowserDaemon):
            closeButton = QAction(QIcon(os.path.join(self.dirname, 'icons/close.png')), 'Close Remote Tab', self)
            closeButton.setStatusTip('Close Remote Browser Tab')
            closeButton.triggered.connect(self.closeByMenu)
            self.menu.addSeparator()
            self.menu.addAction(closeButton)

        if(self.args.enableCleanupBrowserProfileOption):
            self.menu.addSeparator()
            advancedMenu = self.menu.addMenu(QIcon(os.path.join(self.dirname, 'icons/settings.png')), 'Advanced')

            # Delete All Cookies
            deleteAllCookiesButton = QAction(QIcon(os.path.join(self.dirname, 'icons/cleanup.png')),
                                             'Cleanup Browser Profile', self)
            deleteAllCookiesButton.setStatusTip('Delete Cookies for Current Site')
            deleteAllCookiesButton.triggered.connect(partial(self.parent.enableCleanupBrowserProfileOption))
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
        except AttributeError as e:
            logging.debug(f'No Parent to close found: {e}')
        except Exception as e:
            logging.error(f'Unexpected error while closing parent: {e}')

