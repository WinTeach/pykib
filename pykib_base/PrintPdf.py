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
import os
import time
import logging
import pypdfium2 as pdfium
from itertools import count
from PIL.ImageQt import ImageQt
from PIL import Image

from PyQt6 import QtCore
from PyQt6.QtCore import pyqtSignal, QRect
from PyQt6.QtGui import QPainter

class PrintPdf(QtCore.QThread):
    printFinished = pyqtSignal()
    def __init__(self, pdf_file, printer):
        super(PrintPdf, self).__init__()
        self.pdf_file = pdf_file
        self._printer = printer

    def run(self):
        exitCounter = 0
        while not os.path.isfile(self.pdf_file):
            logging.debug("Wait for temp File (" + self.pdf_file + ") to come available")
            exitCounter += 1
            if exitCounter > 20:
                logging.error("Temp File did not come available in time")
                return
            time.sleep(0.5)

        # For Printing, we use a Method provided by digidigital, https://github.com/digidigital/Print-existing-PDF-with-PyQT6-Qt6-,
        # Thank You for Sharing. This Method worked for me on Windows on Linux it produced low quality and wrong positioned prints.
        painter = QPainter(self._printer)
        rect = painter.viewport()

        pdf = pdfium.PdfDocument(self.pdf_file)
        n_pages = len(pdf)

        fromPage = self._printer.fromPage()
        toPage = self._printer.toPage()
        printRange = range(n_pages) if fromPage == 0 else range(fromPage - 1, toPage)

        page_indices = [i for i in printRange]

        # Updated rendering logic for older pypdfium2 (no return_type argument)
        pil_images = []
        for page_index in page_indices:
            page = pdf[page_index]
            pdf_bitmap = page.render(scale=300/72)  # No return_type argument
            pil_image = pdf_bitmap.to_pil()
            pil_images.append(pil_image)

        for i, pil_image, pageNumber in zip(page_indices, pil_images, count(1)):

            if pageNumber > 1:
                self._printer.newPage()

            pilWidth, pilHeight = pil_image.size
            imageRatio = pilHeight / pilWidth

            viewportRatio = rect.height() / rect.width()

            # Rotate image if orientation is not the same as print format orientation
            if (viewportRatio < 1 and imageRatio > 1) or (viewportRatio > 1 and imageRatio < 1):
                pil_image = pil_image.transpose(Image.ROTATE_90)
                pilWidth, pilHeight = pil_image.size
                imageRatio = pilHeight / pilWidth

            # Adjust drawing area to available viewport
            if viewportRatio > imageRatio:
                y = int(rect.width() / (pilWidth / pilHeight))
                printArea = QRect(0, 0, rect.width(), y)
            else:
                x = int(pilWidth / pilHeight * rect.height())
                printArea = QRect(0, 0, x, rect.height())

            image = ImageQt(pil_image)

            # Print image
            painter.drawImage(printArea, image)
            firstPage = False

        # Cleanup
        pdf.close()
        painter.end()

        del self._printer
        #delete pdf file
        os.remove(self.pdf_file)

        self.printFinished.emit()
