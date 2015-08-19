# -*- coding: utf-8 -*-
'''
Thremma Xtract v2.1
- Threema Backup Messages Extractor for iPhone (not Android)

Released on MMM DD YYYY
Last Update MMM DD YYYY ()


Tested with python 2.7.6, pyside 1.2.2

Changelog:

V1.0 (created by  - MMM DD, YYY)
- first release, iPhone only:

(C)opyright 2015  (C)opyright 2015 GrisoMG

'''

from PySide import QtCore, QtGui, QtSql
from PySide.QtCore import Qt
from gui.sqlbrowser_form import Ui_Browser


class sqlBrowserGUI(QtGui.QMainWindow):
    def __init__(self, sqlitedb=None, path=None, dbname=None):
        QtGui.QMainWindow.__init__(self)

        self.ui = Ui_Browser()
        self.ui.setupUi(self)
        self.ui.treeWidgetDB.setColumnCount(5)
        self.ui.treeWidgetDB.setColumnHidden(1, True)

        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.path = path
        self.dbname = dbname
        self.dbsystables = None
        self.dbsystablesrecord = None
        self.dbtables = None
        self.dbviews = None

        self.createConnection(sqlitedb)

        self.ui.treeWidgetDB.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeWidgetDB.customContextMenuRequested.connect(self.ctxMenu)
        self.ui.txtSqlEdit.installEventFilter(self)


        if self.sqlitedb.isOpen():
            self.dbsystables = self.sqlitedb.tables(QtSql.QSql.SystemTables)
            self.dbtables = self.sqlitedb.tables(QtSql.QSql.Tables)
            self.dbviews = self.sqlitedb.tables(QtSql.QSql.Views)

        self.treeDatabase()

    def eventFilter(self, widget, event):
        if (event.type() == QtCore.QEvent.KeyPress and widget is self.ui.txtSqlEdit):
            if event.key() == QtCore.Qt.Key_Return:
                self.executeSQL()
        pass

    def createConnection(self, db):
        self.sqlitedb = QtSql.QSqlDatabase.addDatabase('QSQLITE')
        self.sqlitedb.setDatabaseName(db)
        if self.sqlitedb.open():
            return True
        else:
            print (self.sqlitedb.lastError().text())
            return False

    def treeDatabase(self):

        self.ui.treeWidgetDB.setHeaderLabels(('Schema ' + self.dbname + ';' + 'T/R' + ';' + 'Type' + ';' + 'Required' + ';' + 'Generated').split(';'))


        dbSysTables = QtGui.QTreeWidgetItem(None)
        dbSysTables.setText(0, 'System Tables')
        self.ui.treeWidgetDB.addTopLevelItem(dbSysTables)
        for table in self.dbsystables:
            newTable = QtGui.QTreeWidgetItem(dbSysTables)
            newTable.setText(0, table)
            newTable.setText(1, 'T')
            self.ui.treeWidgetDB.addTopLevelItem(newTable)

            dbrecord = self.sqlitedb.record(table)

            if dbrecord.count() > 0:
                i = 0
                for i in range(dbrecord.count()):
                    name = dbrecord.field(i).name()
                    type = dbrecord.field(i).type()
                    requiredStatus = dbrecord.field(i).requiredStatus().name
                    generated = dbrecord.field(i).isGenerated()
                    if generated == True:
                        generated = 'True'
                    else:
                        generated = 'False'
                    newRecord = QtGui.QTreeWidgetItem(newTable)
                    newRecord.setText(0, name)
                    newRecord.setText(1, 'R')
                    newRecord.setText(2, type.__name__)
                    newRecord.setText(3, requiredStatus)
                    newRecord.setText(4, generated)
                    self.ui.treeWidgetDB.addTopLevelItem(newRecord)
                    i += 1

        dbTables = QtGui.QTreeWidgetItem(None)
        dbTables.setText(0, 'Tables')
        self.ui.treeWidgetDB.addTopLevelItem(dbTables)
        for table in self.dbtables:
            newTable = QtGui.QTreeWidgetItem(dbTables)
            newTable.setText(0, table)
            newTable.setText(1, 'T')
            self.ui.treeWidgetDB.addTopLevelItem(newTable)

            dbrecord = self.sqlitedb.record(table)

            if dbrecord.count() > 0:
                i = 0
                for i in range(dbrecord.count()):
                    name = dbrecord.field(i).name()
                    type = dbrecord.field(i).type()
                    requiredStatus = dbrecord.field(i).requiredStatus().name
                    generated = dbrecord.field(i).isGenerated()
                    if generated == True:
                        generated = 'True'
                    else:
                        generated = 'False'
                    newRecord = QtGui.QTreeWidgetItem(newTable)
                    newRecord.setText(0, name)
                    newRecord.setText(1, 'R')
                    newRecord.setText(2, type.__name__)
                    newRecord.setText(3, requiredStatus)
                    newRecord.setText(4, generated)
                    self.ui.treeWidgetDB.addTopLevelItem(newRecord)
                    i += 1

        dbViews = QtGui.QTreeWidgetItem(None)
        dbViews.setText(0, 'Views')
        self.ui.treeWidgetDB.addTopLevelItem(dbViews)
        for table in self.dbviews:
            newTable = QtGui.QTreeWidgetItem(dbViews)
            newTable.setText(0, table)
            newTable.setText(1, 'T')
            self.ui.treeWidgetDB.addTopLevelItem(newTable)

            dbrecord = self.sqlitedb.record(table)

            if dbrecord.count() > 0:
                i = 0
                for i in range(dbrecord.count()):
                    name = dbrecord.field(i).name()
                    type = dbrecord.field(i).type()
                    requiredStatus = dbrecord.field(i).requiredStatus().name
                    generated = dbrecord.field(i).isGenerated()
                    if generated == True:
                        generated = 'True'
                    else:
                        generated = 'False'
                    newRecord = QtGui.QTreeWidgetItem(newTable)
                    newRecord.setText(0, name)
                    newRecord.setText(1, 'R')
                    newRecord.setText(2, type.__name__)
                    newRecord.setText(3, requiredStatus)
                    newRecord.setText(4, generated)
                    self.ui.treeWidgetDB.addTopLevelItem(newRecord)
                    i += 1

    def ctxMenu(self, pos):

        # managing "standard" files
        selectedItem = self.ui.treeWidgetDB.currentItem()
        if (not selectedItem) or str(selectedItem.text(1)) is not 'T':
            return


        menu = QtGui.QMenu()
        action1 = QtGui.QAction("Open table", self)
        action1.triggered.connect(self.openTable)
        menu.addAction(action1)
        menu.exec_(self.ui.treeWidgetDB.mapToGlobal(pos))

    def openTable(self):

        selectedItem = self.ui.treeWidgetDB.currentItem()
        table = str(selectedItem.text(0))
        cmd = "SELECT * FROM %s" %table
        model =  QtSql.QSqlQueryModel()
        model.setQuery(cmd)

        self.ui.tableViewTable.setModel(model)


    def executeSQL(self):
        cmd = self.ui.txtSqlEdit.text()
        model =  QtSql.QSqlQueryModel()
        model.setQuery(cmd)
        self.ui.tableViewTable.setModel(model)
