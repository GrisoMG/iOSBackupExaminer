# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'smsmessages_form.ui'
#
# Created: Tue Jun  2 16:43:16 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_frmSMS(object):
    def setupUi(self, frmSMS):
        frmSMS.setObjectName("frmSMS")
        frmSMS.resize(800, 600)
        self.centralwidget = QtGui.QWidget(frmSMS)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tableViewChats = QtGui.QTableView(self.centralwidget)
        self.tableViewChats.setObjectName("tableViewChats")
        self.horizontalLayout.addWidget(self.tableViewChats)
        self.tableViewMessages = QtGui.QTableView(self.centralwidget)
        self.tableViewMessages.setObjectName("tableViewMessages")
        self.horizontalLayout.addWidget(self.tableViewMessages)
        frmSMS.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        frmSMS.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(frmSMS)
        self.statusbar.setObjectName("statusbar")
        frmSMS.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(frmSMS)
        self.toolBar.setObjectName("toolBar")
        frmSMS.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionQuit = QtGui.QAction(frmSMS)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Images/data/img/exit.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionQuit.setIcon(icon)
        self.actionQuit.setObjectName("actionQuit")
        self.actionExtract = QtGui.QAction(frmSMS)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Images/data/img/unzip_app.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionExtract.setIcon(icon1)
        self.actionExtract.setObjectName("actionExtract")
        self.actionReport = QtGui.QAction(frmSMS)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/Images/data/img/open.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionReport.setIcon(icon2)
        self.actionReport.setObjectName("actionReport")
        self.toolBar.addAction(self.actionQuit)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionExtract)
        self.toolBar.addAction(self.actionReport)

        self.retranslateUi(frmSMS)
        QtCore.QObject.connect(self.actionQuit, QtCore.SIGNAL("triggered(bool)"), frmSMS.close)
        QtCore.QObject.connect(self.tableViewChats, QtCore.SIGNAL("clicked(QModelIndex)"), frmSMS.onTreeClick)
        QtCore.QObject.connect(self.actionExtract, QtCore.SIGNAL("activated()"), frmSMS.extractApp)
        QtCore.QObject.connect(self.actionReport, QtCore.SIGNAL("activated()"), frmSMS.printReport)
        QtCore.QMetaObject.connectSlotsByName(frmSMS)

    def retranslateUi(self, frmSMS):
        frmSMS.setWindowTitle(QtGui.QApplication.translate("frmSMS", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("frmSMS", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("frmSMS", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setToolTip(QtGui.QApplication.translate("frmSMS", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setShortcut(QtGui.QApplication.translate("frmSMS", "Ctrl+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExtract.setText(QtGui.QApplication.translate("frmSMS", "Extract", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExtract.setToolTip(QtGui.QApplication.translate("frmSMS", "Extract App", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExtract.setShortcut(QtGui.QApplication.translate("frmSMS", "Ctrl+E", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReport.setText(QtGui.QApplication.translate("frmSMS", "Print Report", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReport.setToolTip(QtGui.QApplication.translate("frmSMS", "Create HTML Report", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReport.setShortcut(QtGui.QApplication.translate("frmSMS", "Ctrl+P", None, QtGui.QApplication.UnicodeUTF8))

import iosbackupexaminer2_rc
