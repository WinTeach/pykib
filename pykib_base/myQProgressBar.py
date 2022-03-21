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

from PyQt6.QtWidgets import QProgressBar

LOADING = """
QProgressBar{
    border: 0px;
    border-radius: 0px;
    text-align: center;
    
}

QProgressBar::chunk {
    background-color: lightblue;
}
"""

DOWNLOAD = """
QProgressBar{
    border: 0px;
    border-radius: 0px;
    text-align: right; 
}

QProgressBar::chunk {
    color: blue;
    background-color: #f2b059;
}
"""

MEMORYCAP = """
QProgressBar{
    border: 0px;
    border-radius: 0px;
    text-align: center; 
}

QProgressBar::chunk {
    color: blue;
    background-color: #FF5E71;
}
"""

class myQProgressBar(QProgressBar):
    disabled = False
    
    def __init__(self, parent = None):
        QProgressBar.__init__(self, parent)
        self.changeStyle("loading")
    
    def changeStyle(self, style):
        if(style == "loading"):
            self.setStyleSheet(LOADING)
        elif(style == "download"):
            self.setStyleSheet(DOWNLOAD)
        elif (style == "memorycap"):
            self.setStyleSheet(MEMORYCAP)