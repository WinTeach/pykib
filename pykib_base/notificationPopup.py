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

import os
import logging

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QVBoxLayout, QPushButton
from PyQt6.QtWebEngineCore import QWebEngineNotification
from PyQt6.QtGui import QPixmap, QMouseEvent, QCloseEvent, QFont, QGuiApplication, QIcon
from PyQt6.QtMultimedia import QSoundEffect



class NotificationPopup(QWidget):
    def __init__(self, parent) -> None:
        super().__init__()
        self.parent = parent
        self.notification = None
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.WindowStaysOnTopHint)

        self.soundEffect = QSoundEffect()
        self.soundEffect.setSource(QUrl.fromLocalFile(os.path.join(self.parent.dirname, 'sounds/bell.wav')))

        self.notificationTitle, self.notificationIcon, self.notificationMessage, self.notificationSender = QLabel(), QLabel(), QLabel(), QLabel()

        closeButton = QPushButton()
        closeButton.setIcon(QIcon(os.path.join(self.parent.dirname, 'icons/close.png')))
        closeButton.clicked.connect(self.onClosed)

        notificationTitleFont = QFont()
        notificationTitleFont.setBold(True)
        notificationTitleFont.setPointSize(10)
        self.notificationTitle.setFont(notificationTitleFont)

        notificationMessageFont = QFont()
        notificationMessageFont.setPointSize(10)
        self.notificationMessage.setFont(notificationMessageFont)

        notificationSenderFont = QFont()
        notificationSenderFont.setItalic(True)
        self.notificationSender.setFont(notificationSenderFont)

        iconMessageDividerLayout = QHBoxLayout()
        iconMessageDividerLayout.addWidget(self.notificationIcon)

        messageLayout = QVBoxLayout()
        iconMessageDividerLayout.addLayout(messageLayout)
        messageLayout.addWidget(self.notificationMessage)
        messageLayout.setAlignment(self.notificationMessage, Qt.AlignmentFlag.AlignTop)

        messageLayout.addWidget(self.notificationSender)
        messageLayout.setAlignment(self.notificationSender, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        titleLayout = QHBoxLayout()
        titleLayout.addWidget(self.notificationTitle)
        titleLayout.setAlignment(self.notificationTitle, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignCenter)
        titleLayout.addWidget(closeButton)
        titleLayout.setAlignment(closeButton, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignCenter)

        notificationLayout = QVBoxLayout(self)
        notificationLayout.addLayout(titleLayout)
        notificationLayout.addLayout(iconMessageDividerLayout)


    def present(self, newNotification: QWebEngineNotification):
        if self.notification:
            self.notification.close()
        self.notification = newNotification

        logging.debug("--- Presend Notification --- ")
        logging.debug("from:   " + self.notification.origin().toString())
        logging.debug("title: " + self.notification.title())
        logging.debug("message: " + self.notification.message())

        self.setWindowTitle(self.notification.title())
        self.setWindowIcon(self.parent.windowIcon())

        self.notificationTitle.setText(self.notification.title())
        self.notificationMessage.setText(self.notification.message())
        self.notificationSender.setText(self.notification.origin().toString())
        #One time seems to be not enough
        self.adjustSize()
        self.adjustSize()

        iconHeigth = self.notificationIcon.height()
        if(iconHeigth > 100):
            iconHeigth = 100
        elif(iconHeigth < 50):
            iconHeigth = 50

        self.notificationIcon.setPixmap(QPixmap.fromImage(self.notification.icon())
                                        .scaledToHeight(iconHeigth))
        self.show()
        self.notification.show()

        self.notification.closed.connect(self.onClosed)

        if not self.parent.args.remoteBrowserDaemon:
            self.parent.tray.setIcon(self.parent.windowIcon())
            self.parent.tray.setToolTip("Message from "+self.notification.origin().toString())
            self.parent.tray.setVisible(True)
            self.parent.tray.show()

        notificationPositionX = QGuiApplication.primaryScreen().availableGeometry().right() - self.width() - 20
        notificationPositionY = QGuiApplication.primaryScreen().availableGeometry().bottom() - self.height() - 40

        self.move(notificationPositionX, notificationPositionY)

        self.soundEffect.play()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if not self.parent.args.remoteBrowserDaemon:
            self.parent.setWindowState(self.parent.restoreState)
            self.parent.activateWindow()
            self.parent.show()
            if not self.parent.args.enableTrayMode:
                self.parent.tray.setVisible(False)
                self.parent.tray.setToolTip("")
        if self.notification:
            self.notification.click()
            self.onClosed()

    def closeEvent(self, event: QCloseEvent):
        self.onClosed()

    def onClosed(self):
        self.hide()
        if self.notification:
            self.notification.close()
        self.notification = None

