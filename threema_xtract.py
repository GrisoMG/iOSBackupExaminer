# -*- coding: utf-8 -*-
'''
Thremma Xtract 1.0
- Threema Backup Messages Extractor for iPhone (not Android)

Released on MMM DD YYYY
Last Update MMM DD YYYY ()


Tested with ThreemaApp (iPhone)  

Changelog:

V1.0 (created by  - MMM DD, YYY)
- first release, iPhone only:
- sortable js allows table sorting to make chat sessions easily readable

Usage:

For iPhone DB: 
> python threema_xtract.py -i ThreemaData.sqlite


(C)opyright 2015    GrisoMG
'''



import sys, re, os, string, datetime, time, sqlite3, glob, webbrowser, base64, subprocess, tempfile, shutil, struct
from os.path import expanduser
from argparse import ArgumentParser
from PySide import QtCore, QtGui
from PySide.phonon import Phonon
from iOSForensicClasses import ThreemaChatsession, ThreemaMessage, ThreemaContact, makeTmpDir, rmTmpDir
from gui.threema_form import Ui_frmThreema


SCALEFACTOR = 0.5

class threemaGUI(QtGui.QMainWindow):
    def __init__(self, threemaDB=None, path=None):
        QtGui.QMainWindow.__init__(self)

        self.threemaDB = threemaDB
        self.path = path
        self.tmpdir = ""
        self.contact_list = []
        self.chat_session_list = []
        self.audio_playing = False
        self.video_playing = False

        self.ui = Ui_frmThreema()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        QtCore.QObject.connect(self.ui.tableWidgetChats, QtCore.SIGNAL("itemSelectionChanged()"), self.onTreeClick)
        QtCore.QObject.connect(self.ui.actionReport, QtCore.SIGNAL("triggered(bool)"), self.printReport)
        QtCore.QObject.connect(self.ui.actionExtract, QtCore.SIGNAL("triggered(bool)"), self.extractApp)

        self.ui.tableWidgetContacts.setColumnCount(9)
        #self.ui.tableWidgetContacts.setSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        self.ui.tableWidgetChats.setColumnCount(7)
        self.ui.tableWidgetMessages.setColumnCount(9)

        self.readThreemaDB()
        if self.contact_list is not None:
            self.tableContacts()
        if self.chat_session_list is not None:
            self.tableChatSessions()

    def closeEvent(self, event):
        #clean up and remove temporary files...
        #rmTmpDir(self.path)
        rmTmpDir(self.tmpdir)

    def tableContacts(self):

        self.ui.tableWidgetContacts.setHorizontalHeaderLabels(("PK;Lastname;Firstname;Nickname;ID;Status;#Msgs;Last Msg;Picture").split(";"))

        row = 0
        self.ui.tableWidgetContacts.setRowCount(self.contact_list.__len__())
        for contact in self.contact_list:
            newItem0 = QtGui.QTableWidgetItem()
            newItem0.setText(str(contact.zpk))
            self.ui.tableWidgetContacts.setItem(row,0, newItem0)
            newItem1 = QtGui.QTableWidgetItem()
            newItem1.setText(contact.lastname)
            self.ui.tableWidgetContacts.setItem(row,1, newItem1)
            newItem2 = QtGui.QTableWidgetItem()
            newItem2.setText(contact.firstname)
            self.ui.tableWidgetContacts.setItem(row,2, newItem2)
            newItem3 = QtGui.QTableWidgetItem()
            newItem3.setText(contact.nickname)
            self.ui.tableWidgetContacts.setItem(row,3, newItem3)
            newItem4 = QtGui.QTableWidgetItem()
            newItem4.setText(str(contact.identity))
            self.ui.tableWidgetContacts.setItem(row,4, newItem4)
            if contact.verificationlevel == 0:
                image0 = ImageWidget("data/img/verification_red.png", self.ui.tableWidgetContacts)
                self.ui.tableWidgetContacts.setCellWidget(row, 5, image0)
            elif contact.verificationlevel == 1:
                image0 = ImageWidget("data/img/verification_orange.png", self.ui.tableWidgetContacts)
                self.ui.tableWidgetContacts.setCellWidget(row, 5, image0)
            elif contact.verificationlevel == 2:
                image0 = ImageWidget("data/img/verification_green.png", self.ui.tableWidgetContacts)
                self.ui.tableWidgetContacts.setCellWidget(row, 5, image0)
            else:
                newItem5 = QtGui.QTableWidgetItem()
                newItem5.setText(str(contact.verificationlevel))
                self.ui.tableWidgetContacts.setItem(row,5, newItem5)
            newItem6 = QtGui.QTableWidgetItem()
            newItem6.setText(str(contact.numberofmessages))
            self.ui.tableWidgetContacts.setItem(row,6, newItem6)
            newItem7 = QtGui.QTableWidgetItem()
            newItem7.setText(str(contact.last_message_date))
            self.ui.tableWidgetContacts.setItem(row,7, newItem7)
            if contact.has_image == True:
                image1 = ImageWidget(contact.imageurl, self.ui.tableWidgetContacts, SCALEFACTOR)
                image1.setStatusTip(contact.imageurl)
                image1.setToolTip(contact.imageurl)
                self.ui.tableWidgetContacts.setColumnWidth(8, image1.picture.width())
                self.ui.tableWidgetContacts.setRowHeight(row, image1.picture.height())
                self.ui.tableWidgetContacts.setCellWidget(row, 8, image1)
            row += 1

        self.ui.tableWidgetContacts.setMouseTracking(True)
        self.ui.tableWidgetContacts.cellClicked.connect(self.cellHoverContacts)

        self.ui.tableWidgetMessages.setMouseTracking(True)
        self.ui.tableWidgetMessages.cellClicked.connect(self.cellHoverMessages)

    def cellHoverContacts(self, row, column):
        item = self.ui.tableWidgetContacts.cellWidget(row, column)

        if column == 8 and item is not None:
            self.w = ImageViewer(item.toolTip(), self.ui.tableWidgetContacts)
            self.w.setWindowTitle(item.toolTip())
            self.w.show()

    def cellHoverMessages(self, row, column):
        item = self.ui.tableWidgetMessages.cellWidget(row, column)

        if column == 7 and item is not None:
            if item.toolTip() == "" or item.toolTip() is None:
                return
            #split tooltip
            tooltip = item.toolTip().split(":")

            if tooltip[0] == "Image":
                self.w = ImageViewer(tooltip[1], self.ui.tableWidgetMessages)
                self.w.setWindowTitle(tooltip[1])
                self.w.show()
            elif tooltip[0] == "Audio":
                if self.audio_playing == True:
                    self.audio_obj.stop()
                    self.audio_playing = False
                else:
                    self.audio_m = Phonon.MediaSource(tooltip[1])
                    self.audio_obj = Phonon.createPlayer(Phonon.MusicCategory, self.audio_m)
                    self.audio_obj.play()
                    self.audio_playing = True
            elif tooltip[0] == "Video":
                try:
                    self.videoplayer = Phonon.VideoPlayer()
                    self.videoplayer.load(Phonon.MediaSource(tooltip[1]))
                    self.videoplayer.play()
                    self.videoplayer.show()
                    self.video_playing = True
                except:
                    print("Error")

    def tableChatSessions(self):
        self.ui.tableWidgetChats.setHorizontalHeaderLabels(("PK;Contact;ID;Status;#Msgs;#Unread;Last Msg").split(";"))

        row = 0
        self.ui.tableWidgetChats.setRowCount(self.chat_session_list.__len__())
        for chat in self.chat_session_list:
            newItem0 = QtGui.QTableWidgetItem()
            newItem0.setText(str(chat.zpk))
            self.ui.tableWidgetChats.setItem(row,0, newItem0)

            newItem1 = QtGui.QTableWidgetItem()
            if chat.group_id == "" or chat.group_id is None:
                name = chat.contact_name
            else:
                name = " (Group) " + chat.group_name
            newItem1.setText(name)
            self.ui.tableWidgetChats.setItem(row,1, newItem1)

            newItem2 = QtGui.QTableWidgetItem()
            newItem2.setText(str(chat.identity))
            self.ui.tableWidgetChats.setItem(row,2, newItem2)

            if chat.contact_status == 0:
                newItem3 = ImageWidget("data/img/verification_red.png", self.ui.tableWidgetContacts)
                self.ui.tableWidgetChats.setCellWidget(row, 3, newItem3)
            elif chat.contact_status == 1:
                newItem3 = ImageWidget("data/img/verification_orange.png", self.ui.tableWidgetContacts)
                self.ui.tableWidgetChats.setCellWidget(row, 3, newItem3)
            elif chat.contact_status == 2:
                newItem3 = ImageWidget("data/img/verification_green.png", self.ui.tableWidgetContacts)
                self.ui.tableWidgetChats.setCellWidget(row, 3, newItem3)
            else:
                newItem3 = QtGui.QTableWidgetItem()
                newItem3.setText(str(chat.contact_status))
                self.ui.tableWidgetChats.setItem(row,3, newItem3)

            newItem4 = QtGui.QTableWidgetItem()
            newItem4.setText(str(chat.msg_count))
            self.ui.tableWidgetChats.setItem(row,4, newItem4)

            newItem5 = QtGui.QTableWidgetItem()
            newItem5.setText(str(chat.contact_unread_msg))
            self.ui.tableWidgetChats.setItem(row,5, newItem5)

            newItem6 = QtGui.QTableWidgetItem()
            newItem6.setText(str(chat.last_message_date ))
            self.ui.tableWidgetChats.setItem(row,6, newItem6)

            row += 1

        self.ui.tableWidgetChats.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.ui.tableWidgetChats.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.ui.tableWidgetChats.resizeColumnsToContents()
        self.ui.tableWidgetChats.resizeRowsToContents()

    def readThreemaDB(self):
        # connects to the database(s)

        self.tmpdir = makeTmpDir()

        msgstore = sqlite3.connect(self.threemaDB)
        msgstore.row_factory = sqlite3.Row
        c1 = msgstore.cursor()
        c2 = msgstore.cursor()

        self.contact_list = getContacts(c1, c2, self.tmpdir)
        self.chat_session_list = getChatSessions(c1)
        threemadir = self.path + "/AppDomain/ch.threema.iapp/Documents"
        self.chat_session_list = getChatMessages(c1, self.chat_session_list, self.tmpdir, threemadir)

    def onTreeClick(self):

        self.ui.tableWidgetMessages.clear()
        self.ui.tableWidgetMessages.setHorizontalHeaderLabels(("PK;Chat;Msg Date;Delivery Date;Read Date;Status;From;Content;Type").split(";"))

        selectedItem = self.ui.tableWidgetChats.selectedItems()
        try:
            chat = self.getChat(selectedItem[0].text())
        except:
            return

        if chat is None:
            return

        if chat.msg_list.__len__() == 0:
            return
        else:
            self.ui.tableWidgetMessages.setRowCount(chat.msg_list.__len__())

        row = 0
        for msg in chat.msg_list:
            if msg.contact_from == "me":
                rowcolour = QtGui.QColor(153,255,153)
            else:
                rowcolour = QtGui.QColor(192,192,192)

            newItem0 = QtGui.QTableWidgetItem()
            newItem0.setText(str(msg.zpk))
            newItem0.setBackground(rowcolour)
            self.ui.tableWidgetMessages.setItem(row,0, newItem0)

            newItem1 = QtGui.QTableWidgetItem()
            if chat.group_id == "" or chat.group_id is None:
                name = chat.contact_name
            else:
                name = " (Group) " + chat.group_name
            newItem1.setText(name)
            newItem1.setBackground(rowcolour)
            self.ui.tableWidgetMessages.setItem(row,1, newItem1)

            newItem2 = QtGui.QTableWidgetItem()
            newItem2.setText(str(msg.msg_date))
            newItem2.setBackground(rowcolour)
            self.ui.tableWidgetMessages.setItem(row,2, newItem2)

            newItem3 = QtGui.QTableWidgetItem()
            newItem3.setText(str(msg.delivery_date))
            newItem3.setBackground(rowcolour)
            self.ui.tableWidgetMessages.setItem(row,3, newItem3)

            newItem4 = QtGui.QTableWidgetItem()
            newItem4.setText(str(msg.read_date))
            newItem4.setBackground(rowcolour)
            self.ui.tableWidgetMessages.setItem(row,4, newItem4)

            newItem5 = QtGui.QTableWidgetItem()
            newItem5.setText(str(msg.status))
            newItem5.setBackground(rowcolour)
            self.ui.tableWidgetMessages.setItem(row,5, newItem5)


            newItem6 = QtGui.QTableWidgetItem()
            if chat.group_id != "":
                newItem6.setText(msg.contact_from)
            elif msg.contact_from == "me":
                newItem6.setText(msg.contact_from)
            else:
                newItem6.setText(chat.contact_name)
            newItem6.setBackground(rowcolour)
            self.ui.tableWidgetMessages.setItem(row,6, newItem6)

            if msg.media_wa_type == "Text":
                newItem7 = QtGui.QTableWidgetItem()
                newItem7.setText(msg.msg_text)
                newItem7.setBackground(rowcolour)
                self.ui.tableWidgetMessages.setItem(row,7, newItem7)
            elif msg.media_wa_type == "Image":
                image1 = ImageWidget(msg.image_url, self.ui.tableWidgetMessages, SCALEFACTOR)
                image1.setStatusTip(msg.image_url)
                image1.setToolTip("Image:" + msg.image_url)
                self.ui.tableWidgetMessages.setColumnWidth(7, image1.picture.width())
                self.ui.tableWidgetMessages.setRowHeight(row, image1.picture.height())
                self.ui.tableWidgetMessages.setCellWidget(row, 7, image1)
            elif msg.media_wa_type == "Audio":
                image1 = ImageWidget("data/img/audio.png", self.ui.tableWidgetMessages, 1.8)
                image1.setStatusTip(msg.audio_url)
                image1.setToolTip("Audio:" + msg.audio_url)
                self.ui.tableWidgetMessages.setCellWidget(row, 7, image1)
            elif msg.media_wa_type == "Video":
                image1 = ImageWidget("data/img/video.png", self.ui.tableWidgetMessages, 1.8)
                image1.setStatusTip(msg.video_url)
                image1.setToolTip("Video:" + msg.video_url)
                self.ui.tableWidgetMessages.setCellWidget(row, 7, image1)

            newItem8 = QtGui.QTableWidgetItem()
            newItem8.setText(str(msg.media_wa_type))
            newItem8.setBackground(rowcolour)
            self.ui.tableWidgetMessages.setItem(row,8, newItem8)

            row += 1

        self.ui.tableWidgetMessages.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.ui.tableWidgetMessages.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.ui.tableWidgetMessages.setVisible(False)
        #self.ui.tableWidgetMessages.resizeColumnsToContents()
        #self.ui.tableWidgetMessages.resizeRowsToContents()
        self.ui.tableWidgetMessages.setVisible(True)

    def getChat(self, zpk):
        for chat in self.chat_session_list:
            if str(chat.zpk) == str(zpk):
                return chat
        return None

    def extractApp(self):
        mbdomain_type = "AppDomain"
        mbapp_name = "ch.threema.iapp"

        outdir = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", "",
                                                            QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks)

        if (outdir == None) or (len(outdir) == 0):
            return None

        src = self.path + "/" + mbdomain_type + "/" + mbapp_name
        outdir = outdir + "/" + mbdomain_type + "/" + mbapp_name

        shutil.copytree(src, outdir)

    def printReport(self):

        path = expanduser("~")
        outdir = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", path,
                                                            QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks)

        if (outdir == None) or (len(outdir) == 0):
            return None

        outfile = outdir + "/Threema-Report"
        printHTMLReport(outfile, self.contact_list, self.chat_session_list)

class ImageWidget(QtGui.QWidget):

    def __init__(self, imagePath, parent, factor=None):
        super(ImageWidget, self).__init__(parent)
        img = QtGui.QImage(imagePath)
        if factor == None:
            self.picture = QtGui.QPixmap(img)
        else:
            imgsize = img.size()
            w = int(imgsize.width()*factor)
            h = int(imgsize.height()*factor)
            self.picture = QtGui.QPixmap(img.scaled(w,h))

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.picture)

class ImageViewer(QtGui.QDialog):
    def __init__(self, imagePath, parent):
        QtGui.QDialog.__init__(self, parent)
        self.picture = QtGui.QPixmap(imagePath)
        self.picture.scaled(0, 0, QtCore.Qt.KeepAspectRatio)
        self.resize(self.picture.size())

    def paintEvent(self, e):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.picture)

################################################################################
# Smileys conversion function
def convertsmileys (text):
    global PYTHON_VERSION
    if PYTHON_VERSION == 2:
        newtext = convert_smileys_python_2.convertsmileys_python2 (text)
    elif PYTHON_VERSION == 3:
        newtext = convert_smileys_python_2.convertsmileys_python3 (text)
    return newtext

################################################################################
#Functions for Find Offline File

def filelistonce (folder, date):
    flistnames = glob.glob( os.path.join(folder, '*'+date+'*') )
    flistsizes = []
    for i in range(len(flistnames)):
        statinfo = os.stat(flistnames[i])
        fsize = statinfo.st_size
        flistsizes.append(fsize)
    flist = [flistnames, flistsizes]
    return flist

def filelist (type, date):
    folder = None
    flist = None
    if type == 'IMG':
        folder = 'Media/Images/'
        if not date in flistimg:
            flistimg[date] = filelistonce (folder, date)
        flist = flistimg[date]
    elif type == 'AUD':
        folder = 'Media/Audio/'
        if not date in flistaud:
            flistaud[date] = filelistonce (folder, date)
        flist = flistaud[date]
    elif type == 'VID':
        folder = 'Media/Video/'
        if not date in flistvid:
            flistvid[date] = filelistonce (folder, date)
        flist = flistvid[date]
    return folder, flist

def findfile (type, size, localurl, date, additionaldays):
    fname = ''
        #folder = 'Media/'
        #if os.path.exists(localurl):
        #    fname = localurl
        #else:
        #    fname = folder
    fname = localurl
    
    #return the file name
    return fname

def writeMedia (tmpdir, imgid, media, ext):
  destname = tmpdir + "/" + str(imgid) + "." + ext

  try:
    with open(destname, 'wb') as output_file:
      output_file.write(media)
  except:
    destname = ""
        
  return destname

def getMediaURL (threemadir, tmpdir, imgid, image, ext):
    srcpath = threemadir + "/.ThreemaData_SUPPORT/_EXTERNAL_DATA/"
    sourcename = srcpath + str(image)
    destname = tmpdir + "/" + str(imgid) + "." + ext
    
    with open(sourcename, 'rb') as input_file:
        ablob = input_file.read()
    with open(destname, 'wb') as output_file:
        output_file.write(ablob)

    return destname

def printHTMLReport(outfile, contact_list, chat_session_list):

    owner = "Threema-Report"


    outfile = '%s.html' % outfile
    wfile = open(outfile,'wb')
    print ("printing output to "+outfile+" ...")
    # writes page header
    wfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n'.encode('utf-8'))
    wfile.write('"http://www.w3.org/TR/html4/loose.dtd">\n'.encode('utf-8'))
    wfile.write('<html><head><title>{}</title>\n'.format(outfile).encode('utf-8'))
    wfile.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n'.encode('utf-8'))
    wfile.write('<meta name="GENERATOR" content="Threema Xtract v2.0"/>\n'.encode('utf-8'))
    # adds page style
    wfile.write(css_style.encode('utf-8'))

    # adds javascript to make the tables sortable
    wfile.write('\n<script type="text/javascript">\n'.encode('utf-8'))
    wfile.write(popups.encode('utf-8'))
    wfile.write(sortable.encode('utf-8'))
    wfile.write('</script>\n\n'.encode('utf-8'))
    wfile.write('</head><body>\n'.encode('utf-8'))

    # H1 Title
    wfile.write('<h1>iOS Forensic<h1>'.encode('utf-8'))

    # H2 DB Owner
    wfile.write('<a name="top"></a><h2>'.encode('utf-8'))
    wfile.write('Threema '.encode('utf-8'))
    wfile.write('<img src="data/img/threema.jpg" alt="" '.encode('utf-8'))
    wfile.write('style="width:40px;height:40px;vertical-align:middle"/>'.encode('utf-8'))
    wfile.write('Xtract &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'.encode('utf-8'))
    wfile.write('<img src="data/img/apple.png" alt="" '.encode('utf-8'))

    wfile.write('style="width:35px;height:35px;"/>'.encode('utf-8'))
    wfile.write('&nbsp;{}</h2>\n'.format(owner).encode('utf-8'))

    # writes table header "Threema Contacts"
    wfile.write('<h3>Threema Contacts</h3>\n'.encode('utf-8'))
    wfile.write('<table class="sortable" id="contactlist" border="1" cellpadding="2" cellspacing="0">\n'.encode('utf-8'))
    wfile.write('<thead>\n'.encode('utf-8'))
    wfile.write('<tr>\n'.encode('utf-8'))
    wfile.write('<th>PK</th>\n'.encode('utf-8'))
    wfile.write('<th>Lastname</th>\n'.encode('utf-8'))
    wfile.write('<th>Firstname</th>\n'.encode('utf-8'))
    wfile.write('<th>Nickname</th>\n'.encode('utf-8'))
    wfile.write('<th>Contact ID</th>\n'.encode('utf-8'))
    wfile.write('<th>Status</th>\n'.encode('utf-8'))
    wfile.write('<th>Conversation ID</th>\n'.encode('utf-8'))
    wfile.write('<th>NumOfMsgs</th>\n'.encode('utf-8'))
    wfile.write('<th>Last Msg Date</th>\n'.encode('utf-8'))
    wfile.write('<th>Picture</th>\n'.encode('utf-8'))
    wfile.write('</tr>\n'.encode('utf-8'))
    wfile.write('</thead>\n'.encode('utf-8'))

    # writes contact list table content
    wfile.write('<tbody>\n'.encode('utf-8'))
    for i in contact_list:
        wfile.write('<tr>\n'.encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.zpk).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.lastname).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.firstname).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.nickname).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.identity).encode('utf-8'))

        if i.verificationlevel == 2:
            wfile.write('<td ><img src="data/img/verification_green.png" alt="2"> </td>'.encode('utf-8'))
        elif i.verificationlevel == 1:
            wfile.write('<td ><img src="data/img/verification_orange.png" alt="1"> </td>'.encode('utf-8'))
        elif i.verificationlevel == 0:
            wfile.write('<td ><img src="data/img/verification_red.png" alt="0"> </td>'.encode('utf-8'))
        else:
             wfile.write('<td>{}</td>\n'.format(contactstatus).encode('utf-8'))

        wfile.write('<td>{}</td>\n'.format(i.conversation_id).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.numberofmessages).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.last_message_date).encode('utf-8'))

        if i.has_image == True:
            wfile.write('<td ><a onclick="image(this.href);return(false);" target="image" href="{}"><img src="{}" width="20%" height="20%" alt="Image"/></a>&nbsp;|&nbsp;<a onclick="image(this.href);return(false);" target="image" href="{}">Image</a>'.format(i.imageurl, i.imageurl,i.imageurl).encode('utf-8'))
        else:
            wfile.write('<td > </td>'.encode('utf-8'))
    wfile.write('</tbody>\n'.encode('utf-8'))
    # writes contact list table footer
    wfile.write('</table>\n\n'.encode('utf-8'))


    # writes table header "CHAT SESSION"
    wfile.write('<h3>Threema Chat Sessions</h3>\n'.encode('utf-8'))

    wfile.write('<table class="sortable" id="chatsession" border="1" cellpadding="2" cellspacing="0">\n'.encode('utf-8'))
    wfile.write('<thead>\n'.encode('utf-8'))
    wfile.write('<tr>\n'.encode('utf-8'))
    wfile.write('<th>PK</th>\n'.encode('utf-8'))
    wfile.write('<th>Contact Name</th>\n'.encode('utf-8'))
    wfile.write('<th>Contact ID</th>\n'.encode('utf-8'))
    wfile.write('<th>Status</th>\n'.encode('utf-8'))
    wfile.write('<th># Msg</th>\n'.encode('utf-8'))
    wfile.write('<th># Unread Msg</th>\n'.encode('utf-8'))
    wfile.write('<th>Last Message</th>\n'.encode('utf-8'))
    wfile.write('</tr>\n'.encode('utf-8'))
    wfile.write('</thead>\n'.encode('utf-8'))

    # writes chat session table content
    wfile.write('<tbody>\n'.encode('utf-8'))
    for i in chat_session_list:
        if i.contact_name == "N/A" or i.contact_name == "" or i.contact_name is None:
            try:
                i.contact_name = i.contact_id.split('@')[0]
            except:
                i.contact_name = i.contact_id
            contactname = i.contact_name
        else:
            contactname = convertsmileys ( i.contact_name ) # chat name

        contactstatus = convertsmileys ( str(i.contact_status) )

        lastmessagedate = i.last_message_date
        wfile.write('<tr>\n'.encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.zpk).encode('utf-8'))
        if i.group_id == "" or i.group_id is None:
            wfile.write('<td class="contact"><a href="#{}">{}</a></td>\n'.format(i.contact_name,contactname + " (" + i.identity + ")").encode('utf-8'))
        else:
            wfile.write('<td class="contact"><a href="#{}">{}</a></td>\n'.format(i.group_name + "_" + str(i.zpk), "(Group) " + i.group_name).encode('utf-8'))

        wfile.write('<td class="contact">{}</td>\n'.format(i.contact_id).encode('utf-8'))
        # Contact Status
        if i.contact_status == 2:
            wfile.write('<td ><img src="data/img/verification_green.png" alt="2"> </td>'.encode('utf-8'))
        elif i.contact_status == 1:
            wfile.write('<td ><img src="data/img/verification_orange.png" alt="1"> </td>'.encode('utf-8'))
        elif i.contact_status == 0:
            wfile.write('<td ><img src="data/img/verification_red.png" alt="0"> </td>'.encode('utf-8'))
        else:
             wfile.write('<td>{}</td>\n'.format(contactstatus).encode('utf-8'))

        wfile.write('<td>{}</td>\n'.format(i.msg_count).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.contact_unread_msg).encode('utf-8'))
        wfile.write('<td><a href="#{}">{}</a></td>\n'.format(str(i.contact_name).replace(" ", "") + "_" + str(lastmessagedate).replace(" ",""), lastmessagedate).encode('utf-8'))
        wfile.write('</tr>\n'.encode('utf-8'))
    wfile.write('</tbody>\n'.encode('utf-8'))
    # writes 1st table footer
    wfile.write('</table>\n'.encode('utf-8'))

    global content_type

    # writes a table for each chat session
    for i in chat_session_list:#
        contactname = convertsmileys ( i.contact_name ) # chat name
        try:
            chatid = i.contact_id.split('@')[0]
        except:
            chatid = i.contact_id

        if i.group_name == "" or i.group_name is None:
            wfile.write('<h3>Chat session <a href="#top">#</a> {}: <a name="{}">{}</a></h3>\n'.format(i.zpk, i.contact_name, contactname).encode('utf-8'))
        else:
            wfile.write('<h3>Chat session <a href="#top">#</a> {}: <a name="{}">{}</a></h3>\n'.format("(Group) " + i.group_name, i.group_name + "_" + str(i.zpk), "").encode('utf-8'))

        wfile.write('<table class="sortable" id="msg_{}" border="1" cellpadding="2" cellspacing="0">\n'.format(chatid).encode('utf-8'))
        wfile.write('<thead>\n'.encode('utf-8'))
        wfile.write('<tr>\n'.encode('utf-8'))
        wfile.write('<th>PK</th>\n'.encode('utf-8'))
        wfile.write('<th>Chat</th>\n'.encode('utf-8'))
        wfile.write('<th>Msg date</th>\n'.encode('utf-8'))
        wfile.write('<th>Delivery Date</th>\n'.encode('utf-8'))
        wfile.write('<th>Read Date</th>\n'.encode('utf-8'))
        wfile.write('<th>From</th>\n'.encode('utf-8'))
        wfile.write('<th>Msg content</th>\n'.encode('utf-8'))
        wfile.write('<th>Msg status</th>\n'.encode('utf-8'))
        wfile.write('<th>Media Type</th>\n'.encode('utf-8'))
#        wfile.write('<th>Media Size</th>\n'.encode('utf-8'))
        wfile.write('</tr>\n'.encode('utf-8'))
        wfile.write('</thead>\n'.encode('utf-8'))

        # writes table content
        wfile.write('<tbody>\n'.encode('utf-8'))
        for y in i.msg_list:

            # Determine type of content
            content_type = None

            if y.image_id:
                content_type = CONTENT_IMAGE

            if y.audio_id:
                content_type = CONTENT_AUDIO

            if y.video_id:
                content_type = CONTENT_VIDEO

            if y.msg_text is not None and y.msg_text is not "N/A":
                y.media_wa_type = ""
                content_type = CONTENT_TEXT
            # End if Clause

            # row class selection
            if content_type == CONTENT_NEWGROUPNAME:
               wfile.write('<tr class="newgroupname">\n'.encode('utf-8'))
            elif y.from_me == 1:
                wfile.write('<tr class="me">\n'.encode('utf-8'))
            else:
                wfile.write('<tr class="other">\n'.encode('utf-8'))

            # PK
            wfile.write('<td>{}</td>\n'.format(y.zpk).encode('utf-8'))

            # Chat name
            if i.group_id != "":
                wfile.write('<td class="contact">{}</td>\n'.format(i.group_name).encode('utf-8'))
            else:
                wfile.write('<td class="contact">{}</td>\n'.format(contactname).encode('utf-8'))
            # Msg date
            if y.msg_date == i.last_message_date:
                wfile.write('<td><a name="{}">{}</a></td>\n'.format(str(i.contact_name).replace(" ", "") + "_" + str(i.last_message_date).replace(" ",""),str(y.msg_date).replace(" ","&nbsp;")).encode('utf-8'))
            else:
                wfile.write('<td>{}</td>\n'.format(str(y.msg_date).replace(" ","&nbsp;")).encode('utf-8'))
            # Msg delivery date
            wfile.write('<td>{}</td>\n'.format(str(y.delivery_date).replace(" ","&nbsp;")).encode('utf-8'))
            # Msg read date
            wfile.write('<td>{}</td>\n'.format(str(y.read_date).replace(" ","&nbsp;")).encode('utf-8'))
            # From
            if i.group_id != "":
                wfile.write('<td class="contact">{}</td>\n'.format(y.contact_from).encode('utf-8'))
            else:
                if y.contact_from == "me":
                    wfile.write('<td class="contact">{}</td>\n'.format(y.contact_from).encode('utf-8'))
                else:
                    wfile.write('<td class="contact">{}</td>\n'.format(i.contact_name).encode('utf-8'))

            # date elaboration for further use
            date = str(y.msg_date)[:10]
            if date != 'N/A' and date != 'N/A error':
                date = int(date.replace("-",""))

            # Display Msg content (Text/Media)

            if content_type == CONTENT_IMAGE:
                try:
                    wfile.write('<td class="text"><a onclick="image(this.href);return(false);" target="image" href="{}"><img src="{}" width="20%" height="20%" alt="Image"/></a>&nbsp;|&nbsp;<a onclick="image(this.href);return(false);" target="image" href="{}">Image</a>'.format(y.image_url, y.image_url, y.image_url).encode('utf-8'))
                except:
                    wfile.write('<td class="text">Bild N/A'.encode('utf-8'))
            elif content_type == CONTENT_AUDIO:
                try:
                    wfile.write('<td class="text"><a onclick="media(this.href);return(false);" target="media" href="{}">Audio (offline)</a>'.format(y.audio_url).encode('utf-8'))
                except:
                    wfile.write('<td class="text">Audio N/A'.encode('utf-8'))
            elif content_type == CONTENT_VIDEO:
                try:
#                    wfile.write('<td class="text"><a onclick="media(this.href);return(false);" target="media" href="{}"><img src="{}" alt="Video"/></a>&nbsp;|&nbsp;<a onclick="media(this.href);return(false);" target="media" href="{}">Video</a>'.format(y.video_url, y.video_url, y.video_url).encode('utf-8'))
                    wfile.write('<td class="text"><a onclick="media(this.href);return(false);" target="media" href="{}">Video<img src="{}" alt="Video"/>'.format(y.video_url, y.video_url).encode('utf-8'))
                except:
                    wfile.write('<td class="text">Video N/A'.encode('utf-8'))
            elif content_type == CONTENT_MEDIA_THUMB:
                try:
#                    wfile.write('<td class="text"><a onclick="image(this.href);return(false);" target="image" href="{}"><img src="{}" alt="Media"/></a>&nbsp;|&nbsp;<a onclick="image(this.href);return(false);" target="image" href="{}">Media</a>'.format("",y.media_thumb,"").encode('utf-8'))
                    wfile.write('<td class="text">Media N/A'.encode('utf-8'))
                except:
                    wfile.write('<td class="text">Media N/A'.encode('utf-8'))
            elif content_type == CONTENT_MEDIA_NOTHUMB:
                try:
                    wfile.write('<td class="text"><a onclick="media(this.href);return(false);" target="media" href="{}">Media (online)</a>&nbsp;|&nbsp;<a onclick="media(this.href);return(false);" target="media" href="{}">Media (offline)</a>'.format(y.media_url, linkmedia).encode('utf-8'))
                except:
                    wfile.write('<td class="text">Media N/A'.encode('utf-8'))
            elif content_type == CONTENT_VCARD:
                if y.vcard_name == "" or y.vcard_name is None:
                    vcardintro = ""
                else:
                    vcardintro = "CONTACT: <b>" + y.vcard_name + "</b><br>\n"
                y.vcard_string = y.vcard_string.replace ("\n", "<br>\n")
                try:
                    wfile.write('<td class="text">{}'.format(vcardintro + y.vcard_string).encode('utf-8'))
                except:
                    wfile.write('<td class="text">VCARD N/A'.encode('utf-8'))
            elif content_type == CONTENT_GPS:
                try:
                    if gpsname == "" or gpsname == None:
                        gpsname = ""
                    else:
                        gpsname = "\n" + gpsname
                    gpsname = gpsname.replace ("\n", "<br>\n")
                    if y.media_thumb:
                        wfile.write('<td class="text"><a onclick="image(this.href);return(false);" target="image" href="https://maps.google.com/?q={},{}"><img src="{}" alt="GPS"/></a>{}'.format(y.latitude, y.longitude, y.media_thumb, gpsname).encode('utf-8'))
                    else:
                        wfile.write('<td class="text"><a onclick="image(this.href);return(false);" target="image" href="https://maps.google.com/?q={},{}">GPS: {}, {}</a>{}'.format(y.latitude, y.longitude, y.latitude, y.longitude, gpsname).encode('utf-8'))
                except:
                    wfile.write('<td class="text">GPS N/A'.encode('utf-8'))
            elif content_type == CONTENT_NEWGROUPNAME:
                content_type = CONTENT_OTHER
            elif content_type != CONTENT_TEXT:
                content_type = CONTENT_OTHER
            # End of If-Clause, now text or other type of content:
            if content_type == CONTENT_TEXT or content_type == CONTENT_OTHER:
                msgtext = convertsmileys ( y.msg_text )
                msgtext = re.sub(r'(http[^\s\n\r]+)', r'<a onclick="image(this.href);return(false);" target="image" href="\1">\1</a>', msgtext)
                msgtext = re.sub(r'((?<!\S)www\.[^\s\n\r]+)', r'<a onclick="image(this.href);return(false);" target="image" href="http://\1">\1</a>', msgtext)
                msgtext = msgtext.replace ("\n", "<br>\n")
                try:
                    wfile.write('<td class="text">{}'.format(msgtext).encode('utf-8'))
                except:
                    wfile.write('<td class="text">N/A'.encode('utf-8'))
            # wfile.write(str(content_type)) #Debug
            wfile.write('</td>\n'.encode('utf-8'))

            # Msg status
            wfile.write('<td>{}</td>\n'.format(y.status).encode('utf-8'))

            # Media type
            wfile.write('<td>{}</td>\n'.format(y.media_wa_type).encode('utf-8'))

        wfile.write('</tbody>\n'.encode('utf-8'))
        # writes 1st table footer
        wfile.write('</table>\n'.encode('utf-8'))

    # writes page footer
    wfile.write('</body></html>\n'.encode('utf-8'))
    wfile.close()
    print ("done!")

    #END
    webbrowser.open(outfile)

def getContacts(c1, c2, tmpdir):
    #get all of the threema contacts
    contact_list = []
    try:
        c1.execute("SELECT Z_PK, ZABRECORDID, ZFEATURELEVEL, ZSTATE, ZVERIFICATIONLEVEL, ZFIRSTNAME, ZIDENTITY, ZLASTNAME, ZPUBLICNICKNAME, ZVERIFIEDEMAIL, ZVERIFIEDMOBILENO, ZIMAGEDATA, ZPUBLICKEY FROM ZCONTACT ORDER BY Z_PK")
        for c in c1:
            chatid =None
            msgcnt = None
            lastmsg = None
            lastmsgdate = None
            zpk = None
            try:
                c2.execute("SELECT Z_PK, ZLASTMESSAGE FROM ZCONVERSATION WHERE ZCONTACT=?", [c["Z_PK"]])
                chatid, lastmsg = c2.fetchone()
                if chatid != "" and chatid is not None:
                    c2.execute("SELECT Z_PK, count(*) FROM ZMESSAGE WHERE ZCONVERSATION=?", [str(chatid)])
                    zpk, msgcnt = c2.fetchone()
                if lastmsg != "" and lastmsg is not None:
                    c2.execute("SELECT Z_PK, ZDATE FROM ZMESSAGE WHERE Z_PK=?", [str(lastmsg)])
                    zpk, lastmsgdate = c2.fetchone()
            except:
                pass

            contact = ThreemaContact(c["Z_PK"],c["ZABRECORDID"],c["ZFEATURELEVEL"],c["ZSTATE"],c["ZVERIFICATIONLEVEL"],c["ZFIRSTNAME"],c["ZIDENTITY"],c["ZLASTNAME"],c["ZPUBLICNICKNAME"],c["ZVERIFIEDEMAIL"],c["ZVERIFIEDMOBILENO"],c["ZIMAGEDATA"],c["ZPUBLICKEY"], chatid, msgcnt, lastmsg, lastmsgdate)
            if contact.has_image == True:
                #contact.imageurl = writeMedia(tmpdir,str(contact.zpk) + "_" + str(contact.lastname), contact.imagedata, 'jpg')
                contact.imageurl = writeMedia(tmpdir,str(contact.zpk) + "_" + str(contact.abrecordid), contact.imagedata, 'jpg')
            contact_list.append(contact)
        contact_list = sorted(contact_list, key=lambda ContactList: ContactList.lastname, reverse=True)
        return contact_list
    except sqlite3.Error as msg:
        print('Error: {}'.format(msg))
        return None

def getChatSessions(c1):
    # gets all the chat sessions
    chat_session_list = []
    try:
        c1.execute("SELECT ZCONVERSATION.ZLASTMESSAGE AS LASTMSG, ZCONVERSATION.ZCONTACT AS CONTACT_ID, ZCONVERSATION.Z_PK AS ZPK, ZCONTACT.ZFIRSTNAME AS CONTACT_FIRSTNAME, ZCONTACT.ZLASTNAME AS CONTACT_LASTNAME, ZCONTACT.ZIDENTITY AS CONTACT_IDENTITY, ZCONTACT.ZPUBLICNICKNAME AS CONTACT_NICKNAME, ZMESSAGE.ZTEXT AS MSGTEXT, ZMESSAGE.ZDATE AS MSGDATE, ZMESSAGE.ZISOWN AS FROMME, ZCONVERSATION.ZGROUPNAME AS GROUPNAME, ZCONVERSATION.ZGROUPID AS GROUP_ID, ZCONVERSATION.ZUNREADMESSAGECOUNT AS UNREADMSGCNT, ZCONTACT.ZVERIFICATIONLEVEL AS STATUS FROM ZCONVERSATION LEFT OUTER JOIN ZCONTACT ON (ZCONVERSATION.ZCONTACT = ZCONTACT.Z_PK) INNER JOIN ZMESSAGE ON (ZCONVERSATION.ZLASTMESSAGE = ZMESSAGE.Z_PK)")
        for chats in c1:
            #print chats
            curr_chat =  ThreemaChatsession(chats["LASTMSG"],chats["CONTACT_ID"],chats["ZPK"],chats["CONTACT_FIRSTNAME"],chats["CONTACT_LASTNAME"],chats["CONTACT_IDENTITY"],chats["CONTACT_NICKNAME"], chats["MSGTEXT"],chats["MSGDATE"],chats["FROMME"],chats["GROUPNAME"],chats["GROUP_ID"],chats["UNREADMSGCNT"],chats["STATUS"], None)
            chat_session_list.append(curr_chat)
        chat_session_list = sorted(chat_session_list, key=lambda Chatsession: Chatsession.last_message_date, reverse=True)
        return chat_session_list
    except sqlite3.Error as msg:
        print('Error: {}'.format(msg))
        return None

def getChatMessages(c1, chat_session_list, tmpdir, threemadir=None):
    # for each chat session, gets all messages
    count_chats = 0

    for chats in chat_session_list:
        count_chats = count_chats + 1
        try:
            # c1.execute("SELECT * FROM ZMESSAGE WHERE ZCONVERSATION=? ORDER BY Z_PK ASC;", [chats.zpk])
            c1.execute("SELECT ZMESSAGE.Z_PK AS Z_PK, ZMESSAGE.ZISOWN AS ZISOWN, ZMESSAGE.ZDATE AS ZDATE, \
                        ZMESSAGE.ZTEXT AS ZTEXT, ZMESSAGE.ZREAD AS ZREAD, ZMESSAGE.ZIMAGE AS ZIMAGE, \
                        ZMESSAGE.ZIMAGESIZE AS ZIMAGESIZE, ZMESSAGE.ZTHUMBNAIL AS ZTHUMBNAIL, \
                        ZMESSAGE.ZAUDIO AS ZAUDIO, ZMESSAGE.ZVIDEO AS ZVIDEO, ZMESSAGE.ZVIDEOSIZE AS ZVIDEOSIZE,\
                        ZMESSAGE.ZDELIVERYDATE AS ZDELIVERYDATE, ZMESSAGE.ZREADDATE ZREADDATE, \
                        ZMESSAGE.ZLATITUDE AS ZLATITUDE, ZMESSAGE.ZLONGITUDE AS ZLONGITUDE, \
                        ZCONTACT.ZFIRSTNAME AS FIRSTNAME, ZCONTACT.ZLASTNAME LASTNAME, ZCONTACT.ZPUBLICNICKNAME AS NICKNAME \
                        FROM ZMESSAGE LEFT OUTER JOIN ZCONTACT ON (ZMESSAGE.ZSENDER = ZCONTACT.Z_PK) WHERE ZCONVERSATION=? ORDER BY ZMESSAGE.Z_PK ASC;", [chats.zpk])
            count_messages = 0
            for msgs in c1:
                count_messages = count_messages + 1
                try:

                    if msgs["ZISOWN"] == 1:
                        contactfrom = "me"
                    else:
                        contactfrom = ""

                    thumb_nail = "N/A"

                    curr_message = ThreemaMessage(msgs["Z_PK"],msgs["ZISOWN"],msgs["ZDATE"],msgs["ZTEXT"],contactfrom, \
                                                  msgs["LASTNAME"],msgs["FIRSTNAME"],msgs["NICKNAME"],msgs["ZREAD"], \
                                                  msgs["ZIMAGE"],msgs["ZIMAGESIZE"],msgs["ZTHUMBNAIL"],msgs["ZAUDIO"], \
                                                  msgs["ZVIDEO"],msgs["ZVIDEOSIZE"],msgs["ZDELIVERYDATE"], \
                                                  msgs["ZREADDATE"],msgs["ZLATITUDE"],msgs["ZLONGITUDE"],thumb_nail)
                except sqlite3.Error as msg:
                    print('Error while reading message #{} in chat #{}: {}'.format(count_messages, chats.zpk, msg))
                    curr_message = ThreemaMessage(None,None,None,"_Error: sqlite3.Error, see output in window",None,None,None,None,None,None,None,None,None,None,None)
                except TypeError as msg:
                    print('Error while reading message #{} in chat #{}: {}'.format(count_messages, chats.zpk, msg))
                    curr_message = ThreemaMessage(None,None,None,"_Error: TypeError, see output in window",None,None,None,None,None,None,None,None,None,None,None)
                chats.msg_list.append(curr_message)
            chats.msg_count = count_messages

        except sqlite3.Error as msg:
            print('Error sqlite3.Error while reading chat #{}: {}'.format(chats.zpk, msg))
            return None
        except TypeError as msg:
            print('Error TypeError while reading chat #{}: {}'.format(chats.zpk, msg))
            return None

    for chats in chat_session_list:
        for msgs in chats.msg_list:
            if  (msgs.image_id is not "" and msgs.image_id):
                try:
                    c1.execute("Select Z_PK, ZDATA FROM ZIMAGEDATA WHERE Z_PK=?", [msgs.image_id])
                    id, image = c1.fetchone()
                    fileheader = "".join(hex(ord(n)) for n in image[:5])
                    if str(fileheader) == "0x10xff0xd80xff0xe0":
                        msgs.image_url = writeMedia(tmpdir,str(msgs.zpk) + "_" + str(msgs.imgthumb_id), image[1:], 'jpg')
                    else:
                        msgs.image_url = getMediaURL(threemadir, tmpdir,str(msgs.zpk) + "_" + str(msgs.image_id), image[1:-1], 'jpg')
                except:
                    print "Error reading image: %s" %msgs.zpk + "_" + str(msgs.image_id)
            if (msgs.audio_id is not "" and msgs.audio_id):
                try:
                    c1.execute("Select Z_PK, ZDATA FROM ZAUDIODATA WHERE Z_PK=?", [msgs.audio_id])
                    id, audio = c1.fetchone()
                    fileheader = "".join(hex(ord(n)) for n in audio[:7])
                    if str(fileheader) == '0x10x00x00x00x1c0x660x74':
                        msgs.audio_url = writeMedia(tmpdir,str(msgs.zpk) + "_" + str(msgs.audio_id), audio[1:], 'm4a') #[1:])
                    else:
                        msgs.audio_url = getMediaURL(threemadir, tmpdir,str(msgs.zpk) + "_" + str(msgs.audio_id), audio[1:-1], 'm4a') #[1:-1])
                except:
                    print "Error reading audio: %s" %str(msgs.zpk) + "_" + str(msgs.audio_id)
            if (msgs.video_id is not "" and msgs.video_id):
                try:
                    c1.execute("Select Z_PK, ZDATA FROM ZVIDEODATA WHERE Z_PK=?", [msgs.video_id])
                    id, video = c1.fetchone()
                    fileheader = "".join(hex(ord(n)) for n in video[:12])
                    if str(fileheader) == "0x000x000x000x1C0x660x740x790x700x6D0x700x340x32":
                        msgs.video_url = writeMedia(tmpdir,str(msgs.zpk) + "_" + str(msgs.video_id), video, 'mov') #[1:])
                    else:
                        msgs.video_url = getMediaURL(threemadir, tmpdir,str(msgs.zpk) + "_" + str(msgs.video_id), video[1:-1], 'mov')# [1:-1])
                except:
                    print "Error reading video: %s" %str(msgs.zpk) + "_" + str(msgs.video_id) + "_" + str(video)
    return chat_session_list

################################################################################
################################################################################
# MAIN
def main(argv):

    chat_session_list = []
    contact_list = []
    global mode
    global PYTHON_VERSION
    threemadir = ""
    

    # parser options
    parser = ArgumentParser(description='Converts a Threema database to HTML.')
    parser.add_argument(dest='infile', 
                       help="input 'ThreemaData.sqlite' (iPhone) file to scan")
    parser.add_argument('-o', '--outfile',  dest='outfile', 
                       help="optionally choose name of output file")
    options = parser.parse_args()


    # checks for the input file
    if options.infile is None:
        parser.print_help()
        sys.exit(1)
    if not os.path.exists(options.infile):
        print('"{}" file is not found!'.format(options.infile))
        sys.exit(1)

    # connects to the database(s)
    msgstore = sqlite3.connect(options.infile)
    msgstore.row_factory = sqlite3.Row
    c1 = msgstore.cursor()
    c2 = msgstore.cursor()

    # check on platform
    mode = IPHONE
    print ("iPhone mode!\n")


    # gets metadata plist info (iphone only)
    try:
        # ------------------------------------------------------ #
        #  IPHONE  ThreemaData.sqlite file *** Z_METADATA TABLE  #
        # ------------------------------------------------------ #
        # Z_VERSION INTEGER PRIMARY KEY
        # Z_UIID VARCHAR
        # Z_PLIST BLOB
        from util.bplist import BPlistReader
        c1.execute("SELECT * FROM Z_METADATA")
        metadata = c1.fetchone()
        print ("*** METADATA PLIST DUMP ***\n")
        print ("Plist ver.:  {}".format(metadata["Z_VERSION"]))
        print ("UUID:        {}".format(metadata["Z_UUID"]))
        bpReader = BPlistReader(metadata["Z_PLIST"])
        plist = bpReader.parse()

        for entry in plist.items():
            if entry[0] == "NSStoreModelVersionHashes":
                print ("{}:".format(entry[0]))
                for inner_entry in entry[1].items():
                    print ("\t{}: {}".format(inner_entry[0],base64.b64encode(inner_entry[1]).decode("utf-8")))
            else:
                print ("{}: {}".format(entry[0],entry[1]))
        print ("\n***************************\n")
          
    except:
        print ("Metadata Plist Dump is failed. Note that you need to use Python 2.7 for that bplist.py works")
    
    threemadir = os.path.dirname(options.infile)
    tmpdir = makeTmpDir()

    contact_list = getContacts(c1, c2, tmpdir)
    chat_session_list = getChatSessions(c1)
    chat_session_list = getChatMessages(c1, chat_session_list, tmpdir, threemadir)

    # OUTPUT
    owner = "Threema-Report"
    if options.outfile is None:
        outfile = "Threema-Report"
    else:
        outfile = options.outfile

    printHTMLReport(outfile, contact_list, chat_session_list)

##### GLOBAL variables #####

PYTHON_VERSION = None
testtext = ""
testtext = testtext.replace('\ue40e', 'v3')
if testtext == "v3":    
    PYTHON_VERSION = 3
#    print ("Python Version 3.x")
else:
    PYTHON_VERSION = 2
#    print ("Python Version 2.x")
    reload(sys)
    sys.setdefaultencoding( "utf-8" )
    import convert_smileys_python_2


mode    = None
IPHONE  = 1
ANDROID = 2

content_type          = None
CONTENT_TEXT          = 0
CONTENT_IMAGE         = 1
CONTENT_AUDIO         = 2
CONTENT_VIDEO         = 3
CONTENT_VCARD         = 4
CONTENT_GPS           = 5
CONTENT_NEWGROUPNAME  = 6
CONTENT_MEDIA_THUMB   = 7
CONTENT_MEDIA_NOTHUMB = 8
CONTENT_OTHER         = 99

flistvid = {}
flistaud = {}
flistimg = {}

css_style = """
<style type="text/css">
body {
    font-family: calibri;
    background-color: #f5f5f5;
}
h1 {
    font-family: courier;
    font-style:italic;
    color: #444444;
}
h2 {
    font-style:italic;
    color: #444444;
}
h3 {
    font-style:italic;
}
table {
    text-align: center;
}
th {
    font-style:italic;
}
td.text {
    width: 600px;
    text-align: left;
}
td.contact {
    width: 250px;
}
tr.even {
    background-color: #DDDDDD
}
tr.me {
    background-color: #88FF88;
}
tr.other {
    background-color: #F5F5F5;
}
tr.newgroupname {
    background-color: #FFCC33;
}
</style>
"""

popups = """
function media( url )
{
  if (typeof(newwindow) !== "undefined" && !newwindow.closed)
  {
    newwindow.close();
  } else
  {
  }
  newwindow=window.open("about:blank", "media", "menubar=0,location=1");
  newwindow.document.write('<html><body><embed src="' + url + '" width="800" height="600" /></body></html>');
  //newwindow.document.write('<video src="' + url + '" controls="controls">video doesn't work</video>');
}

function image( url )
{
  if (typeof(imagewindow) !== "undefined" && !imagewindow.closed)
  {
    imagewindow=window.open(url,'image','menubar=0,location=1');
    imagewindow.focus();
  } else
  {
    imagewindow=window.open(url,'image','menubar=0,location=1');
  }
}
"""

sortable = """
/*
Table sorting script  by Joost de Valk, check it out at http://www.joostdevalk.nl/code/sortable-table/.
Based on a script from http://www.kryogenix.org/code/browser/sorttable/.
Distributed under the MIT license: http://www.kryogenix.org/code/browser/licence.html .

Copyright (c) 1997-2007 Stuart Langridge, Joost de Valk.

Version 1.5.7
*/

/* You can change these values */
var image_path = "data/sort-table/";
var image_up = "arrow-up.gif";
var image_down = "arrow-down.gif";
var image_none = "arrow-none.gif";
var europeandate = true;
var alternate_row_colors = true;

/* Don't change anything below this unless you know what you're doing */
addEvent(window, "load", sortables_init);

var SORT_COLUMN_INDEX;
var thead = false;

function sortables_init() {
    // Find all tables with class sortable and make them sortable
    if (!document.getElementsByTagName) return;
    tbls = document.getElementsByTagName("table");
    for (ti=0;ti<tbls.length;ti++) {
        thisTbl = tbls[ti];
        if (((' '+thisTbl.className+' ').indexOf("sortable") != -1) && (thisTbl.id)) {
            ts_makeSortable(thisTbl);
        }
    }
}

function ts_makeSortable(t) {
    if (t.rows && t.rows.length > 0) {
        if (t.tHead && t.tHead.rows.length > 0) {
            var firstRow = t.tHead.rows[t.tHead.rows.length-1];
            thead = true;
        } else {
            var firstRow = t.rows[0];
        }
    }
    if (!firstRow) return;
    
    // We have a first row: assume it's the header, and make its contents clickable links
    for (var i=0;i<firstRow.cells.length;i++) {
        var cell = firstRow.cells[i];
        var txt = ts_getInnerText(cell);
        if (cell.className != "unsortable" && cell.className.indexOf("unsortable") == -1) {
            cell.innerHTML = '<a href="#" class="sortheader" onclick="ts_resortTable(this, '+i+');return false;">'+txt+'<span class="sortarrow">&nbsp;&nbsp;<img src="'+ image_path + image_none + '" alt="&darr;"/></span></a>';
        }
    }
    if (alternate_row_colors) {
        alternate(t);
    }
}

function ts_getInnerText(el) {
    if (typeof el == "string") return el;
    if (typeof el == "undefined") { return el };
    if (el.innerText) return el.innerText;    //Not needed but it is faster
    var str = "";
    
    var cs = el.childNodes;
    var l = cs.length;
    for (var i = 0; i < l; i++) {
        switch (cs[i].nodeType) {
            case 1: //ELEMENT_NODE
                str += ts_getInnerText(cs[i]);
                break;
            case 3:    //TEXT_NODE
                str += cs[i].nodeValue;
                break;
        }
    }
    return str;
}

function ts_resortTable(lnk, clid) {
    var span;
    for (var ci=0;ci<lnk.childNodes.length;ci++) {
        if (lnk.childNodes[ci].tagName && lnk.childNodes[ci].tagName.toLowerCase() == 'span') span = lnk.childNodes[ci];
    }
    var spantext = ts_getInnerText(span);
    var td = lnk.parentNode;
    var column = clid || td.cellIndex;
    var t = getParent(td,'TABLE');
    // Work out a type for the column
    if (t.rows.length <= 1) return;
    var itm = "";
    var i = 0;
    while (itm == "" && i < t.tBodies[0].rows.length) {
        var itm = ts_getInnerText(t.tBodies[0].rows[i].cells[column]);
        itm = trim(itm);
        if (itm.substr(0,4) == "<!--" || itm.length == 0) {
            itm = "";
        }
        i++;
    }
    if (itm == "") return; 
    sortfn = ts_sort_caseinsensitive;
    if (itm.match(/^\d\d[\/\.-][a-zA-z][a-zA-Z][a-zA-Z][\/\.-]\d\d\d\d$/)) sortfn = ts_sort_date;
    if (itm.match(/^\d\d[\/\.-]\d\d[\/\.-]\d\d\d{2}?$/)) sortfn = ts_sort_date;
    if (itm.match(/^-?[£$€Û¢´]\d/)) sortfn = ts_sort_numeric;
    if (itm.match(/^-?(\d+[,\.]?)+(E[-+][\d]+)?%?$/)) sortfn = ts_sort_numeric;
    SORT_COLUMN_INDEX = column;
    var firstRow = new Array();
    var newRows = new Array();
    for (k=0;k<t.tBodies.length;k++) {
        for (i=0;i<t.tBodies[k].rows[0].length;i++) { 
            firstRow[i] = t.tBodies[k].rows[0][i]; 
        }
    }
    for (k=0;k<t.tBodies.length;k++) {
        if (!thead) {
            // Skip the first row
            for (j=1;j<t.tBodies[k].rows.length;j++) { 
                newRows[j-1] = t.tBodies[k].rows[j];
            }
        } else {
            // Do NOT skip the first row
            for (j=0;j<t.tBodies[k].rows.length;j++) { 
                newRows[j] = t.tBodies[k].rows[j];
            }
        }
    }
    newRows.sort(sortfn);
    if (span.getAttribute("sortdir") == 'down') {
            ARROW = '&nbsp;&nbsp;<img src="'+ image_path + image_down + '" alt="&darr;"/>';
            newRows.reverse();
            span.setAttribute('sortdir','up');
    } else {
            ARROW = '&nbsp;&nbsp;<img src="'+ image_path + image_up + '" alt="&uarr;"/>';
            span.setAttribute('sortdir','down');
    } 
    // We appendChild rows that already exist to the tbody, so it moves them rather than creating new ones
    // don't do sortbottom rows
    for (i=0; i<newRows.length; i++) { 
        if (!newRows[i].className || (newRows[i].className && (newRows[i].className.indexOf('sortbottom') == -1))) {
            t.tBodies[0].appendChild(newRows[i]);
        }
    }
    // do sortbottom rows only
    for (i=0; i<newRows.length; i++) {
        if (newRows[i].className && (newRows[i].className.indexOf('sortbottom') != -1)) 
            t.tBodies[0].appendChild(newRows[i]);
    }
    // Delete any other arrows there may be showing
    var allspans = document.getElementsByTagName("span");
    for (var ci=0;ci<allspans.length;ci++) {
        if (allspans[ci].className == 'sortarrow') {
            if (getParent(allspans[ci],"table") == getParent(lnk,"table")) { // in the same table as us?
                allspans[ci].innerHTML = '&nbsp;&nbsp;<img src="'+ image_path + image_none + '" alt="&darr;"/>';
            }
        }
    }        
    span.innerHTML = ARROW;
    alternate(t);
}

function getParent(el, pTagName) {
    if (el == null) {
        return null;
    } else if (el.nodeType == 1 && el.tagName.toLowerCase() == pTagName.toLowerCase()) {
        return el;
    } else {
        return getParent(el.parentNode, pTagName);
    }
}

function sort_date(date) {    
    // y2k notes: two digit years less than 50 are treated as 20XX, greater than 50 are treated as 19XX
    dt = "00000000";
    if (date.length == 11) {
        mtstr = date.substr(3,3);
        mtstr = mtstr.toLowerCase();
        switch(mtstr) {
            case "jan": var mt = "01"; break;
            case "feb": var mt = "02"; break;
            case "mar": var mt = "03"; break;
            case "apr": var mt = "04"; break;
            case "may": var mt = "05"; break;
            case "jun": var mt = "06"; break;
            case "jul": var mt = "07"; break;
            case "aug": var mt = "08"; break;
            case "sep": var mt = "09"; break;
            case "oct": var mt = "10"; break;
            case "nov": var mt = "11"; break;
            case "dec": var mt = "12"; break;
            // default: var mt = "00";
        }
        dt = date.substr(7,4)+mt+date.substr(0,2);
        return dt;
    } else if (date.length == 10) {
        if (europeandate == false) {
            dt = date.substr(6,4)+date.substr(0,2)+date.substr(3,2);
            return dt;
        } else {
            dt = date.substr(6,4)+date.substr(3,2)+date.substr(0,2);
            return dt;
        }
    } else if (date.length == 8) {
        yr = date.substr(6,2);
        if (parseInt(yr) < 50) { 
            yr = '20'+yr; 
        } else { 
            yr = '19'+yr; 
        }
        if (europeandate == true) {
            dt = yr+date.substr(3,2)+date.substr(0,2);
            return dt;
        } else {
            dt = yr+date.substr(0,2)+date.substr(3,2);
            return dt;
        }
    }
    return dt;
}

function ts_sort_date(a,b) {
    dt1 = sort_date(ts_getInnerText(a.cells[SORT_COLUMN_INDEX]));
    dt2 = sort_date(ts_getInnerText(b.cells[SORT_COLUMN_INDEX]));
    
    if (dt1==dt2) {
        return 0;
    }
    if (dt1<dt2) { 
        return -1;
    }
    return 1;
}
function ts_sort_numeric(a,b) {
    var aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]);
    aa = clean_num(aa);
    var bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]);
    bb = clean_num(bb);
    return compare_numeric(aa,bb);
}
function compare_numeric(a,b) {
    var a = parseFloat(a);
    a = (isNaN(a) ? 0 : a);
    var b = parseFloat(b);
    b = (isNaN(b) ? 0 : b);
    return a - b;
}
function ts_sort_caseinsensitive(a,b) {
    aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]).toLowerCase();
    bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]).toLowerCase();
    if (aa==bb) {
        return 0;
    }
    if (aa<bb) {
        return -1;
    }
    return 1;
}
function ts_sort_default(a,b) {
    aa = ts_getInnerText(a.cells[SORT_COLUMN_INDEX]);
    bb = ts_getInnerText(b.cells[SORT_COLUMN_INDEX]);
    if (aa==bb) {
        return 0;
    }
    if (aa<bb) {
        return -1;
    }
    return 1;
}
function addEvent(elm, evType, fn, useCapture)
// addEvent and removeEvent
// cross-browser event handling for IE5+,    NS6 and Mozilla
// By Scott Andrew
{
    if (elm.addEventListener){
        elm.addEventListener(evType, fn, useCapture);
        return true;
    } else if (elm.attachEvent){
        var r = elm.attachEvent("on"+evType, fn);
        return r;
    } else {
        alert("Handler could not be removed");
    }
}
function clean_num(str) {
    str = str.replace(new RegExp(/[^-?0-9.]/g),"");
    return str;
}
function trim(s) {
    return s.replace(/^\s+|\s+$/g, "");
}
function alternate(table) {
    // Take object table and get all it's tbodies.
    var tableBodies = table.getElementsByTagName("tbody");
    // Loop through these tbodies
    for (var i = 0; i < tableBodies.length; i++) {
        // Take the tbody, and get all it's rows
        var tableRows = tableBodies[i].getElementsByTagName("tr");
        // Loop through these rows
        // Start at 1 because we want to leave the heading row untouched
        for (var j = 0; j < tableRows.length; j++) {
            // Check if j is even, and apply classes for both possible results
            if ( (j % 2) == 0  ) {
                if ( !(tableRows[j].className.indexOf('odd') == -1) ) {
                    tableRows[j].className = tableRows[j].className.replace('odd', 'even');
                } else {
                    if ( tableRows[j].className.indexOf('even') == -1 ) {
                        tableRows[j].className += " even";
                    }
                }
            } else {
                if ( !(tableRows[j].className.indexOf('even') == -1) ) {
                    tableRows[j].className = tableRows[j].className.replace('even', 'odd');
                } else {
                    if ( tableRows[j].className.indexOf('odd') == -1 ) {
                        tableRows[j].className += " odd";
                    }
                }
            } 
        }
    }
}
"""

if __name__ == '__main__':
    main(sys.argv[1:])

