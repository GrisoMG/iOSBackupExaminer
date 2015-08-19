# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui/about_window.ui'
#
# Created: Wed Aug 19 13:46:34 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.1
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_AboutWindow(object):
    def setupUi(self, AboutWindow):
        AboutWindow.setObjectName("AboutWindow")
        AboutWindow.resize(494, 493)
        self.about_url = QtGui.QLabel(AboutWindow)
        self.about_url.setGeometry(QtCore.QRect(10, 470, 375, 17))
        self.about_url.setTextFormat(QtCore.Qt.RichText)
        self.about_url.setObjectName("about_url")
        self.plainTextEdit = QtGui.QPlainTextEdit(AboutWindow)
        self.plainTextEdit.setGeometry(QtCore.QRect(0, 150, 491, 301))
        self.plainTextEdit.setObjectName("plainTextEdit")
        self.label_3 = QtGui.QLabel(AboutWindow)
        self.label_3.setGeometry(QtCore.QRect(10, 121, 375, 17))
        self.label_3.setObjectName("label_3")
        self.about_copyright = QtGui.QLabel(AboutWindow)
        self.about_copyright.setGeometry(QtCore.QRect(10, 98, 375, 17))
        self.about_copyright.setObjectName("about_copyright")
        self.label = QtGui.QLabel(AboutWindow)
        self.label.setGeometry(QtCore.QRect(10, 52, 375, 17))
        self.label.setObjectName("label")
        self.about_version = QtGui.QLabel(AboutWindow)
        self.about_version.setGeometry(QtCore.QRect(10, 75, 375, 17))
        self.about_version.setObjectName("about_version")
        self.about_title = QtGui.QLabel(AboutWindow)
        self.about_title.setGeometry(QtCore.QRect(10, 20, 375, 26))
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setWeight(75)
        font.setBold(True)
        self.about_title.setFont(font)
        self.about_title.setTextFormat(QtCore.Qt.RichText)
        self.about_title.setObjectName("about_title")
        self.pushButtonOK = QtGui.QPushButton(AboutWindow)
        self.pushButtonOK.setGeometry(QtCore.QRect(400, 460, 85, 27))
        self.pushButtonOK.setObjectName("pushButtonOK")

        self.retranslateUi(AboutWindow)
        QtCore.QObject.connect(self.pushButtonOK, QtCore.SIGNAL("clicked()"), AboutWindow.close)
        QtCore.QMetaObject.connectSlotsByName(AboutWindow)

    def retranslateUi(self, AboutWindow):
        AboutWindow.setWindowTitle(QtGui.QApplication.translate("AboutWindow", "About", None, QtGui.QApplication.UnicodeUTF8))
        self.about_url.setText(QtGui.QApplication.translate("AboutWindow", "<html><head/><body><p><br/></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.plainTextEdit.setPlainText(QtGui.QApplication.translate("AboutWindow", "    iOSBackupExaminer - Read and analyze iOS Backups\n"
"    Copyright (C) 2015 GrisoMG\n"
"\n"
"    This program is free software: you can redistribute it and/or modify\n"
"    it under the terms of the GNU General Public License as published by\n"
"    the Free Software Foundation, either version 3 of the License, or\n"
"    (at your option) any later version.\n"
"\n"
"    This program is distributed in the hope that it will be useful,\n"
"    but WITHOUT ANY WARRANTY; without even the implied warranty of\n"
"    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the\n"
"    GNU General Public License for more details.\n"
"\n"
"    You should have received a copy of the GNU General Public License\n"
"    along with this program.  If not, see <http://www.gnu.org/licenses/>.", None, QtGui.QApplication.UnicodeUTF8))
        self.label_3.setText(QtGui.QApplication.translate("AboutWindow", "Released under GPL License:", None, QtGui.QApplication.UnicodeUTF8))
        self.about_copyright.setText(QtGui.QApplication.translate("AboutWindow", "<html><head/><body><p>Copyright (C) 2015 GrisoMG</body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("AboutWindow", "Open Source tool for iOS backup data extraction and analysis", None, QtGui.QApplication.UnicodeUTF8))
        self.about_version.setText(QtGui.QApplication.translate("AboutWindow", "Version:", None, QtGui.QApplication.UnicodeUTF8))
        self.about_title.setText(QtGui.QApplication.translate("AboutWindow", "iOS Backup Examiner", None, QtGui.QApplication.UnicodeUTF8))
        self.pushButtonOK.setText(QtGui.QApplication.translate("AboutWindow", "&Ok", None, QtGui.QApplication.UnicodeUTF8))

