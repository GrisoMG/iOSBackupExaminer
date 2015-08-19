# -*- coding: utf-8 -*-
'''
Addressbook Xtract v0.1
- Addressbook Extractor for iPhone

Released on MMM DD YYYY
Last Update MMM DD YYYY ()


Tested with Addressbook iOS 6.1.3 - 8.1.3 (iPhone)

Changelog:

V0.1 (created by  - MMM DD, YYY)
- first release, iPhone only:

Usage:

For iPhone DB: 
> python addressbook_xtract.py -a <Addressbook.db>


(C)opyright 2015 GrisoMG

Thanks to
  Fabio Sangiacomo <fabio.sangiacomo@digital-forensics.it>
  Martina Weidner  <martina.weidner@freenet.ch>
'''

import sys, os, webbrowser
from os.path import expanduser
from PySide import QtCore, QtGui
from argparse import ArgumentParser
from iOSForensicClasses import makeTmpDir, get_addressbook
from gui.contacts_form import Ui_frmContacts

class contactsGUI(QtGui.QMainWindow):
    def __init__(self, addressbook=None, addressbookimages=None, work_dir=None):
        QtGui.QMainWindow.__init__(self)

        self.name = "contactsGUI"
        
        if work_dir is not None:
            self.work_dir = work_dir
        else:
            self.work_dir = makeTmpDir()

        self.ui = Ui_frmContacts()
        self.ui.setupUi(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)

        QtCore.QObject.connect(self.ui.treeWidgetContacts, QtCore.SIGNAL("itemSelectionChanged()"), self.onTreeClick)
        QtCore.QObject.connect(self.ui.actionReport, QtCore.SIGNAL("triggered(bool)"), self.printReport)
        QtCore.QObject.connect(self.ui.actionExtract, QtCore.SIGNAL("triggered(bool)"), self.extractApp)

        self.ui.treeWidgetContacts.setHeaderLabel('Contacts')
        self.ui.treeWidgetContacts.setColumnHidden(1, False)
        self.ui.treeWidgetContacts.setColumnHidden(2, False)
        self.ui.treeWidgetContacts.setColumnHidden(3, False)
        self.ui.treeWidgetContacts.setColumnHidden(4, False)
        self.ui.treeWidgetContacts.setColumnHidden(5, False)
        self.ui.treeWidgetContacts.setColumnHidden(6, False)
        self.ui.treeWidgetContacts.setColumnHidden(7, False)
        self.ui.treeWidgetContacts.setColumnHidden(8, False)
        self.ui.treeWidgetContacts.setColumnHidden(9, False)

        self.address_book_list = get_addressbook(addressbook, addressbookimages)
        for contact in self.address_book_list:
            name = ""
            if contact.last_name != "" and contact.last_name is not None:
                name = contact.last_name
            if contact.first_name != "" and contact.first_name is not None:
                if name is not "":
                    name = name + ", " + contact.first_name
                else:
                    name = contact.first_name
            if name == "":
                name = contact.organization

            newItem = QtGui.QTreeWidgetItem(None)
            newItem.setText(0, name)
            newItem.setText(1, contact.rowid)
            newItem.setText(2, contact.last_name)
            newItem.setText(3, contact.first_name)
            newItem.setText(4, contact.organization)
            newItem.setText(5, str(contact.creation_date))
            newItem.setText(6, str(contact.modification_date))
            newItem.setText(7, str(contact.birthday))
            newItem.setText(8, contact.image_url)
            newItem.setText(9, str(contact.multivalue))
            self.ui.treeWidgetContacts.addTopLevelItem(newItem)

    def onTreeClick(self):

        self.ui.listWidgetMulitvalue.clear()
        self.ui.lblLastname.setText('')
        self.ui.lblFirstname.setText('')
        self.ui.lblOrganization.setText('')
        self.ui.lblPicture.setPixmap(None)

        selectedItem = self.ui.treeWidgetContacts.currentItem()

        person = self.getPerson(selectedItem.text(1))

        if person is None:
            return

        self.ui.lblLastname.setText(person.last_name)
        self.ui.lblFirstname.setText(person.first_name)
        self.ui.lblOrganization.setText(person.organization)

        for value in person.multivalue:
            if value != "" and value is not None:
                item = QtGui.QListWidgetItem()
                item.setText(value)
                if person.isMailAddress(value):
                    item.setIcon(QtGui.QIcon('data/img/mail.png'))
                elif person.isURLAddress(value):
                    item.setIcon(QtGui.QIcon('data/img/web.png'))
                elif person.isPhoneNumber(value):
                    item.setIcon(QtGui.QIcon('data/img/phone.png'))

                self.ui.listWidgetMulitvalue.addItem(item)

        if person.has_image:
            pixmap = QtGui.QPixmap(person.image_url)
            self.ui.lblPicture.setPixmap(pixmap)
            self.ui.lblPicture.setScaledContents(True)

    def getPerson(self, rowid):

        for person in self.address_book_list:
            if person.rowid == rowid:
                return person
        return None

    def extractApp(self):
        pass

    def printReport(self):

        path = expanduser("~")
        outdir = QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", path,
                                                            QtGui.QFileDialog.ShowDirsOnly | QtGui.QFileDialog.DontResolveSymlinks);

        if (outdir == None) or (len(outdir) == 0):
            return None

        outfile = outdir + "/AB-Report"
        printHTMLReport(outfile, self.address_book_list)

################################################################################
# Helper Functions
def printHTMLReport(outfile, address_book_list):

    outfile = '%s.html' % outfile
    wfile = open(outfile, 'wb')
    print ("printing output to " + outfile + " ...")
    # writes page header
    wfile.write('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"\n'.encode('utf-8'))
    wfile.write('"http://www.w3.org/TR/html4/loose.dtd">\n'.encode('utf-8'))
    wfile.write('<html><head><title>{}</title>\n'.format(outfile).encode('utf-8'))
    wfile.write('<meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/>\n'.encode('utf-8'))
    wfile.write('<meta name="GENERATOR" content="Addressbook Xtract v0.1"/>\n'.encode('utf-8'))
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
    wfile.write('Addressbook '.encode('utf-8'))
    wfile.write('<img src="data/img/contacts.png" alt="" '.encode('utf-8'))
    wfile.write('style="width:40px;height:40px;vertical-align:middle"/>'.encode('utf-8'))
    wfile.write('Xtract &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'.encode('utf-8'))
    wfile.write('<img src="data/img/apple.png" alt="" '.encode('utf-8'))

    wfile.write('style="width:35px;height:35px;"/>'.encode('utf-8'))
    wfile.write('&nbsp;{}</h2>\n'.format(owner).encode('utf-8'))

    # writes 1st table header
    wfile.write('<table class="sortable" id="lastname" border="1" cellpadding="2" cellspacing="0">\n'.encode('utf-8'))
    wfile.write('<thead>\n'.encode('utf-8'))
    wfile.write('<tr>\n'.encode('utf-8'))
    wfile.write('<th>RowID</th>\n'.encode('utf-8'))
    wfile.write('<th>Lastname</th>\n'.encode('utf-8'))
    wfile.write('<th>Firstname</th>\n'.encode('utf-8'))
    wfile.write('<th>Picture</th>\n'.encode('utf-8'))
    wfile.write('<th>Creationdate</th>\n'.encode('utf-8'))
    wfile.write('<th>Modifikationdate</th>\n'.encode('utf-8'))
    wfile.write('<th>Birthday</th>\n'.encode('utf-8'))
    wfile.write('<th>Values</th>\n'.encode('utf-8'))
    wfile.write('</tr>\n'.encode('utf-8'))
    wfile.write('</thead>\n'.encode('utf-8'))

    # writes 1st table content
    wfile.write('<tbody>\n'.encode('utf-8'))
    for i in address_book_list:
        wfile.write('<tr>\n'.encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.rowid).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.last_name).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.first_name).encode('utf-8'))

        if i.person_has_image() == True:
            try:
                wfile.write(
                    '<td class="text"><a onclick="image(this.href);return(false);" target="image" href="{}"><img src="{}" width="20%" height="20%" alt="Image"/></a>&nbsp;|&nbsp;<a onclick="image(this.href);return(false);" target="image" href="{}">Image</a>'.format(
                        i.image_url, i.image_url, i.image_url).encode('utf-8'))
            except:
                wfile.write('<td class="text">'.encode('utf-8'))
        else:
            wfile.write('<td class="text">'.encode('utf-8'))

        wfile.write('<td>{}</td>\n'.format(str(i.creation_date).replace(" ", "&nbsp;")).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(str(i.modification_date).replace(" ", "&nbsp;")).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(str(i.birthday).replace(" ", "&nbsp;")).encode('utf-8'))
        wfile.write('<td>{}</td>\n'.format(i.get_values_html_formatted()).encode('utf-8'))
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
    address_book_list = []
    global mode
    global PYTHON_VERSION
    global ADDRESSBOOKAVAILABLE
    global ADDRESSBOOKIMAGESAVAILABLE


    # parser options
    parser = ArgumentParser(description='Converts a Addressbook database to HTML.')
    parser.add_argument('-a', '--abdb', dest='abfile',
                        help="input 'Addressbook Database' (iPhone) file to scan")
    parser.add_argument('-p', '--picdb', dest='picfile',
                        help="input 'AddressbookImages Database' (iPhone) file to scan")
    parser.add_argument('-o', '--outfile', dest='outfile',
                        help="optionally choose name of output file")
    options = parser.parse_args()


    # checks for the input file

    if options.abfile is not None:
        if not os.path.exists(options.abfile):
            print('"{}" file is not found!'.format(options.abfile))
            sys.exit(1)

    if options.picfile is not None:
        if not os.path.exists(options.picfile):
            print('"{}" file is not found!'.format(options.picfile))
            sys.exit(1)
        else:
            picfile = options.picfile
    else:
        picfile = ""

    address_book_list = get_addressbook(options.abfile, picfile)

    # check on platform
    mode = IPHONE
    print ("iPhone mode!\n")

    # gets metadata plist info (iphone only)


    # OUTPUT
    if options.outfile is None:
        outfile = "AB-Report"
    else:
        outfile = options.outfile

    printHTMLReport(outfile, address_book_list)

##### GLOBAL variables #####
owner = "Addressbook-Report"
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
    sys.setdefaultencoding("utf-8")
#    import convert_smileys_python_2

mode = None
IPHONE = 1
ANDROID = 2

content_type = None
CONTENT_TEXT = 0
CONTENT_IMAGE = 1
CONTENT_AUDIO = 2
CONTENT_VIDEO = 3
CONTENT_VCARD = 4
CONTENT_GPS = 5
CONTENT_NEWGROUPNAME = 6
CONTENT_MEDIA_THUMB = 7
CONTENT_MEDIA_NOTHUMB = 8
CONTENT_OTHER = 99

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

