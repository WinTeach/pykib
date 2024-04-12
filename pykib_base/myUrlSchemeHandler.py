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

import platform
import logging
import subprocess
from PyQt6.QtWebEngineCore import QWebEngineUrlSchemeHandler

class myUrlSchemeHandler(QWebEngineUrlSchemeHandler):

    def requestStarted(self, job):
        url = job.requestUrl().toString()
        scheme = job.requestUrl().scheme()
        logging.debug(scheme)

        if scheme == 'workspaces':
            # if url is empty try to get workspace url from error string
            if url == "":
                logging.warning("URL is empty but workspace request detected. Trying to get workspace URL from error string (Workaround)")
                try:
                    url_array = job.requestUrl().errorString().split('"')
                    #find in url array the workspace url
                    for i in range(len(url_array)):
                        if url_array[i].startswith("workspaces://"):
                            url = url_array[i]
                            break
                    logging.debug(url)
                except:
                    logging.debug("no URL found")
                    return

            if url != "":
                if (platform.system().lower() == "linux"):
                    logging.debug("Workspaces request detected trying to run: xdg-open '" + url + "'")
                    subprocess.Popen("xdg-open '" + url + "'", shell=True)
                else:
                    logging.debug('Workspaces request detected trying to run "start ' + url)
                    subprocess.Popen("start " + url, shell=True)

        elif scheme == 'msteams':
            if (platform.system().lower() == "linux"):
                logging.debug("Teams request detected trying to run: xdg-open '" + url + "'")
                subprocess.Popen("xdg-open '" + url + "'", shell=True)
            else:
                logging.debug('Teams request detected trying to run "start ' + url)
                subprocess.Popen("start " + url, shell=True)