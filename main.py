#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
iOS Backup Extractor/Analyzer

Released on MMM DD YYYY
Last Update MMM DD YYYY ()


Tested with iOS >6.x, python 2.7.6, pyside 1.2.2

Changelog:

V0.8 (created by  - MMM DD, YYY)
- first release, iPhone only:

(C)opyright 2015    GrisoMG

Thanks to
  Fabio Sangiacomo <fabio.sangiacomo@digital-forensics.it>
  Martina Weidner  <martina.weidner@freenet.ch>
  iphone-dataprotection Team: https://code.google.com/p/iphone-dataprotection/
'''
import os, sys, sqlite3, collections
from os.path import expanduser

from PySide import QtCore, QtGui
from PySide.QtCore import Qt, QSettings
from PySide.QtGui import QCursor, QApplication

from backups.backup4 import MBDB
from keystore.keybag import Keybag
from backups.backup4 import MBFileRecordFromDB
from backup_tool import readManifest, readInfo, iOSBackupDB, store2db

from gui.main_window import Ui_MainWindow
from gui.about_window import Ui_AboutWindow

from threema_xtract import threemaGUI
from addressbook_xtract import contactsGUI
from sms_xtract import smsGUI
from callhistory_xtract import callhistoryGUI
from whatsapp_xtract import whatsappGUI

from iOSForensicClasses import makeTmpDir, rmTmpDir
from sql_browser import sqlBrowserGUI


iOSBEName = "iOS (6-8) Backup Examiner"
iOSBEVersion = "0.8 build 20150609"
iOSBEVersionDate = "Jun 2015"
iOSBECC = '<html><head/><body><p>Copyright (C) 2015 GrisoMG</p></body></html>'
iOSBEURL = ''

TestMode = True
TestBackuppath = expanduser("~") + "/Downloads/iOSForensic"
TestDatabase = expanduser("~") +"/test.sqlite"

PICEXTENSIONLIST = ["BMP", "GIF", "JPG", "JPEG", "PNG", "PBM", "PGM", "PPM", "TIFF", "XBM", "XPM"]
SQLITEEXTENSIONLIST = ["DB", "SQLITE", "SQLITEDB", "STOREDATA"]

IPHONE_VERSION6 = 6
IPHONE_VERSION7 = 7
IPHONE_VERSION8 = 8
IPHONE_UNSUPPORTED = 0

class AboutWindow(QtGui.QDialog):
    def __init__(self):
        super(AboutWindow, self).__init__(None)

        self.ui = Ui_AboutWindow()
        self.ui.setupUi(self)
        self.ui.about_version.setText("%s Ver. %s (%s)" % (iOSBEName, iOSBEVersion, iOSBEVersionDate))
        self.ui.about_copyright.setText(iOSBECC)
        self.ui.about_url.setText(iOSBEURL)

class iOSBE(QtGui.QMainWindow):
    def __init__(self):
        super(iOSBE, self).__init__(None)

        self.backuppath = None
        self.database = None
        self.cursor = None
        self.manifest = None
        self.infoplist = None
        self.iOSVersion = 0
        self.passwd = None
        self.work_dir = None
        self.extractpath = None
        self.is_active = False
        self.mbdb = None
        self.mru_list = list()
        self.threemaUI = None
        self.contactsUI = None
        self.sqlbrowserUI = None
        self.smsUI = None
        self.callhistoryUI = None
        self.whatsappUI = None

        if "linux" in sys.platform:
            self.mousewait = Qt.WaitCursor
        else:
            self.mousewait = QCursor(Qt.WaitCursor)

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        self.ui.treeViewDomains.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.treeViewDomains.customContextMenuRequested.connect(self.ctxMenu)

        self.ui.treeViewDomains.setHeaderLabel("")

        self.ui.treeViewDomains.setColumnWidth(0, 200)
        self.ui.treeViewDomains.setColumnWidth(2, 16)

        self.ui.treeViewDomains.setColumnHidden(1, True)
        self.ui.treeViewDomains.setColumnHidden(3, True)
        self.ui.treeViewDomains.setColumnHidden(4, True)
        self.ui.treeViewDomains.setColumnHidden(5, True)

        # action handlers
        QtCore.QObject.connect(self.ui.action_OpenBackup, QtCore.SIGNAL("triggered(bool)"), self.openBackupGUI)
        QtCore.QObject.connect(self.ui.action_About, QtCore.SIGNAL("triggered(bool)"), self.displayAbout)
        QtCore.QObject.connect(self.ui.action_CloseBackup, QtCore.SIGNAL("triggered(bool)"), self.closeBackup)

        QtCore.QObject.connect(self.ui.action_ExtractApp, QtCore.SIGNAL("triggered(bool)"), self.extractApp)
        QtCore.QObject.connect(self.ui.action_ExtractAll, QtCore.SIGNAL("triggered(bool)"), self.extractAll)

        QtCore.QObject.connect(self.ui.action_Contacts, QtCore.SIGNAL("triggered(bool)"), self.showContacts)
        QtCore.QObject.connect(self.ui.action_CallHistory, QtCore.SIGNAL("triggered(bool)"), self.showCallHistory)
        QtCore.QObject.connect(self.ui.action_Messages, QtCore.SIGNAL("triggered(bool)"), self.showMessages)
        QtCore.QObject.connect(self.ui.action_Threema, QtCore.SIGNAL("triggered(bool)"), self.showThreema)
        QtCore.QObject.connect(self.ui.action_WhatsApp, QtCore.SIGNAL("triggered(bool)"), self.showWhatsapp)

        self.work_dir = makeTmpDir()

        if sys.platform != "darwin":
            self.ui.separatorMRUList.setSeparator(True)
            self.mruLoadList()
            self.mruUpdateFileMenu()

    def closeEvent(self, event):
        #clean up and remove temporary files...
        rmTmpDir(self.work_dir)

    def ctxMenu(self, pos):

        # managing "standard" files
        selectedItem = self.ui.treeViewDomains.currentItem()
        if (selectedItem):
            pass
        else:
            return

        file = selectedItem.text(0).split(".")
        ftype = ""

        if file.__len__() != 2:
            return

        fext = file[1].encode('ascii','ignore').upper()

        for ext in PICEXTENSIONLIST:
            if fext == ext:
                ftype = "image"
                break

        if ftype == "":
            for ext in SQLITEEXTENSIONLIST:
                if fext == ext:
                    ftype = "sqlite"
                    break

        showMenu = False

        menu = QtGui.QMenu()

        # if image
        if (ftype == "image"):
            action1 = QtGui.QAction("Open with Image Viewer", self)
            action1.triggered.connect(self.openSelectedImage)
            menu.addAction(action1)
            showMenu = True


        # if sqlite
        if (ftype == "sqlite"):
            action1 = QtGui.QAction("Open with SQLite Browser", self)
            action1.triggered.connect(self.openSelectedSqlite)
            menu.addAction(action1)
            showMenu = True
        if (showMenu):
            menu.exec_(self.ui.treeViewDomains.mapToGlobal(pos))

    def isSubWindowOpen(self, win):
        # check if plugin already open
        found = False

    def isWindowOpen(self, win):
        #check if pid file of win is existing
        pass

    def showContacts(self):

        if self.isSubWindowOpen("contactsGUI") == True:
            return

        mbdomain_type = "HomeDomain"
        mbapp_name = "Library/AddressBook"

        if self.extractpath == None:
            dir = self.work_dir
        else:
            dir = self.extractpath

        self.cursor.execute("Select * from indice where mbdomain_type=? and mbfile_path= ?", (mbdomain_type,mbapp_name))
        records = self.cursor.fetchall()

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, dir)

        abook = dir + "/HomeDomain/Library/AddressBook/AddressBook.sqlitedb"
        abimg = dir + "/HomeDomain/Library/AddressBook/AddressBookImages.sqlitedb"
        self.contactsUI = contactsGUI(abook, abimg, self.work_dir)
        self.contactsUI.show()

    def showMessages(self):
        if self.isSubWindowOpen("smsGUI") == True:
            return

        if self.extractpath == None:
            dir = self.work_dir
        else:
            dir = self.extractpath


        mbdomain_type = "HomeDomain"
        mbapp_name = "Library/AddressBook"

        self.cursor.execute("Select * from indice where mbdomain_type=? and mbfile_path= ?", (mbdomain_type,mbapp_name))
        records = self.cursor.fetchall()

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, dir)

        mbdomain_type = "HomeDomain"
        mbapp_name = "Library/SMS"

        self.cursor.execute("Select * from indice where mbdomain_type=? and mbfile_path= ?", (mbdomain_type,mbapp_name))
        records = self.cursor.fetchall()

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, dir)


        abook = dir + "/HomeDomain/Library/AddressBook/AddressBook.sqlitedb"
        abimg = dir + "/HomeDomain/Library/AddressBook/AddressBookImages.sqlitedb"
        sms   = dir + "/HomeDomain/Library/SMS/sms.db"

        self.smsUI = smsGUI(sms, abook, abimg)
        self.smsUI.show()

    def showCallHistory(self):

        if self.extractpath == None:
            dir = self.work_dir
        else:
            dir = self.extractpath

        if self.iOSVersion == IPHONE_UNSUPPORTED:
            QtGui.QMessageBox.information(self, "Information", "Unsupported iOS version...")
            return

        if self.iOSVersion == IPHONE_VERSION6 or self.iOSVersion == IPHONE_VERSION7:
            mbdomain_type = "WirelessDomain"
            mbfile_name = "call_history.db"
        elif self.iOSVersion == IPHONE_VERSION8:
            mbdomain_type = "HomeDomain"
            mbfile_name = "CallHistory.storedata"

        self.cursor.execute("Select * from indice where mbdomain_type=? and mbfile_name= ?", (mbdomain_type,mbfile_name))
        records = self.cursor.fetchall()

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, dir)

        callhistorydb = dir + "/" + dbrecord.mbdomain_type + "/" + str(dbrecord.mbfile_path) + "/" + dbrecord.mbfile_name

        mbdomain_type = "HomeDomain"
        mbapp_name = "Library/AddressBook"

        self.cursor.execute("Select * from indice where mbdomain_type=? and mbfile_path= ?", (mbdomain_type,mbapp_name))
        records = self.cursor.fetchall()

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, dir)

        abook = dir + "/HomeDomain/Library/AddressBook/AddressBook.sqlitedb"
        abimg = dir + "/HomeDomain/Library/AddressBook/AddressBookImages.sqlitedb"

        self.callhistoryUI = callhistoryGUI(callhistorydb, abook)
        self.callhistoryUI.show()
        return

    def showThreema(self):
        if self.isSubWindowOpen("threemaGUI") == True:
            return

        mbdomain_type = "AppDomain"
        mbapp_name = "ch.threema.iapp"

        if self.extractpath == None:
            dir = self.work_dir
        else:
            dir = self.extractpath

        self.cursor.execute("Select * from indice where mbdomain_type=? and mbapp_name= ?", (mbdomain_type,mbapp_name))
        records = self.cursor.fetchall()

        if len(records) == 0:
            QtGui.QMessageBox.information(self, "Information", "Threema not found...")
            return

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, dir)

        threemaDB = dir + "/" + mbdomain_type + "/" + mbapp_name + "/Documents/ThreemaData.sqlite"

        self.threemaUI = threemaGUI(threemaDB, dir)
        self.threemaUI.show()

    def showWhatsapp(self):

        if self.iOSVersion == IPHONE_UNSUPPORTED:
            QtGui.QMessageBox.information(self, "Information", "Unsupported iOS version...")
            return
        if self.extractpath == None:
            dir = self.work_dir
        else:
            dir = self.extractpath

        self.cursor.execute("select * from indice where mbapp_name Like '%Whatsapp%' order by domain")
        records = self.cursor.fetchall()

        if len(records) == 0:
            QtGui.QMessageBox.information(self, "Information", "Whatsapp not found...")
            return

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, dir)

        path2appdomain = "AppDomain/net.whatsapp.WhatsApp"
        if self.iOSVersion == IPHONE_VERSION8:
            path2groupdomain = "AppDomainGroup/group.net.whatsapp.WhatsApp.shared"
        else:
            path2groupdomain = None

        self.whatsappUI = whatsappGUI(path2appdomain, path2groupdomain, self.work_dir)
        self.whatsappUI.show()
        return

    def onTreeClick(self):
        selectedItem = self.ui.treeViewDomains.currentItem()
        file = selectedItem.text(0).split(".")
        if file.__len__() == 2:
            for ext in PICEXTENSIONLIST:
                fext = file[1].encode('ascii','ignore')
                if fext.upper() == ext:
                    self.showPicture(selectedItem.text(4), selectedItem.text(0), ext)
                    break

    def openSelectedSqlite(self):
        selectedItem = self.ui.treeViewDomains.currentItem()
        self.showSQLite(selectedItem.text(4), selectedItem.text(0))

    def openSelectedImage(self):
        selectedItem = self.ui.treeViewDomains.currentItem()
        self.showPicture(selectedItem.text(4), selectedItem.text(0))

    def showSQLite(self, mbd, mbf):
        mbdomain_type = mbd
        mbfile_name = mbf

        if self.extractpath == None:
            dir = self.work_dir
        else:
            dir = self.extractpath

        self.cursor.execute("Select * from indice where mbdomain_type=? and mbfile_name= ?", (mbdomain_type,mbfile_name))
        records = self.cursor.fetchall()

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, dir)

        sqlitedb = dir + "/" + dbrecord.mbdomain_type + "/" + str(dbrecord.mbfile_path) + "/" + dbrecord.mbfile_name

        self.sqlbrowserUI = sqlBrowserGUI(sqlitedb, dir, dbrecord.mbfile_name)
        self.sqlbrowserUI.show()

    def showPicture(self, mbd, mbf):
        mbdomain_type = mbd
        mbfile_name = mbf

        self.cursor.execute("Select * from indice where mbdomain_type = ? and mbfile_name like ?", (mbdomain_type,mbfile_name))
        records = self.cursor.fetchall()

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            image_data = self.mbdb.readBackupFile(dbrecord)
        qimg = QtGui.QImage.fromData(image_data)
        qimg = qimg.scaled(800,600).scaled(400,300, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
        pixmap = QtGui.QPixmap.fromImage(qimg)
        self.w = ImageViewer(pixmap, self.ui.treeViewDomains)
        self.w.setWindowTitle(mbf)
        self.w.show()

    def informationMessage(self, message):
        QtGui.QMessageBox.information(self,
                                      "Information",
                                      message)

    def passwordDialog(self):
        passwd = None
        ok = False

        passwd, ok = QtGui.QInputDialog.getText(self, 'Backup seems to be encrypted. Password required...', 'Password:',
                                                QtGui.QLineEdit.Password)

        # passwd, ok = QtGui.QInputDialog.getText(None, "Backup ist encrypted. Password required...", 'Password', 'Enter password:', QtGui.QLineEdit.Password)

        if ok:
            return passwd
        else:
            return None

    def displayAbout(self):

        self.aboutDialog = AboutWindow()
        self.aboutDialog.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.aboutDialog.show()

    def getFilepathDialog(self, path=None):

        mobilesync = ""
        if path is not None:
            mobilesync = path
        elif sys.platform == "win32":
            mobilesync = os.environ["APPDATA"] + "/Apple Computer/MobileSync/Backup/"
        elif sys.platform == "darwin":
            mobilesync = os.environ["HOME"] + "/Library/Application Support/MobileSync/Backup/"
        else:
            if TestMode:
                mobilesync = TestBackuppath
            else:
                mobilesync = ""

        backuppath = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", mobilesync,
                                                            QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks);
        if (backuppath == None) or (len(backuppath) == 0):
            return None
        else:
            return backuppath

    def openBackupGUI(self):
        self.ui.statusbar.showMessage("Open iOS Backup...")

        if self.backuppath is None or self.backuppath is "":
            self.backuppath = self.getFilepathDialog()

        QApplication.setOverrideCursor(self.mousewait)

        if (self.backuppath == None) or (len(self.backuppath) == 0):
            self.ui.statusbar.showMessage("Stop...")
            QApplication.restoreOverrideCursor()
            return None


        if self.openBackup() is True:
            if sys.platform != "darwin":
                self.mruAddArchive(self.infoplist["Display Name"] + " (" + self.infoplist["Product Name"] + ")", self.backuppath)


        QApplication.restoreOverrideCursor()
        self.ui.statusbar.showMessage("Done...")

    def activateMenu(self, action):

        self.ui.action_OpenBackup.setEnabled(not action)
        self.ui.action_CloseBackup.setEnabled(action)
        self.ui.action_Contacts.setEnabled(action)
        self.ui.action_CallHistory.setEnabled(action)
        self.ui.action_Messages.setEnabled(action)
        self.ui.action_Threema.setEnabled(action)
        self.ui.action_WhatsApp.setEnabled(action)
        self.ui.action_ExtractApp.setEnabled(action)
        self.ui.action_ExtractAll.setEnabled(action)
        self.is_active = action

    def openBackup(self, path=None):

        if path is not None:
            self.backuppath = path

        self.manifest = readManifest(self.backuppath)
        if self.manifest is None:
            self.informationMessage("%s seems not to be a valid backup directory" % self.backuppath)
            self.ui.statusbar.showMessage("Stop...")
            return False
        else:
            # refresh gridLayoutManifest
            self.gridLayoutManifest_refresh(self.manifest)

        self.infoplist = readInfo(self.backuppath)
        if self.infoplist is None:
            self.informationMessage("Can't find Info.plist in directory %s.  Not a valid backup directory?" % self.backuppath)
            self.ui.statusbar.showMessage("Stop...")
            return False
        else:
            # refresh gridLayoutInfo
            self.gridLayoutInfo_refresh(self.infoplist)

        if not self.manifest.has_key("BackupKeyBag"):
            self.informationMessage("Only iOSBackup >= Version 5 Supported")

        if self.manifest["IsEncrypted"]:
            self.passwd = self.passwordDialog()

            if self.passwd is None:
                self.informationMessage("Password not given! Will not be able to extract information...")

        progressBar = QtGui.QProgressBar()
        self.ui.statusbar.addWidget(progressBar)
        self.mbdb = MBDB(self.backuppath)

        if self.passwd is not None:
            kb = Keybag.createWithBackupManifest(self.manifest, self.passwd)
            if not kb:
                self.informationMessage(
                    "Can not extract backup key.\nYou can only browse through the domains and apps...")
                # return False

            self.manifest["password"] = self.passwd

            self.mbdb.keybag = kb

        progressBar.setMaximum(self.mbdb.numoffiles)
        if TestMode is True:
            self.database, self.cursor = iOSBackupDB(TestDatabase)
        else:
            self.database, self.cursor = iOSBackupDB()

        store2db(self.cursor, self.mbdb)
        self.database.commit()

        self.ui.treeViewDomains.setHeaderLabel("Files/Domains/Apps")
        standardFiles = QtGui.QTreeWidgetItem(None)
        standardFiles.setText(0, "Standard files")
        self.ui.treeViewDomains.addTopLevelItem(standardFiles)

        for elementName in ['Manifest.plist', 'Info.plist', 'Status.plist']:
            newItem = QtGui.QTreeWidgetItem(standardFiles)
            newItem.setText(0, elementName)
            newItem.setText(1, "X")
            self.ui.treeViewDomains.addTopLevelItem(newItem)

        self.cursor.execute("SELECT DISTINCT(mbdomain_type) FROM indice")

        domain_types = self.cursor.fetchall()

        for domain_type_u in domain_types:
            domain_type = str(domain_type_u[0])

            newDomainFamily = QtGui.QTreeWidgetItem(None)
            newDomainFamily.setText(0, domain_type)

            self.ui.treeViewDomains.addTopLevelItem(newDomainFamily)

            # show new domain family in main view
            QtGui.QApplication.processEvents()

            query = "SELECT DISTINCT(mbapp_name) FROM indice WHERE mbdomain_type = ? ORDER BY mbdomain_type"
            self.cursor.execute(query, (domain_type,))
            domain_names = self.cursor.fetchall()

            for domain_name_u in domain_names:
                domain_name = str(domain_name_u[0])

                if (len(domain_names) > 1):
                    newDomain = QtGui.QTreeWidgetItem(newDomainFamily)
                    newDomain.setText(0, domain_name)
                    self.ui.treeViewDomains.addTopLevelItem(newDomain)

                    rootNode = newDomain
                else:
                    rootNode = newDomainFamily

                # query = "SELECT path, mbfile_path, mbfile_name, size, fileid, mbfile_type FROM indice WHERE mbdomain_type = ? AND mbapp_name = ? ORDER BY mbfile_path, mbfile_name"
                query = "SELECT mbfile_path, mbfile_name, size, id, mbfile_type FROM indice WHERE mbdomain_type = ? AND mbapp_name = ? ORDER BY mbfile_path, mbfile_name"

                self.cursor.execute(query, (domain_type, domain_name))
                nodes = self.cursor.fetchall()

                pathToNode = {'': rootNode}

                for nodeData in nodes:
                    path = str(nodeData[0])
                    # finding parent directory
                    lookup = path
                    missing = collections.deque()
                    dirNode = None
                    while dirNode is None:
                        dirNode = pathToNode.get(lookup, None)

                        if dirNode is None:
                            lookup, sep, component = lookup.rpartition('/')
                            missing.appendleft(component)

                    # creating parent directory if neccesary
                    for component in missing:
                        newPath = QtGui.QTreeWidgetItem(dirNode)
                        newPath.setText(0, component)
                        newPath.setToolTip(0, component)
                        self.ui.treeViewDomains.addTopLevelItem(newPath)

                        dirNode = newPath
                        #lookup = posixpath.join(lookup, component)
                        lookup = path
                        pathToNode[lookup] = newPath
                    try:
                        file_name = str(nodeData[1].encode("utf-8"))
                    except:
                        file_name = nodeData[1]

                    if (nodeData[2]) < 1024:
                        file_dim = str(nodeData[2]) + " b"
                    else:
                        file_dim = str(nodeData[2] / 1024) + " kb"
                    file_id = int(nodeData[3])
                    file_type = str(nodeData[4])

                    if file_type == 'd':
                        newFile = dirNode
                    else:
                        newFile = QtGui.QTreeWidgetItem(newPath)
                        self.ui.treeViewDomains.addTopLevelItem(newFile)

                        newFile.setText(0, file_name)
                        newFile.setToolTip(0, file_name)
                        newFile.setText(2, str(file_dim))

                    newFile.setText(1, file_type)
                    newFile.setText(3, str(file_id))
                    newFile.setText(4, domain_type)
                    newFile.setText(5, domain_name)

        rawFiles = QtGui.QTreeWidgetItem(None)
        rawFiles.setText(0, "Raw files")
        self.ui.treeViewDomains.addTopLevelItem(rawFiles)
        # query = "SELECT mbfile_path, mbfile_name, size, id, mbfile_type FROM indice ORDER BY mbfile_path, mbfile_name"

        query = "SELECT domain, path, size, id, mbfile_type FROM indice ORDER BY domain, path"

        self.cursor.execute(query)
        nodes = self.cursor.fetchall()
        for nodeData in nodes:
            domain_name = str(nodeData[0]).replace("-", "/", 1) + "/" + str(nodeData[1])
            newFile = QtGui.QTreeWidgetItem(rawFiles)
            self.ui.treeViewDomains.addTopLevelItem(newFile)

            if (nodeData[2]) < 1024:
                file_dim = str(nodeData[2]) + " b"
            else:
                file_dim = str(nodeData[2] / 1024) + " kb"
            file_id = int(nodeData[3])
            file_type = str(nodeData[4])
            newFile.setText(0, domain_name)
            newFile.setToolTip(0, domain_name)
            newFile.setText(2, str(file_dim))
            newFile.setText(1, file_type)
            newFile.setText(3, str(file_id))

        self.ui.statusbar.removeWidget(progressBar)
        self.activateMenu(True)
        return True

    def closeBackup(self):
        self.ui.statusbar.showMessage("Close Backup %s..." %self.backuppath)
        self.activateMenu(False)
        self.gridLayoutInfo_refresh()
        self.gridLayoutManifest_refresh()
        self.ui.treeViewDomains.clear()
        self.backuppath = None
        self.database = None
        self.cursor = None
        self.manifest = None
        self.infoplist = None
        self.passwd = None
        self.extractpath = None
        self.ui.statusbar.showMessage("Done...")

    def extractApp(self):

        if self.is_active == False:
            return

        selectedItem = self.ui.treeViewDomains.currentItem()


        if self.backuppath is None:
            msg = "No iOS Backup open..."
            self.informationMessage(msg)
            return

        if (self.extractpath == None) or (len(self.extractpath) == 0):
            self.extractpath = self.getFilepathDialog(self.backuppath)

            if (self.extractpath == None) or (len(self.extractpath) == 0):
                return None

        if selectedItem.text(4) == "AppDomain":
            search = '%' + selectedItem.text(0) + '%'
            self.cursor.execute("Select * from indice where mbapp_name like ?", (search,))
        else:
            search = '%' + selectedItem.text(0) + '%'
            self.cursor.execute("Select * from indice where mbdomain_type = ? and mbfile_path like ?", (selectedItem.text(4),search))
        records = self.cursor.fetchall()

        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, self.extractpath)

    def extractAll(self):
        if self.is_active == False:
            return
        if self.backuppath is None:
            msg = "No iOS Backup open..."
            self.informationMessage(msg)
            return

        if (self.extractpath == None) or (len(self.extractpath) == 0):
            self.extractpath = self.getFilepathDialog(self.backuppath)

            if (self.extractpath == None) or (len(self.extractpath) == 0):
                return None

#        msg = "Will extract App %s to path %s" % (selectedItem.text(0), self.extractpath)
#        self.informationMessage(msg)

        self.cursor.execute("Select * from indice")
        records = self.cursor.fetchall()
        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            self.mbdb.extract_backup_from_db(dbrecord, self.extractpath)

    def gridLayoutInfo_refresh(self, showinfo=None):
        mydict = {"Build Version": self.ui.lblBuildVersion,
                  "Device Name": self.ui.lblDeviceName,
                  "Display Name": self.ui.lblDisplayName,
                  "GUID": self.ui.lblGUID,
                  "ICCID": self.ui.lblICCID,
                  "IMEI": self.ui.lblIMEI,
                  "MEID": self.ui.lblMEID,
                  "Phone Number": self.ui.lblPhoneNumber,
                  "Product Name": self.ui.lblProductName,
                  "Product Type": self.ui.lblProductType,
                  "Product Version": self.ui.lblProductVersion,
                  "Serial Number": self.ui.lblSerialNumber,
                  "Target Identifier": self.ui.lblTargetIdentifier,
                  "Target Type": self.ui.lblTargetType,
                  "Unique Identifier": self.ui.lblUniqueIdentifier,
                  "iTunes Version": self.ui.lbliTunesVersion
                  }

        for i in mydict:
            if showinfo is not None:
                value = unicode(showinfo.get(i, "missing"))
                if i == 'Product Version':
                    self.iOSVersion = self.getIOSVersion(value)
            else:
                value = ''
            try:
                mydict[i].setText(value)
            except:
                pass

    def getIOSVersion(self, version):
        try:
            return int(version.split('.')[0])
        except:
            return 0

    def gridLayoutManifest_refresh(self, showinfo=None):
        mydict = {"Date": self.ui.lblDate,
                  "IsEncrypted": self.ui.lblIsEncrypted,
                  "SystemDomainsVersion": self.ui.lblSystemDomainsVersion,
                  "Version": self.ui.lblVersion,
                  "WasPasscodeSet": self.ui.lblWasPasscodeSet,
                  "BackupKeyBag": self.ui.lblHasBackupKeybag
                  }

        for i in mydict:
            if showinfo is not None:
                value = unicode(showinfo.get(i, "missing"))
                if i == "BackupKeyBag":
                    value = showinfo.has_key("BackupKeyBag")
            else:
                value = ''
            try:
                mydict[i].setText(value)
            except:
                pass

    def mruAddArchive(self, description, path):
        """
		Update the list of Most Recently Used archives, with a newly opened archive.

		description = The "Display name" of the open archive (e.g. "MyPhone (iPhone3)")
		path = The filesystem path of the archive.

		The function updates the MRU list,
		the application settings file, and the "File" Menu.
		"""

        # Remove the path, if it already exists
        tmp = filter(lambda x: x[0] == path, self.mru_list)
        if len(tmp) > 0:
            self.mru_list.remove(tmp[0])

        # Add the new archive, to the beginning of the list
        self.mru_list.insert(0, ( path, description ))

        self.mruSaveList()
        self.mruUpdateFileMenu()

    def mruSaveList(self):
        """
		Saves the list of MRU files to the application settings file.
		"""
        qs = QSettings()

        qs.remove("mru")
        qs.beginWriteArray("mru")
        for i, m in enumerate(self.mru_list):
            (path, description) = m
            qs.setArrayIndex(i)
            qs.setValue("path", path)
            qs.setValue("description", description)
        qs.endArray()

    def mruLoadList(self):
        """
		Loads the list of MRU files from the pplication settings file.
		"""
        self.mru_list = list()
        qs = QSettings()

        count = qs.beginReadArray("mru")
        for i in range(count):
            qs.setArrayIndex(i)
            path = qs.value("path")
            description = qs.value("description")
            if os.path.exists(path):
                self.mru_list.append((path, description))
        qs.endArray()

    def mruUpdateFileMenu(self):
        items = self.ui.menuReopen.actions()
        found_separator = False
        for i, item in enumerate(items):
            if found_separator:
                self.ui.menuReopen.removeAction(item)
            if (not found_separator) and item == self.ui.separatorMRUList:
                found_separator = True

        # Re-create MRU list
        # (Menu item for each MRU item)
        self.ui.separatorMRUList.setVisible(len(self.mru_list) != 0)

        for i, m in enumerate(self.mru_list):
            (path, description) = m

            text = "%d %s" % (i + 1, description)
            if i < 9:
                text = '&' + text

            action = self.ui.menuReopen.addAction(text)
            action.triggered.connect(lambda p=path: self.openBackup(path))

class ImageViewer(QtGui.QDialog):
    def __init__(self, image, parent):
        QtGui.QDialog.__init__(self, parent)
        self.picture = image
        #self.picture.scaled(0, 80, QtCore.Qt.KeepAspectRatio)
        self.resize(self.picture.size())

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.picture)

if __name__ == "__main__":

    print(__import__("sys").version)
    PYTHONVERSION, = __import__("sys").version_info[:1]

    iApp = QtGui.QApplication(sys.argv)
    iApp.setOrganizationName("iOSBE")
    iApp.setOrganizationDomain("iOSBackupExaminer.com")
    iApp.setApplicationName("iOSBackupExaminer")
    main_iOSBE_window = iOSBE()
    main_iOSBE_window.show()

    if PYTHONVERSION != 2:
        QtGui.QMessageBox.information(main_iOSBE_window, "Information", "Unsupported python version %s..." %__import__("sys").version)
        exit(-1)
    else:
        sys.exit(iApp.exec_())
