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

from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QTabBar, QLabel, QSizePolicy, QWidget, QHBoxLayout, QToolButton


class MyTabBar(QTabBar):
    middleMouseButtonClicked = pyqtSignal(int)  # Tab-Index als Argument
    closeTabClicked = pyqtSignal(int)  # Tab-Index als Argument

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.MiddleButton:
            tab_index = self.tabAt(event.position().toPoint())
            self.middleMouseButtonClicked.emit(tab_index)
        super().mousePressEvent(event)

    def addButtonTab(self, web, icon, allowManageTabs=False):
        index = self.addTab("")

        web.tabIndex = index
        textLabel = QLabel(web.url().toString())
        textLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        textLabel.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        iconLabel = QLabel()

        labelContainer = QWidget()
        if allowManageTabs:
            labelContainer.setMinimumWidth(160)
            labelContainer.setMaximumWidth(160)
        else:
            labelContainer.setMinimumWidth(175)
            labelContainer.setMaximumWidth(175)
        labelContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        labelLayout = QHBoxLayout(labelContainer)
        labelLayout.setContentsMargins(4, 0, 4, 0)
        labelLayout.setSpacing(4)
        labelLayout.addWidget(iconLabel)
        labelLayout.addWidget(textLabel)

        tabButtonWidget = QWidget()
        tabLayout = QHBoxLayout(tabButtonWidget)
        tabLayout.setContentsMargins(0, 0, 4, 0)
        tabLayout.setSpacing(0)
        tabLayout.addWidget(labelContainer)
        if allowManageTabs:
            closeButton = QToolButton()
            closeButton.setIcon(icon)
            closeButton.setStyleSheet("QToolButton { border: none; padding: 0px; }")
            closeButton.setCursor(Qt.CursorShape.PointingHandCursor)
            closeButton.setFixedSize(16, 16)
            closeButton.setStyleSheet("""
                            QToolButton {
                                border: none;
                                padding: 0px;
                                background: transparent;
                            }
                            QToolButton:hover {
                                border: 1px solid #888;
                                border-radius: 3px;
                                background-color: #f0f0f0;
                            }
                        """)
            closeButton.clicked.connect(lambda: self.closeTab(web.tabIndex))
            tabLayout.addWidget(closeButton)

        self.setTabButton(index, QTabBar.ButtonPosition.LeftSide, tabButtonWidget)
        self.setCurrentIndex(index)
        return index, iconLabel, textLabel

    def closeTab(self, index):
        self.closeTabClicked.emit(index)