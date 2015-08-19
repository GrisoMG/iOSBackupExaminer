# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'sqlbrowser_form.ui'
#
# Created: Fri May 29 09:34:02 2015
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Browser(object):
    def setupUi(self, Browser):
        Browser.setObjectName("Browser")
        Browser.resize(800, 600)
        self.centralwidget = QtGui.QWidget(Browser)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtGui.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.treeWidgetDB = QtGui.QTreeWidget(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.MinimumExpanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.treeWidgetDB.sizePolicy().hasHeightForWidth())
        self.treeWidgetDB.setSizePolicy(sizePolicy)
        self.treeWidgetDB.setHorizontalScrollMode(QtGui.QAbstractItemView.ScrollPerItem)
        self.treeWidgetDB.setObjectName("treeWidgetDB")
        self.treeWidgetDB.headerItem().setText(0, "1")
        self.horizontalLayout.addWidget(self.treeWidgetDB)
        self.gridLayout.addLayout(self.horizontalLayout, 0, 0, 1, 1)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.tableViewTable = QtGui.QTableView(self.centralwidget)
        self.tableViewTable.setObjectName("tableViewTable")
        self.horizontalLayout_2.addWidget(self.tableViewTable)
        self.gridLayout.addLayout(self.horizontalLayout_2, 0, 1, 1, 1)
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.txtSqlEdit = QtGui.QTextEdit(self.centralwidget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.txtSqlEdit.sizePolicy().hasHeightForWidth())
        self.txtSqlEdit.setSizePolicy(sizePolicy)
        self.txtSqlEdit.setObjectName("txtSqlEdit")
        self.verticalLayout.addWidget(self.txtSqlEdit)
        self.gridLayout.addLayout(self.verticalLayout, 1, 0, 1, 2)
        Browser.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar()
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 22))
        self.menubar.setObjectName("menubar")
        Browser.setMenuBar(self.menubar)
        self.statusbar = QtGui.QStatusBar(Browser)
        self.statusbar.setObjectName("statusbar")
        Browser.setStatusBar(self.statusbar)
        self.toolBar = QtGui.QToolBar(Browser)
        self.toolBar.setObjectName("toolBar")
        Browser.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)
        self.actionQuit = QtGui.QAction(Browser)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/Images/data/img/exit.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionQuit.setIcon(icon)
        self.actionQuit.setObjectName("actionQuit")
        self.toolBar.addAction(self.actionQuit)

        self.retranslateUi(Browser)
        QtCore.QObject.connect(self.actionQuit, QtCore.SIGNAL("activated()"), Browser.close)
        QtCore.QMetaObject.connectSlotsByName(Browser)

    def retranslateUi(self, Browser):
        Browser.setWindowTitle(QtGui.QApplication.translate("Browser", "MainWindow", None, QtGui.QApplication.UnicodeUTF8))
        self.toolBar.setWindowTitle(QtGui.QApplication.translate("Browser", "toolBar", None, QtGui.QApplication.UnicodeUTF8))
        self.actionQuit.setText(QtGui.QApplication.translate("Browser", "Quit", None, QtGui.QApplication.UnicodeUTF8))

import iosbackupexaminer2_rc
