# -*- coding: utf-8 -*-
'''
Module: Whatsapp Xtract

based on:   WhatsApp Xtract v2.1 - WhatsApp Backup Messages Extractor for Android and iPhone
            Original version:
            (C)opyright 2012 Fabio Sangiacomo <fabio.sangiacomo@digital-forensics.it>
            (C)opyright 2012 Martina Weidner  <martina.weidner@freenet.ch>

Current version:

'''

import sys, re, os, string, datetime, time, sqlite3, glob, webbrowser, base64, subprocess
from argparse import ArgumentParser
from os.path import expanduser
from iOSForensicClasses import WhatsappChatsession, WhatsappMessage, WhatsappContact, WhatsappPhone, makeTmpDir
from gui.whatsapp_form import Ui_frmWhatsapp
from PySide import QtCore, QtGui

SCALEFACTOR = 0.5
MEDIATYPE_TEXT  = 0
MEDIATYPE_IMAGE = 1
MEDIATYPE_VIDEO = 3

class whatsappGUI(QtGui.QMainWindow):
    def __init__(self, path2appdomain=None, path2groupdomain=None, work_dir=None):
        QtGui.QMainWindow.__init__(self)

        self.name = "whatsappGUI"
        self.contact_list = []
        self.chat_session_list = []

        if work_dir is not None:
            self.work_dir = work_dir
        else:
            self.work_dir = makeTmpDir()

        #ios 6 pfad zu whatsapp, dbs liegen unter documents, profiles unter Library/Media/Profiles, Media unter Media/<id>
        #ios 8 pfad zu whatsapp appdomain: Media liegt unter Library/Media/<id>, group-domain dbs direkt, profiles unter Media/Profiles
        if path2appdomain is None:
            QtGui.QMessageBox.information(self, "Information", "Nothing to do...")
            return
        else:
            self.path2appdomain = self.work_dir + "/" + path2appdomain

        self.path2media = self.path2appdomain + "/" + "Library"   #/Media"
        self.path2dbs = self.path2appdomain + "/" + "Documents"
        if path2groupdomain is None:
            #asume ios 6
            self.path2profiles = self.path2media + "/" + "Profile"
        else:
            #asume ios 8
            self.path2dbs = self.work_dir + "/" + path2groupdomain
            self.path2profiles = self.work_dir + "/" + path2groupdomain + "/" #+ "Media/Profile"

        self.ui = Ui_frmWhatsapp()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        QtCore.QObject.connect(self.ui.tableViewContacts, QtCore.SIGNAL("itemSelectionChanged()"), self.onTreeClickContacts)
        QtCore.QObject.connect(self.ui.tableViewChats, QtCore.SIGNAL("itemSelectionChanged()"), self.onTreeClickChats)
        QtCore.QObject.connect(self.ui.actionReport, QtCore.SIGNAL("triggered(bool)"), self.printReport)
        QtCore.QObject.connect(self.ui.actionExtract, QtCore.SIGNAL("triggered(bool)"), self.extractApp)

        wadb = self.path2dbs + "/" + "Contacts.sqlite"
        msgstore = sqlite3.connect(wadb)
        msgstore.row_factory = sqlite3.Row
        c1 = msgstore.cursor()

        self.contact_list = getContacts(c1)
        msgstore.close()

        contactsmodel = ContactsTableModel(self.contact_list)
        self.ui.tableViewContacts.setModel(contactsmodel)

        wadb = self.path2dbs + "/" + "ChatStorage.sqlite"
        msgstore = sqlite3.connect(wadb)
        msgstore.row_factory = sqlite3.Row
        c1 = msgstore.cursor()
        c2 = msgstore.cursor()

        self.chat_session_list = getChatSessions(c1, c2)
        self.chat_session_list = getChatMessages(c1, c2, self.chat_session_list)
        msgstore.close()
        chatsmodel = ChatsTableModel(self.chat_session_list)
        self.ui.tableViewChats.setModel(chatsmodel)

    def onTreeClickChats(self):
        index = self.ui.tableViewChats.currentIndex()
        row = index.row()
        msgmodel = MessagesTableModel(self.chat_session_list[row].msg_list, self.path2media)
        self.ui.tableViewMessages.setModel(msgmodel)

    def onTreeClickContacts(self):
        self.ui.labelStatus.setText("")
        self.ui.labelPicture.setPixmap("")
        index = self.ui.tableViewContacts.currentIndex()
        row = index.row()

        phones = self.contact_list[row].waphone_list
        phonesmodel = PhonesTableModel(phones)
        self.ui.tableViewPhones.setModel(phonesmodel)
        self.ui.labelStatus.setText(self.contact_list[row].ztext)

        if self.contact_list[row].contact_haspicture() == True:
            image_url = self.path2profiles + "/" + self.contact_list[row].zpicturepath + ".thumb"
            pixmap = QtGui.QPixmap(image_url)
            self.ui.labelPicture.setPixmap(pixmap)

    def extractApp(self):
        pass

    def printReport(self):

        path = expanduser("~")
        outdir = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", path,
                                                            QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks);

        if (outdir == None) or (len(outdir) == 0):
            return None

        outfile = outdir + "/Whatsapp-Report"
        printHTMLReport(outfile, self.chat_session_list)

class PhonesTableModel(QtCore.QAbstractTableModel):
    def __init__(self, phones=None, parent=None):
        super(PhonesTableModel, self).__init__(parent)

        self.header = ["ZLABEL", "ZPHONE"]
        if phones is None:
            self.phones = []
        else:
            self.phones = phones

    def rowCount(self, parent):
        return len(self.phones)

    def columnCount(self, parent):
        return 2

    def data(self, index, role=QtCore.Qt.DisplayRole):

        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None

        col = index.column()
        row = index.row()
        if col == 0:
            return self.phones[row].zlabel
        if col == 1:
            return self.phones[row].zphone

    def headerData(self, col, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

class ContactsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, contacts=None, parent=None):
        super(ContactsTableModel, self).__init__(parent)

        self.header = ["ZPK", "ZABUSERID", "ZLASTMODIFIEDDATE", "ZFIRSTNAME", "ZFULLNAME", "ZINDEXNAME"]
        if contacts is None:
            self.contacts = []
        else:
            self.contacts = contacts

    def rowCount(self, parent):
        return len(self.contacts)

    def columnCount(self, parent):
        return 6

    def data(self, index, role=QtCore.Qt.DisplayRole):

        if not index.isValid():
            return None #QtCore.QVariant()
#        elif role != QtCore.Qt.DisplayRole:
#            return None #QtCore.QVariant()

        col = index.column()
        row = index.row()

        if role == QtCore.Qt.BackgroundRole:
            if self.contacts[row].favorite_zpk != "" or self.contacts[row].status_zpk != "":
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.green))
            else:
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.gray))

        if col == 0:
            if role == QtCore.Qt.DisplayRole:
                return self.contacts[row].z_pk
        if col == 1:
            if role == QtCore.Qt.DisplayRole:
                return self.contacts[row].zabuserid
        if col == 2:
            if role == QtCore.Qt.DisplayRole:
                return str(self.contacts[row].zlastmodifieddate)
        if col == 3:
            if role == QtCore.Qt.DisplayRole:
                return self.contacts[row].zfirstname
        if col == 4:
            if role == QtCore.Qt.DisplayRole:
                return self.contacts[row].zfullname
        if col == 5:
            if role == QtCore.Qt.DisplayRole:
                return self.contacts[row].zindexname

    def headerData(self, col, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

class ChatsTableModel(QtCore.QAbstractTableModel):
    def __init__(self, chats=None, parent=None):
        super(ChatsTableModel, self).__init__(parent)

        self.header = ["ZPK", "Contact Name", "Contact ID", "Status", "#Msg", "#Unread", "Last Msg"]
        if chats is None:
            self.chats = []
        else:
            self.chats = chats

    def rowCount(self, parent):
        return len(self.chats)

    def columnCount(self, parent):
        return 7

    def data(self, index, role=QtCore.Qt.DisplayRole):

        if not index.isValid():
            return None #QtCore.QVariant()
        elif role != QtCore.Qt.DisplayRole:
            return None #QtCore.QVariant()

        col = index.column()
        row = index.row()
        if col == 0:
            return str(self.chats[row].pk_cs)
        if col == 1:
            return self.chats[row].contact_name
        if col == 2:
            return str(self.chats[row].contact_id)
        if col == 3:
            return convertsmileys(self.chats[row].contact_status)
        if col == 4:
            return str(self.chats[row].contact_msg_count)
        if col == 5:
            return str(self.chats[row].contact_unread_msg)
        if col == 6:
            return str(self.chats[row].last_message_date)

    def headerData(self, col, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None

class MessagesTableModel(QtCore.QAbstractTableModel):
    def __init__(self, messages=None, path2media=None, parent=None):
        super(MessagesTableModel, self).__init__(parent)

        self.header = ["ZPK", "Chat", "Msg Date", "From", "Message", "Msg Status", "Media Type", "Media Size"]

        if messages is None:
            self.messages = []
        else:
            self.messages = messages

        if path2media is None:
            self.path2media = ""
        else:
            self.path2media = path2media

    def rowCount(self, parent):
        return len(self.messages)

    def columnCount(self, parent):
        return 8

    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid():
            return None #QtCore.QVariant()
#        elif role != QtCore.Qt.DisplayRole:
#            return None #QtCore.QVariant()

        col = index.column()
        row = index.row()

        if role == QtCore.Qt.BackgroundRole:
            if self.messages[row].contact_from == "me":
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.green))
            else:
                return QtGui.QBrush(QtGui.QColor(QtCore.Qt.lightGray))

        if col == 0:
            if role != QtCore.Qt.DisplayRole:
                return None
            else:
                return str(self.messages[row].pk_msg)
        if col == 1:
            if role != QtCore.Qt.DisplayRole:
                return None
            else:
                return str(self.messages[row].msg_date)
        if col == 2:
            if role != QtCore.Qt.DisplayRole:
                return None
            else:
                return str(self.messages[row].contact_from)
        if col == 3:
            if role != QtCore.Qt.DisplayRole:
                return None
            else:
                return self.messages[row].contact_from
        if col == 4:
            mediatype = self.messages[row].get_mediatype()
            if role == QtCore.Qt.DecorationRole:
                if mediatype == MEDIATYPE_IMAGE:
                    path = self.path2media + "/" + self.messages[row].local_url
                    img = QtGui.QImage(path)
                    imgsize = img.size()
                    w = int(imgsize.width()*SCALEFACTOR)
                    h = int(imgsize.height()*SCALEFACTOR)
                    return QtGui.QPixmap(img.scaled(w,h))
            if role == QtCore.Qt.DisplayRole:
                if mediatype == MEDIATYPE_TEXT:
                    return self.messages[row].msg_text
        if col == 5:
            if role != QtCore.Qt.DisplayRole:
                return None
            else:
                return self.messages[row].status
        if col == 6:
            if role != QtCore.Qt.DisplayRole:
                return None
            else:
                return str(self.messages[row].media_wa_type)
        if col == 7:
            if role != QtCore.Qt.DisplayRole:
                return None
            else:
                return self.messages[row].media_size

    def headerData(self, col, orientation, role=QtCore.Qt.DisplayRole):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.header[col]
        return None
###############################

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

###############################
def getContacts(c1):
    contact_list = []
    waphone_list = []
    wa_version = ""

    cmd = "SELECT ZHIGHLIGHTEDNAME FROM ZWACONTACT"
    try:
        c1.execute(cmd)
        wa_version = 1
    except:
        wa_version = 2

    cmd = "SELECT Z_PK, ZABUSERID, ZLASTMODIFIEDDATE, ZFIRSTNAME, ZFULLNAME, ZINDEXNAME FROM ZWACONTACT ORDER BY ZWACONTACT.ZFULLNAME"
    try:
        c1.execute(cmd)
        for c in c1:
            contact = WhatsappContact(c["Z_PK"], c["ZABUSERID"], c["ZLASTMODIFIEDDATE"], c["ZFIRSTNAME"], c["ZFULLNAME"], c["ZINDEXNAME"], wa_version)
            contact_list.append(contact)
        contact = ""
        for contact in contact_list:
            waphone = ""
            waphone_list = []
            cmd = "SELECT ZWAPHONE.Z_PK AS PHONEZPK, ZWAPHONE.ZCONTACT, ZWAPHONE.ZFAVORITE, ZWAPHONE.ZSTATUS, ZWAPHONE.ZLABEL, ZWAPHONE.ZPHONE, ZWAPHONE.ZWHATSAPPID FROM ZWAPHONE WHERE (ZWAPHONE.ZCONTACT="+ str(contact.z_pk)
            c1.execute("SELECT ZWAPHONE.Z_PK AS PHONEZPK, ZWAPHONE.ZCONTACT, ZWAPHONE.ZFAVORITE, ZWAPHONE.ZSTATUS, ZWAPHONE.ZLABEL, ZWAPHONE.ZPHONE, ZWAPHONE.ZWHATSAPPID FROM ZWAPHONE WHERE (ZWAPHONE.ZCONTACT=?)",[str(contact.z_pk)])
            for c in c1:
                waphone = WhatsappPhone(c["PHONEZPK"], c["ZCONTACT"], c["ZFAVORITE"], c["ZSTATUS"], c["ZLABEL"], c["ZPHONE"], c["ZWHATSAPPID"])
                waphone_list.append(waphone)
            #contact.waphone_list = waphone_list
            contact.set_waphonelist(waphone_list)
            if contact.status_zpk != "" and contact.status_zpk is not None:
                c1.execute("SELECT ZCALLABILITY, ZDATE, ZPICTUREDATE, ZPICTUREID, ZPICTUREPATH, ZTEXT FROM ZWASTATUS WHERE (ZWASTATUS.Z_PK=?)",[str(contact.status_zpk)])
                status = c1.fetchone()
                contact.set_zwastatus(status)
        return contact_list
    except sqlite3.Error as msg:
        print('Error: {}'.format(msg))
        return None

def getChatSessions(c1, c2):
    chat_session_list = []
    # gets all the chat sessions
    try:
        c1.execute("SELECT * FROM ZWACHATSESSION")
        for chats in c1:
            try:
                c2.execute("SELECT ZSTATUSTEXT FROM ZWASTATUS WHERE ZCONTACTABID =?;", [chats["ZCONTACTABID"]])
                statustext = c2.fetchone()[0]
            except:
                statustext = None
            curr_chat = WhatsappChatsession(chats["Z_PK"],chats["ZPARTNERNAME"],chats["ZCONTACTJID"],chats["ZMESSAGECOUNTER"],chats["ZUNREADCOUNT"],statustext,chats["ZLASTMESSAGEDATE"])
            chat_session_list.append(curr_chat)
        chat_session_list = sorted(chat_session_list, key=lambda Chatsession: Chatsession.last_message_date, reverse=True)
        return chat_session_list
    except sqlite3.Error as msg:
        print('Error: {}'.format(msg))
        return None

def getChatMessages(c1, c2, chat_session_list):
    # for each chat session, gets all messages
    count_chats = 0
    for chats in chat_session_list:
        count_chats = count_chats + 1
        try:
            c1.execute("SELECT * FROM ZWAMESSAGE WHERE ZCHATSESSION=? ORDER BY Z_PK ASC;", [chats.pk_cs])
            count_messages = 0
            for msgs in c1:
                count_messages = count_messages + 1
                try:
                    if msgs["ZISFROMME"] == 1:
                        contactfrom = "me"
                    else:
                        contactfrom = msgs["ZFROMJID"]
                    if msgs["ZMEDIAITEM"] is None:
                        curr_message = WhatsappMessage(msgs["Z_PK"],msgs["ZISFROMME"],msgs["ZMESSAGEDATE"],msgs["ZTEXT"],contactfrom,msgs["ZMESSAGESTATUS"],None,None,None,None,None,None,None,None,None,None)
                    else:
                        try:
                            messagetext = str(msgs["ZTEXT"])
                        except:
                            messagetext = ""
                        try:
                            c2.execute("SELECT * FROM ZWAMEDIAITEM WHERE Z_PK=?;", [msgs["ZMEDIAITEM"]])
                            media = c2.fetchone()
                            try:
                                movieduration = media["ZMOVIEDURATION"]
                            except:
                                movieduration = 0
                            if movieduration > 0:
                                mediawatype = "3"
                            else:
                                mediawatype = msgs["ZMESSAGETYPE"]
                            try:
                                ZXMPPTHUMBPATH = media["ZXMPPTHUMBPATH"]
                            except:
                                ZXMPPTHUMBPATH = None
                            curr_message = WhatsappMessage(msgs["Z_PK"],msgs["ZISFROMME"],msgs["ZMESSAGEDATE"],msgs["ZTEXT"],contactfrom,msgs["ZMESSAGESTATUS"],media["ZMEDIALOCALPATH"],media["ZMEDIAURL"],None,ZXMPPTHUMBPATH,mediawatype,media["ZFILESIZE"],media["ZLATITUDE"],media["ZLONGITUDE"],media["ZVCARDNAME"],media["ZVCARDSTRING"])
                        except TypeError as msg:
                            print('Error TypeError while reading media message #{} in chat #{}: {}'.format(count_messages, chats.pk_cs, msg) + "\nI guess this means that the media part of this message can't be found in the DB")
                            curr_message = WhatsappMessage(msgs["Z_PK"],msgs["ZISFROMME"],msgs["ZMESSAGEDATE"],messagetext + "<br>MediaMessage_Error: see output in DOS window",contactfrom,msgs["ZMESSAGESTATUS"],None,None,None,None,None,None,None,None,None,None)
                        except sqlite3.Error as msg:
                            print('Error sqlite3.Error while reading media message #{} in chat #{}: {}'.format(count_messages, chats.pk_cs, msg))
                            curr_message = WhatsappMessage(msgs["Z_PK"],msgs["ZISFROMME"],msgs["ZMESSAGEDATE"],messagetext + "<br>MediaMessage_Error: see output in DOS window",contactfrom,msgs["ZMESSAGESTATUS"],None,None,None,None,None,None,None,None,None,None)
                except sqlite3.Error as msg:
                    print('Error while reading message #{} in chat #{}: {}'.format(count_messages, chats.pk_cs, msg))
                    curr_message = WhatsappMessage(None,None,None,"_Error: sqlite3.Error, see output in DOS window",None,None,None,None,None,None,None,None,None,None,None,None)
                except TypeError as msg:
                    print('Error while reading message #{} in chat #{}: {}'.format(count_messages, chats.pk_cs, msg))
                    curr_message = WhatsappMessage(None,None,None,"_Error: TypeError, see output in DOS window",None,None,None,None,None,None,None,None,None,None,None,None)
                chats.msg_list.append(curr_message)
        except sqlite3.Error as msg:
            print('Error sqlite3.Error while reading chat #{}: {}'.format(chats.pk_cs, msg))
            return None
        except TypeError as msg:
            print('Error TypeError while reading chat #{}: {}'.format(chats.pk_cs, msg))
            return None
    return chat_session_list

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
        folder = 'Media/WhatsApp Images/'
        if not date in flistimg:
            flistimg[date] = filelistonce (folder, date)
        flist = flistimg[date]
    elif type == 'AUD':
        folder = 'Media/WhatsApp Audio/'
        if not date in flistaud:
            flistaud[date] = filelistonce (folder, date)
        flist = flistaud[date]
    elif type == 'VID':
        folder = 'Media/WhatsApp Video/'
        if not date in flistvid:
            flistvid[date] = filelistonce (folder, date)
        flist = flistvid[date]
    return folder, flist

def findfile (type, size, localurl, date, additionaldays):
    fname = ''
    fname = "../Extractors/Whatsapp/Library/" + localurl

    return fname

def printHTMLReport(outfile, chat_session_list):
    owner = "WhatsApp-Report"

    outfile = '%s.html' % outfile
    wfile = open(outfile,'wb')
    print ("printing output to "+outfile+" ...")
    # writes page header
    wfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n'.encode('utf-8'))
    wfile.write('"http://www.w3.org/TR/html4/loose.dtd">\n'.encode('utf-8'))
    wfile.write('<html><head><title>{}</title>\n'.format(outfile).encode('utf-8'))
    wfile.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n'.encode('utf-8'))
    wfile.write('<meta name="GENERATOR" content="WhatsApp Xtract v2.0"/>\n'.encode('utf-8'))
    # adds page style
    wfile.write(css_style.encode('utf-8'))

    # adds javascript to make the tables sortable
    wfile.write('\n<script type="text/javascript">\n'.encode('utf-8'))
    wfile.write(popups.encode('utf-8'))
    wfile.write(sortable.encode('utf-8'))
    wfile.write('</script>\n\n'.encode('utf-8'))
    wfile.write('</head><body>\n'.encode('utf-8'))

    # H1 Title
    wfile.write('<h1>iOS Forensics<h1>'.encode('utf-8'))

    # H2 DB Owner
    wfile.write('<a name="top"></a><h2>'.encode('utf-8'))
    wfile.write('WhatsApp'.encode('utf-8'))
    wfile.write('<img src="data/img/whatsapp.png" alt="" '.encode('utf-8'))
    wfile.write('style="width:40px;height:40px;vertical-align:middle"/>'.encode('utf-8'))
    wfile.write('Xtract &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'.encode('utf-8'))
    wfile.write('<img src="data/img/apple.png" alt="" '.encode('utf-8'))
    wfile.write('style="width:35px;height:35px;"/>'.encode('utf-8'))
    wfile.write('&nbsp;{}</h2>\n'.format(owner).encode('utf-8'))

    # writes 1st table header "CHAT SESSION"
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

    # writes 1st table content
    wfile.write('<tbody>\n'.encode('utf-8'))
    for i in chat_session_list:
        if i.contact_name == "N/A":
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
        wfile.write('<td>{}</td>\n'.format(i.pk_cs).encode('utf-8'))
        wfile.write('<td class="contact"><a href="#{}">{}</a></td>\n'.format(i.contact_name,contactname).encode('utf-8'))
        wfile.write('<td class="contact">{}</td>\n'.format(i.contact_id).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(contactstatus).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.contact_msg_count).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.contact_unread_msg).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(lastmessagedate).encode('utf-8'))
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
        wfile.write('<h3>Chat session <a href="#top">#</a> {}: <a name="{}">{}</a></h3>\n'.format(i.pk_cs, i.contact_name, contactname).encode('utf-8'))
        wfile.write('<table class="sortable" id="msg_{}" border="1" cellpadding="2" cellspacing="0">\n'.format(chatid).encode('utf-8'))
        wfile.write('<thead>\n'.encode('utf-8'))
        wfile.write('<tr>\n'.encode('utf-8'))
        wfile.write('<th>PK</th>\n'.encode('utf-8'))
        wfile.write('<th>Chat</th>\n'.encode('utf-8'))
        wfile.write('<th>Msg date</th>\n'.encode('utf-8'))
        wfile.write('<th>From</th>\n'.encode('utf-8'))
        wfile.write('<th>Msg content</th>\n'.encode('utf-8'))
        wfile.write('<th>Msg status</th>\n'.encode('utf-8'))
        wfile.write('<th>Media Type</th>\n'.encode('utf-8'))
        wfile.write('<th>Media Size</th>\n'.encode('utf-8'))
        wfile.write('</tr>\n'.encode('utf-8'))
        wfile.write('</thead>\n'.encode('utf-8'))

        # writes table content
        wfile.write('<tbody>\n'.encode('utf-8'))
        for y in i.msg_list:

            # Determine type of content
            content_type = None
            # IPHONE mode
            # prepare thumb
            if y.media_thumb:
                y.media_thumb = "data:image/jpg;base64,\n" + base64.b64encode(y.media_thumb).decode("utf-8")
            elif y.media_thumb_local_url:
                y.media_thumb = y.media_thumb_local_url
            # Start if Clause
            # GPS
            if y.latitude and y.longitude:
                content_type = CONTENT_GPS
                y.media_wa_type = "5"
                gpsname = None
            # VCARD
            elif y.vcard_string:
                content_type = CONTENT_VCARD
                y.media_wa_type = "4"
            # AUDIO?
            # MEDIA
            elif y.media_url:
                if y.media_thumb:
                    if y.media_wa_type == "3":
                        content_type = CONTENT_VIDEO
                    else:
                        content_type = CONTENT_IMAGE
                        y.media_wa_type = "1"
                    #content_type = CONTENT_MEDIA_THUMB
                else:
                    content_type = CONTENT_MEDIA_NOTHUMB
            # TEXT
            elif y.msg_text is not None:
                content_type = CONTENT_TEXT
                y.media_wa_type = "0"
            # End if Clause

            # row class selection
            if content_type == CONTENT_NEWGROUPNAME:
               wfile.write('<tr class="newgroupname">\n'.encode('utf-8'))
            elif y.from_me == 1:
                wfile.write('<tr class="me">\n'.encode('utf-8'))
            else:
                wfile.write('<tr class="other">\n'.encode('utf-8'))

            # get corresponding contact name for the contact_from of this message:
            if y.contact_from != "me":
                if y.contact_from == i.contact_id: #if sender is identical to chat name
                    y.contact_from = contactname
                else: # for group chats
                    for n in chat_session_list:
                        if n.contact_id == y.contact_from:
                            y.contact_from = convertsmileys ( n.contact_name )

            # PK
            wfile.write('<td>{}</td>\n'.format(y.pk_msg).encode('utf-8'))

            # Chat name
            wfile.write('<td class="contact">{}</td>\n'.format(contactname).encode('utf-8'))
            # Msg date
            wfile.write('<td>{}</td>\n'.format(str(y.msg_date).replace(" ","&nbsp;")).encode('utf-8'))
            # From
            wfile.write('<td class="contact">{}</td>\n'.format(y.contact_from).encode('utf-8'))

            # date elaboration for further use
            date = str(y.msg_date)[:10]
            if date != 'N/A' and date != 'N/A error':
                date = int(date.replace("-",""))

            # Display Msg content (Text/Media)

            if content_type == CONTENT_IMAGE:
                #Search for offline file with current date (+2 days) and known media size
                linkimage = findfile ("IMG", y.media_size, y.local_url, date, 2)
                try:
                    wfile.write('<td class="text"><a onclick="image(this.href);return(false);" target="image" href="{}"><img src="{}" alt="Image"/></a>&nbsp;|&nbsp;<a onclick="image(this.href);return(false);" target="image" href="{}">Image</a>'.format(y.media_url, y.media_thumb, linkimage).encode('utf-8'))
                except:
                    wfile.write('<td class="text">Bild N/A'.encode('utf-8'))
            elif content_type == CONTENT_AUDIO:
                #Search for offline file with current date (+2 days) and known media size
                linkaudio = findfile ("AUD", y.media_size, y.local_url, date, 2)
                try:
                    wfile.write('<td class="text"><a onclick="media(this.href);return(false);" target="media" href="{}">Audio (online)</a>&nbsp;|&nbsp;<a onclick="media(this.href);return(false);" target="media" href="{}">Audio (offline)</a>'.format(y.media_url, linkaudio).encode('utf-8'))
                except:
                    wfile.write('<td class="text">Audio N/A'.encode('utf-8'))
            elif content_type == CONTENT_VIDEO:
                #Search for offline file with current date (+2 days) and known media size
                linkvideo = findfile ("VID", y.media_size, y.local_url, date, 2)
                try:
                    wfile.write('<td class="text"><a onclick="media(this.href);return(false);" target="media" href="{}"><img src="{}" alt="Video"/></a>&nbsp;|&nbsp;<a onclick="media(this.href);return(false);" target="media" href="{}">Video</a>'.format(y.media_url, y.media_thumb, linkvideo).encode('utf-8'))
                except:
                    wfile.write('<td class="text">Video N/A'.encode('utf-8'))
            elif content_type == CONTENT_MEDIA_THUMB:
                #Search for offline file with current date (+2 days) and known media size
                linkmedia = findfile ("MEDIA_THUMB", y.media_size, y.local_url, date, 2)
                try:
                    wfile.write('<td class="text"><a onclick="image(this.href);return(false);" target="image" href="{}"><img src="{}" alt="Media"/></a>&nbsp;|&nbsp;<a onclick="image(this.href);return(false);" target="image" href="{}">Media</a>'.format(y.media_url, y.media_thumb, linkmedia).encode('utf-8'))
                except:
                    wfile.write('<td class="text">Media N/A'.encode('utf-8'))
            elif content_type == CONTENT_MEDIA_NOTHUMB:
                #Search for offline file with current date (+2 days) and known media size
                linkmedia = findfile ("MEDIA_NOTHUMB", y.media_size, y.local_url, date, 2)
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

            # Media size
            wfile.write('<td>{}</td>\n'.format(y.media_size).encode('utf-8'))
            wfile.write('</tr>\n'.encode('utf-8'))

        wfile.write('</tbody>\n'.encode('utf-8'))
        # writes 1st table footer
        wfile.write('</table>\n'.encode('utf-8'))

    # writes page footer
    wfile.write('</body></html>\n'.encode('utf-8'))
    wfile.close()
    print ("done!")
    #END
    webbrowser.open(outfile)

################################################################################
################################################################################
# MAIN
def main(argv):

    chat_session_list = []
    global PYTHON_VERSION

    # parser options
    parser = ArgumentParser(description='Converts a Whatsapp database to HTML.')
    parser.add_argument(dest='infile', 
                       help="'ChatStorage.sqlite' (iPhone) file to scan")
    parser.add_argument('-c', '--contacts', dest='contacts',
                        help="'Contacts.sqlite' (iPhone) contacts database")
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

    msgstore = sqlite3.connect(options.contacts)
    msgstore.row_factory = sqlite3.Row
    c1 = msgstore.cursor()

    contact_list = getContacts(c1)
    msgstore.close()

    # connects to the database(s)
    msgstore = sqlite3.connect(options.infile)
    msgstore.row_factory = sqlite3.Row
    c1 = msgstore.cursor()
    c2 = msgstore.cursor()

    # gets metadata plist info (iphone only)
    try:
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


    chat_session_list = getChatSessions(c1, c2)
    chat_session_list = getChatMessages(c1, c2, chat_session_list)

    outfile = "WhatsApp-Report"
    outfile = '%s.html' % outfile

    printHTMLReport(outfile, chat_session_list)

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

