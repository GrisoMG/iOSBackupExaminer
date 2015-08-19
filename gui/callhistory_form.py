# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'callhistory_form.ui'
#
# Created: Tue Jun  2 16:29:07 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_frmCallHistory(object):
    def setupUi(self, frmCallHistory):
        frmCallHistory.setObjectName("frmCallHistory")
        frmCallHistory.resize(800, 600)
        self.centralwidget = QtGui.QWidget(frmCallHistory)
        self.centralwidget.setObjectName("centralwidget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.centralwidget)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tableViewCalls = QtGui.QTableView(self.centralwidget)
        self.tableViewCalls.setObjectName("tableViewCalls")
        self.horizontalLayout.addWidget(self.tableViewCalls)
        frmCallHistory.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        frmCallHistory.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(frmCallHistory)
        self.statusbar.setObjectName("statusbar")
        frmCallHistory.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(frmCallHistory)
        self.toolBar.setObjectName("toolBar")
        frmCallHistory.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionQuit = QtGui.QAction(frmCallHistory)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Images/data/img/exit.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionQuit.setIcon(icon)
        self.actionQuit.setObjectName("actionQuit")
        self.actionExtract = QtGui.QAction(frmCallHistory)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/Images/data/img/unzip_app.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionExtract.setIcon(icon1)
        self.actionExtract.setObjectName("actionExtract")
        self.actionReport = QtGui.QAction(frmCallHistory)
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(":/Images/data/img/open.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionReport.setIcon(icon2)
        self.actionReport.setObjectName("actionReport")
        self.toolBar.addAction(self.actionQuit)
        self.toolBar.addSeparator()
        self.toolBar.addAction(self.actionExtract)
        self.toolBar.addAction(self.actionReport)

        self.retranslateUi(frmCallHistory)
        QtCore.QObject.connect(self.actionQuit, QtCore.SIGNAL("triggered(bool)"), frmCallHistory.close)
        QtCore.QObject.connect(self.actionExtract, QtCore.SIGNAL("activated()"), frmCallHistory.extractApp)
        QtCore.QObject.connect(self.actionReport, QtCore.SIGNAL("activated()"), frmCallHistory.printReport)
        QtCore.QMetaObject.connectSlotsByName(frmCallHistory)

    def retranslateUi(self, frmCallHistory):
        frmCallHistory.setWindowTitle(QtGui.QApplication.translate("frmCallHistory", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("frmCallHistory", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("frmCallHistory", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setToolTip(QtGui.QApplication.translate("frmCallHistory", "Quit", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setShortcut(QtGui.QApplication.translate("frmCallHistory", "Ctrl+Q", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExtract.setText(QtGui.QApplication.translate("frmCallHistory", "Extract", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExtract.setToolTip(QtGui.QApplication.translate("frmCallHistory", "Extract App", None, QtGui.QApplication.UnicodeUTF8))
        self.actionExtract.setShortcut(QtGui.QApplication.translate("frmCallHistory", "Ctrl+E", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReport.setText(QtGui.QApplication.translate("frmCallHistory", "Print Report", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReport.setToolTip(QtGui.QApplication.translate("frmCallHistory", "Create HTML Report", None, QtGui.QApplication.UnicodeUTF8))
        self.actionReport.setShortcut(QtGui.QApplication.translate("frmCallHistory", "Ctrl+P", None, QtGui.QApplication.UnicodeUTF8))

import iosbackupexaminer2_rc
