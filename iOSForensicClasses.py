# -*- coding: utf-8 -*-
'''
Released on MMM DD YYYY
Last Update MMM DD YYYY ()


Tested with iOS 6.1.3 - 8.1.3 (iPhone)

Changelog:

V0.1 (created by  - MMM DD, YYY)
- first release, iPhone only:

(C)opyright 2015

Released under MIT licence

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

'''

import string, phonenumbers, re, datetime, tempfile, os, magic, sqlite3
# from datetime import datetime

## helper functions
def checkPidFile(pidfile):
    return os.path.exists(pidfile)

def createPidFile(pidfile):
    try:
        with open(pidfile, 'w') as output_file:
            output_file.write("running")
        output_file.close()
        return True
    except:
        return False

def deletePidFile(pidfile):
    try:
        os.remove(pidfile)
        return True
    except:
        return False

def readMagic(item_realpath):

    # check for existence
    if (os.path.exists(item_realpath) == 0):
        return None

    # print file type (from magic numbers)
    filemagic = magic.file(item_realpath)
    return filemagic

def makeTmpDir():
    try:
        tmpdir = tempfile.mkdtemp()
    except:
        tmpdir = ""
    return tmpdir

def rmTmpDir(dir):
    try:
        #os.removedirs(dir)
        shutil.rmtree(dir, ignore_errors=True)
        ret = 1
    except:
        ret = 0
    return ret

def valid_phone(phone):
    """
	Simple validation of phone number.

	It is considered a valid phone number if:
	* It does not contain any letters
	* It does not contain the '@' sign
	* It has at least 3 digits, after stripping all non-numeric digits.

	Returns True if valid, False if not.
	"""
    ret_val = False
    phone_match = re.search('^[^a-zA-Z@]+$', phone)
    if phone_match:
        stripped = strip(phone)
    if len(stripped) >= 3:
        ret_val = True
    return ret_val


def strip(phone):
    """Remove all non-numeric digits in phone string."""
    if phone:
        return re.sub('[^\d]', '', phone)

def formatDurationTime(seconds):

    durationtot = int(seconds)
    durationmin = int(durationtot / 60)
    durationhh = int(durationmin / 60)
    durationmin = durationmin - (durationhh * 60)
    durationsec = durationtot - (durationmin * 60) - (durationhh * 3600)
    duration = "%i:%.2i:%.2i" % (durationhh, durationmin, durationsec)

    return duration

def convertdate(datestring):
    try:
        datestring = str(datestring)
        if datestring.find(".") > -1:  # if timestamp is not like "304966548", but like "306350664.792749", then just use the numbers in front of the "."
            datestring = datestring[:datestring.find(".")]
        return datetime.datetime.fromtimestamp(int(datestring) + 11323 * 60 * 1440)
    except (TypeError, ValueError) as msg:
        print('Error while reading message: {}'.format(msg))
        return "N/A error"

def get_addressbook(addressbook, addressbookimages=None):
    address_book_list = []
    multivalue_list = []

    #print("Open AB database %s" %addressbook)
    msgstore = sqlite3.connect(addressbook)
    msgstore.row_factory = sqlite3.Row
    c1 = msgstore.cursor()

    #tmpdir = makeTmpDir()

    #lookup ABPerson
    try:
        c1.execute(
            "SELECT ROWID, LAST, FIRST, ORGANIZATION, CREATIONDATE, MODIFICATIONDATE, BIRTHDAY, IMAGEURI FROM ABPerson order by LAST, FIRST")
        for person in c1:
            curr_person = ABPerson(person["ROWID"], person["LAST"], person["FIRST"], person["ORGANIZATION"], person["CREATIONDATE"],
                                   person["MODIFICATIONDATE"], person["BIRTHDAY"], person["IMAGEURI"])
            address_book_list.append(curr_person)
    except sqlite3.Error as msg:
        print('Error sqlite3.Error: {}'.format(msg))
        return address_book_list
    except TypeError as msg:
        print('Error TypeError: {}'.format(msg))
        return address_book_list

    #lookup multivalues for ABPerson
    try:
        for person in address_book_list:
            c1.execute("Select value from ABMultivalue where record_id=?;", [person.rowid])
            multivalue_list = []
            for value in c1:
                multivalue_list.append(value["value"])
                person.set_multivalue(multivalue_list)
    except sqlite3.Error as msg:
        print('Error sqlite3.Error: {}'.format(msg))
        return ""
    except TypeError as msg:
        print('Error TypeError: {}'.format(msg))
        return ""

    msgstore.close()

    #lookup person image
    if addressbookimages is not None:
        try:
            if not os.path.exists(addressbookimages):
                print("ABI does not exist...")
            msgstore = sqlite3.connect(addressbookimages)
            msgstore.row_factory = sqlite3.Row
            c1 = msgstore.cursor()

            c1.execute("SELECT name FROM sqlite_master WHERE type='table';")
            #print(c1.fetchall())

            imgdir = makeTmpDir()

            for person in address_book_list:
                if person.has_image == True:
                    c1.execute("Select rowid, record_id, data from ABThumbnailImage where format=0 and record_id=?;", [person.rowid])
                    rowid, record_id, image = c1.fetchone()
                    person.image_url = writeImage(imgdir, str(record_id) + "_" + str(rowid), image)
        except sqlite3.Error as msg:
            print('Error sqlite3.Error: {}'.format(msg))
        except TypeError as msg:
            print('Error TypeError: {}'.format(msg))

    return address_book_list

def writeImage(tmpdir, imgid, image):
    destname = tmpdir + "/" + str(imgid) + ".jpg"
    try:
        with open(destname, 'wb') as output_file:
            output_file.write(image)
    except:
        destname = ""

    return destname

def search_number_in_ab(address_book_list, number):
    ret_val = ""
    for person in address_book_list:
        ret_val = person.has_person_thisnumber(number)
        if ret_val == True:
            ret_val = person.last_name + ", " + person.first_name
            break
    return ret_val

def search_id_in_ab(address_book_list, id):

    ret_val = ""
    for person in address_book_list:
        if person.rowid == id:
            ret_val = person.last_name + ", " + person.first_name
            break

    return ret_val

def iOSCallHistoryVersion(callhistorydb):
    #check if callhistory is < iOS8
    msgstore = sqlite3.connect(callhistorydb)
    msgstore.row_factory = sqlite3.Row
    c1 = msgstore.cursor()
    try:
        c1.execute("Select ROWID FROM call")
        mode = 6
    except:
        try:
            c1.execute("SELECT Z_PK FROM ZCALLRECORD")
            mode = 8
        except:
            mode = "Unknown"
    return mode

class iOS8_CallHistory:
    def __init__(self, zpk, zent, zopt, zanswered, zcalltype, zdisconnected_cause, zface_time_data, znumber_availbility,
                 zoriginated, zread, zdate_timestamp, zduration, zaddress, zdevice_info, ziso_country_code, zname,
                 zunique_id):

        self.contact = ""
        self.direction = ""

        if zpk == "" or zpk is None:
            self.zpk = -1
            self.rowid = -1
        else:
            self.zpk = zpk
            self.rowid = zpk

        if zent == "" or zent is None:
            self.zent = ""
        else:
            self.zent = zent

        if zopt == "" or zopt is None:
            self.zopt = ""
        else:
            self.zopt = zopt

        if zanswered == "" or zanswered is None:
            self.zanswered = ""
        else:
            self.zanswered = zanswered

        if zcalltype == "" or zcalltype is None:
            self.zcalltype = ""
        else:
            self.zcalltype = zcalltype

        if zdisconnected_cause == "" or zdisconnected_cause is None:
            self.zdisconnected_cause = ""
        else:
            self.zdisconnected_cause = zdisconnected_cause

        if zface_time_data == "" or zface_time_data is None:
            self.zface_time_data = ""
        else:
            self.zface_time_data = zface_time_data

        if znumber_availbility == "" or znumber_availbility is None:
            self.znumber_availability = ""
        else:
            self.znumber_availability = znumber_availbility

        if zoriginated == "" or zoriginated is None:
            self.zoriginated = ""
        else:
            self.zoriginated = zoriginated

        if zread == "" or zread is None:
            self.zread = ""
        else:
            self.zread = str(zread)

        if zdate_timestamp == "" or zdate_timestamp is None:
            self.zdate_timestamp = ""
            self.calldate = ""
        else:
            self.zdate_timestamp = convertdate(zdate_timestamp)
            self.calldate = self.zdate_timestamp

        if zduration == "" or zduration is None:
            self.zduration = ""
            self.duration = ""
        else:
            self.zduration = formatDurationTime(zduration)
            self.duration = formatDurationTime(zduration)

        if zaddress == "" or zaddress is None:
            self.zaddress = ""
        else:
            try:
                z = phonenumbers.parse(zaddress, str(ziso_country_code))
                self.zaddress = phonenumbers.format_number(z, phonenumbers.PhoneNumberFormat.E164)
                self.address = self.zaddress
            except:
                self.zaddress = zaddress
                self.address = self.zaddress

        if zdevice_info == "" or zdevice_info is None:
            self.zdevice_info = ""
        else:
            self.zdevice_info = zdevice_info

        if ziso_country_code == "" or ziso_country_code is None:
            self.ziso_country_code = ""
            self.country_code = ""
        else:
            self.ziso_country_code = ziso_country_code
            self.country_code = self.ziso_country_code

        if zname == "" or zname is None:
            self.zname = ""
        else:
            self.zname = zname

        if zunique_id == "" or zunique_id is None:
            self.zunique_id = ""
        else:
            self.zunique_id = zunique_id

    def get_direction(self):
        direction = str(self.zoriginated)

        if direction == "0":
            return "Incomming"
        elif direction == "1":
            return "Outgoing"
        elif direction == "8":
            return "Blocked"
        else:
            return direction

class CallHistory:
    def __init__(self, rowid, address, calldate, duration, flags, contact_id, name, country_code, network_code, read,
                 assisted, face_time_data, originalAddress):

        self.contact = ""
        self.direction = ""

        str(rowid)
        if rowid == "" or rowid is None:
            self.rowid = ""
        else:
            self.rowid = rowid

        if address is "" or address is None:
            self.address = ""
        else:
            self.address = address

        self.calldate = ""
        if calldate == "" or calldate is None:
            self.calldate = ""
        else:
            self.calldate = datetime.datetime.fromtimestamp(int(calldate))

        if duration == "" or duration is None:
            self.duration = ""
        else:
            self.duration = formatDurationTime(duration)

        if flags == "" or flags is None:
            self.flags = ""
        else:
            self.flags = flags

        if contact_id == "" or contact_id is None or str(contact_id) == "-1":
            self.contact_id = ""
        else:
            self.contact_id = str(contact_id)

        if name == "" or name is None:
            self.name = ""
        else:
            self.name = name

        if country_code == "" or country_code is None:
            self.country_code = ""
        else:
            self.country_code = country_code

        if network_code == "" or network_code is None:
            self.network_code = ""
        else:
            self.network_code = network_code

        if read == "" or read is None:
            self.read = ""
        else:
            self.read = read

        if assisted == "" or assisted is None:
            self.assisted = ""
        else:
            self.assisted = assisted

        if face_time_data == "" or face_time_data is None:
            self.face_time_data = ""
        else:
            self.face_time_data = face_time_data

        if originalAddress == "" or originalAddress is None:
            self.originaladdress = ""
        else:
            self.originaladdress = originalAddress

    def get_direction(self):
        direction = str(self.flags)

        if direction == "4":
            return "Incomming"
        elif direction == "5":
            return "Outgoing"
        elif direction == "8":
            return "Blocked"
        else:
            return direction


class ABPerson:
    def __init__(self, rowid, last, first, organization, creationdate, modificationdate, birthday, imageuri):

        self.multivalue = []
        self.image_id = ""
        self.image_url = ""
        self.has_image = False

        rowid = str(rowid)

        if rowid == "" or rowid is None:
            self.rowid = ""
        else:
            self.rowid = rowid

        if last == "" or last is None:
            self.last_name = ""
        else:
            self.last_name = last

        if first == "" or first is None:
            self.first_name = ""
        else:
            self.first_name = first

        if organization == "" or organization is None:
            self.organization = ""
        else:
            self.organization = organization


        self.creation_date = ""
        if creationdate == "" or creationdate is None:
            self.creation_date = ""
        else:
            self.creation_date = convertdate(creationdate)

        self.modification_date = ""
        if modificationdate == "" or modificationdate is None:
            self.modification_date = ""
        else:
            self.modification_date = convertdate(modificationdate)

        self.birthday = ""
        if birthday == "" or birthday is None:
            self.birthday = ""
        else:
            self.birthday = convertdate(birthday)

        self.has_image = False
        if imageuri == "" or imageuri is None:
            self.has_image = False
        else:
            self.has_image = True


    def person_has_image(self):
        return self.has_image

    def has_person_thisnumber(self, number, country_code=None):

        ret_val = False
        if not country_code:
            country_code = "DE"

        try:
            z = phonenumbers.parse(number, country_code)
            number = phonenumbers.format_number(z, phonenumbers.PhoneNumberFormat.E164)
        except:
            number = number

        for value in self.multivalue:
            try:
                z = phonenumbers.parse(value, country_code)
                value = phonenumbers.format_number(z, phonenumbers.PhoneNumberFormat.E164)
                if value == number:
                    ret_val = True
                    break
            except:
                ret_val = False

        return ret_val

    def isMailAddress(self, address):
        if address.find('@') >= 0:
            return True
        else:
            return False

    def isURLAddress(self, url):
        regex = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return url is not None and regex.search(url)

    def isPhoneNumber(self, number):
        a = re.compile("^[#\+0-9]")
        ret = a.match(str(number))
        return ret

    def get_rowid(self):
        return self.rowid

    def set_multivalue(self, multivaluelist):
        mval = []
        for value in multivaluelist:
            try:
                z = phonenumbers.parse(value, phonenumbers.PhoneNumberFormat.E164)
                value = phonenumbers.format_number(z, phonenumbers.PhoneNumberFormat.E164)
            except:
                value = value
            mval.append(value)
        self.multivalue = mval

    def get_person_csv(self):

        ret_val = self.last_name + "; " + self.first_name + "; " + str(self.creation_date) + "; " + str(
            self.modification_date)

        for value in self.multivalue:
            if value is not None:
                ret_val += "; " + str(value).encode('utf-8')

        return ret_val

    def get_values_html_formatted(self):

        ret_val = ""
        for value in self.multivalue:
            try:
                z = phonenumbers.parse(value, phonenumbers.PhoneNumberFormat.E164)
                ret_val += "Tel: " + value + "<br>"
            except:
                if value is None:
                    ret_val += ""
                elif '@' in value:
                    ret_val += "Mail: " + value + "<br>"
                else:
                    ret_val += "Other: " + value + "<br>"
        if ret_val == "":
            ret_val = "N/A"

        return ret_val


    # comparison operator
    def __cmp__(self, other):
        if self.rowid == other.rowid:
            return 0
        return 1


class MSGChat:
    def __init__(self, rowid, chatid, hdlrowid, servicename, state, hdlid, hdlcountry, hdlservice, abcontact):


        # chat session messages
        self.msg_list = []
        self.last_msgdate = ""

        rowid = str(rowid)
        self.msg_count = 0;
        if rowid == "" or rowid is None:
            self.row_id = ""
        else:
            self.row_id = rowid

        chatid = str(chatid)
        if chatid == "" or chatid is None:
            self.chat_id = ""
        else:
            self.chat_id = chatid

        if abcontact == "" or abcontact is None:
            self.ab_contact = ""
        else:
            self.ab_contact = abcontact

        hdlrowid = str(hdlrowid)
        if hdlrowid == "" or hdlrowid is None:
            self.handle_rowid = ""
        else:
            self.handle_rowid = hdlrowid

        if servicename == "" or servicename is None:
            self.service_name = ""
        else:
            self.service_name = servicename

        state = str(state)
        if state == "" or state is None:
            self.state = ""
        else:
            self.state = state

        hdlid = str(hdlid)
        if hdlid == "" or hdlid is None:
            self.handle_id = ""
        else:
            self.handle_id = hdlid

        if hdlcountry == "" or hdlcountry is None:
            self.handle_country = ""
        else:
            self.handle_country = hdlcountry

        if hdlservice == "" or hdlservice is None:
            self.handle_service = ""
        else:
            self.handle_service = hdlservice

    def set_last_msg_date(self, msgdate):

        if self.last_msgdate == "" or self.last_msgdate is None:
            self.last_msgdate = msgdate
        elif self.last_msgdate < msgdate:
            self.last_msgdate = msgdate


class MSGMessage:
    def __init__(self, rowid, date, date_read, isdelivered, isfinished, isread, issent, isfromme, hdlid, msgtext):

        rowid = str(rowid)

        if rowid == "" or rowid is None:
            self.row_id = ""
        else:
            self.row_id = rowid

        fmt_date = self.__convert_date_ios6(date, "%Y-%m-%d %H:%M:%S")
        self.msg_date = ""

        if fmt_date == "" or fmt_date is None:
            self.msg_date = ""
        else:
            self.msg_date = fmt_date

        fmt_date = self.__convert_date_ios6(date_read, "%Y-%m-%d %H:%M:%S")
        self.date_read = ""

        if fmt_date == "" or fmt_date is None:
            self.date_read = ""
        else:
            self.date_read = fmt_date

        isdelivered = str(isdelivered)
        if isdelivered == "" or isdelivered is None:
            self.is_delivered = ""
        else:
            self.is_delivered = isdelivered

        isfinished = str(isfinished)
        if isfinished == "" or isfinished is None:
            self.is_finished = ""
        else:
            self.is_finished = isfinished

        isread = str(isread)
        if isread == "" or isread is None:
            self.is_read = ""
        else:
            self.is_read = isread

        issent = str(issent)
        if issent == "" or issent is None:
            self.is_sent = ""
        else:
            self.is_sent = issent

        fmt_from, fmt_to = self.__convert_address_ios6(hdlid, "Me", isfromme)
        self.contact_from = fmt_from
        self.contact_to = fmt_to

        isfromme = str(isfromme)
        if isfromme == "" or isfromme is None:
            self.is_fromme = ""
        else:
            self.is_fromme = isfromme

        if hdlid == "" or hdlid is None:
            self.handle_id = ""
        else:
            self.handle_id = hdlid

        if msgtext == "" or msgtext is None:
            self.msg_text = ""
        else:
            self.msg_text = msgtext

    def __fix_imessage_date(self, seconds):
        """
		Convert seconds to unix epoch time.

		iMessage dates are not standard unix time.  They begin at midnight on
		2001-01-01, instead of the usual 1970-01-01.

		To convert to unix time, add 978,307,200 seconds!

		Source: http://d.hatena.ne.jp/sak_65536/20111017/1318829688
		(Thanks, Google Translate!)
		"""
        return seconds + 978307200

    def __imessage_date(self, row):
        """
		Return date for iMessage.

		iMessage messages have 2 dates: madrid_date_read and
		madrid_date_delivered. Only one is set for each message, so find the
		non-zero one, fix it so it is standard unix time, and return it.
		"""
        if row['madrid_date_read'] == 0:
            im_date = row['madrid_date_delivered']
        else:
            im_date = row['madrid_date_read']

        return self.__fix_imessage_date(im_date)

    def __convert_date(self, unix_date, format):
        """Convert unix epoch time string to formatted date string."""
        dt = datetime.datetime.fromtimestamp(int(unix_date))
        ds = dt.strftime(format)
        return ds.decode('utf-8')

    def __convert_date_ios6(self, unix_date, format):
        date = self.__fix_imessage_date(unix_date)
        return self.__convert_date(date, format)

    def __convert_address_imessage(self, row, me, alias_map):
        """
		Find the iMessage address in row (a sqlite3.Row) and return a tuple of
		address strings: (from_addr, to_addr).

		In an iMessage message, the address could be an email or a phone number,
		and is found in the `madrid_handle` field.

		Next, look for alias in alias_map.  Otherwise, use formatted address.

		Use `madrid_flags` to determine direction of the message.  (See wiki
		page for Meaning of FLAGS fields discussion.)
		"""

        incoming_flags = (12289, 77825)
        outgoing_flags = (36869, 102405)

        if isinstance(me, str):
            me = me.decode('utf-8')

        # If madrid_handle is phone number, have to truncate it.
        email_match = re.search('@', row['madrid_handle'])
        if email_match:
            handle = row['madrid_handle']
        else:
            handle = trunc(row['madrid_handle'])

        if handle in alias_map:
            other = alias_map[handle]
        else:
            other = format_address(row['madrid_handle'])

        if row['madrid_flags'] in incoming_flags:
            from_addr = other
            to_addr = me
        elif row['madrid_flags'] in outgoing_flags:
            from_addr = me
            to_addr = other

        return (from_addr, to_addr)

    def __convert_address_sms(self, row, me, alias_map):
        """
		Find the sms address in row (a sqlite3.Row) and return a tuple of address
		strings: (from_addr, to_addr).

		In an SMS message, the address is always a phone number and is found in
		the `address` field.

		Next, look for alias in alias_map.  Otherwise, use formatted address.

		Use `flags` to determine direction of the message:
		2 = 'incoming'
		3 = 'outgoing'
		"""

        if isinstance(me, str):
            me = me.decode('utf-8')

        tr_address = trunc(row['address'])
        if tr_address in alias_map:
            other = alias_map[tr_address]
        else:
            other = format_phone(row['address'])

        if row['flags'] == 2:
            from_addr = other
            to_addr = me
        elif row['flags'] == 3:
            from_addr = me
            to_addr = other

        return (from_addr, to_addr)

    def __convert_address_ios6(self, hdlid, me, isfromme):

        if isinstance(me, str):
            me = me.decode('utf-8')

        address = hdlid

        # Truncate phone numbers, not email addresses.
        # m = re.search('@', address)
        # if not m:
        # address = trunc(address)

        if isfromme:
            from_addr = me
            to_addr = address
        else:
            from_addr = address
            to_addr = me

        return (from_addr, to_addr)

        def __clean_text_msg(txt):
            """
			Return cleaned-up text message.

			1. Replace None with ''.
			2. Replace carriage returns (sent by some phones) with '\n'.
			"""
            txt = txt or ''
            return txt.replace("\015", "\n")

################################################################################
# Threema Contact obj definition
class ThreemaContact:
    def __init__(self, zpk, abrecordid, featurelevel, state, verificationlevel, firstname, identity, lastname, nickname, verifiedemail, verifiedmobile, imagedata, pubkey, convid, numofmsgs, lastmsgid, lastmsgdate):

        if convid == "" or convid is None:
            self.conversation_id = ""
        else:
            self.conversation_id = convid

        if numofmsgs == "" or numofmsgs is None:
            self.numberofmessages = ""
        else:
            self.numberofmessages = numofmsgs

        if lastmsgid == "" or lastmsgid is None:
            self.lastmessageid = ""
        else:
            self.lastmessageid = lastmsgid

        if lastmsgdate == "" or lastmsgdate is None:
            self.last_message_date = ""
        else:
            self.last_message_date = convertdate(lastmsgdate)

        if zpk == "" or zpk is None:
            self.zpk = ""
        else:
            self.zpk = zpk

        if abrecordid == "" or abrecordid is None:
            self.abrecordid = ""
        else:
            self.abrecordid = abrecordid

        if featurelevel == "" or featurelevel is None:
            self.featurelevel = ""
        else:
            self.featurelevel = featurelevel

        if state == "" or state is None:
            self.state = ""
        else:
            self.state = state

        if verificationlevel == "" or verificationlevel is None:
            self.verificationlevel = ""
        else:
            self.verificationlevel = verificationlevel

        if firstname == "" or firstname is None:
            self.firstname = ""
        else:
            self.firstname = firstname

        if identity == "" or identity is None:
            self.identity = ""
        else:
            self.identity = identity

        if lastname == "" or lastname is None:
            self.lastname = ""
        else:
            self.lastname = lastname

        if nickname == "" or nickname is None:
            self.nickname = ""
        else:
            self.nickname = nickname

        if self.lastname != "" and self.firstname != "":
            self.contact_name = self.lastname + ", " + self.firstname
        elif self.lastname != "":
            self.contact_name = self.lastname
        elif self.firstname != "":
            self.contact_name = self.firstname
        elif self.nickname != "":
            self.contact_name = self.nickname
        else:
            self.contact_name = self.identity


        if verifiedemail == "" or verifiedemail is None:
            self.verifiedemail = ""
        else:
            self.verifiedemail = verifiedemail

        if verifiedmobile == "" or verifiedmobile is None:
            self.verifiedmobile = ""
        else:
            self.verifiedmobile = verifiedmobile

        if imagedata == "" or imagedata is None:
            self.imagedata = ""
            self.imageurl = ""
            self.has_image = False
        else:
            self.imagedata = imagedata
            self.imageurl = ""
            self.has_image = True

        if pubkey == "" or pubkey is None:
            self.pubkey = ""
        else:
            self.pubkey = pubkey

    def set_lastmsg_date(self, lastmsgdate):

        if lastmsgdate == "" or lastmsgdate is None or lastmsgdate == 0:
            self.last_message_date = " N/A"  # space is necessary for that the empty chats are placed at the end on sorting
        else:
            self.last_message_date = convertdate(lastmsgdate)


    # comparison operator
    def __cmp__(self, other):
        if self.zkp == other.zpk:
            return 0
        return 1

################################################################################
# Threema Group obj definition

################################################################################
# Threema Chatsession obj definition
class ThreemaChatsession:
    # init
    def __init__(self, lastmsg, contactid, zpk, firstname, lastname, identity, nickname, msgtext, lastmsgdate, fromme, groupname, group_id,
                 unreadmsgcnt, status, msgcount):


        # if invalid params are passed, sets attributes to invalid values

        self.media_wa_type = "N/A"

        # lastmessage id
        if lastmsg == "" or lastmsg is None:
            self.lastmsg_id = -1
        else:
            self.lastmsg_id = lastmsg

        # unread msg
        if unreadmsgcnt == "" or unreadmsgcnt is None:
            self.contact_unread_msg = "N/A"
        else:
            self.contact_unread_msg = unreadmsgcnt

        # contact id
        if contactid == "" or contactid is None:
            self.contact_id = "N/A"
        else:
            self.contact_id = contactid

        # primary key
        if zpk == "" or zpk is None:
            self.zpk = -1
        else:
            self.zpk = zpk

        # isown
        if fromme == "" or fromme is None:
            self.isown = "N/A"
        else:
            self.isown = fromme

        # contact firstname
        if firstname == "" or firstname is None:
            self.contact_firstname = ""
        else:
            self.contact_firstname = firstname

        # contact lastname
        if lastname == "" or lastname is None:
            self.contact_lastname = ""
        else:
            self.contact_lastname = lastname

        if identity == "" or identity is None:
            self.identity = ""
        else:
            self.identity = identity

        if nickname == "" or nickname is None:
            self.nickname = ""
        else:
            self.nickname = nickname

        if self.contact_lastname != "" and self.contact_firstname != "":
            self.contact_name = self.contact_lastname + ", " + self.contact_firstname
        elif self.contact_lastname != "":
            self.contact_name = self.contact_lastname
        elif self.contact_firstname != "":
            self.contact_name = self.contact_firstname
        elif self.nickname != "":
            self.contact_name = self.nickname
        else:
            self.contact_name = self.identity


        if status == "" or status is None:
            self.contact_status = "N/A"
        else:
            self.contact_status = status

        # groupname
        if groupname == "" or groupname is None:
            self.group_name = ""
        else:
            self.group_name = groupname

        # group id
        if group_id == "" or group_id is None:
            self.group_id = ""
        else:
            self.group_id = group_id
            if self.group_name == "":
                self.group_name = "no group name"

        # text of last message
        if msgtext == "" or msgtext is None:
            self.msg_text = None
        else:
            self.msg_text = msgtext

        self.last_message_date = ""
        # contact last message date
        if lastmsgdate == "" or lastmsgdate is None or lastmsgdate == 0:
            self.last_message_date = " N/A"  # space is necessary for that the empty chats are placed at the end on sorting
        else:
            self.last_message_date = convertdate(lastmsgdate)

        if msgcount == "" or msgcount is None:
            self.msg_count = "N/A"
        else:
            self.msg_count = msgcount

        # chat session messages
        self.msg_list = []

    # comparison operator
    def __cmp__(self, other):
        if self.zkp == other.zpk:
            return 0
        return 1

################################################################################
# Threema Message obj definition

class ThreemaMessage:
    # init
    def __init__(self, pkmsg, fromme, msgdate, text, contactfrom, lastname, firstname, nickname, msgstatus,
                 imgid, imagesize, imgthumbid, audioid, videoid, videosize, deliverydate, readdate, latitude, longitude,
                 thumb_nail):


        self.media_wa_type = "N/A"
        self.contact_from = ""
        # if invalid params are passed, sets attributes to invalid values
        # primary key
        if pkmsg == "" or pkmsg is None:
            self.zpk = -1
        else:
            self.zpk = pkmsg

        # "from me" flag
        if fromme == 0  or fromme == "" or fromme is None:
            self.from_me = -1
        else:
            self.from_me = fromme

        # message timestamp
        if msgdate == "" or msgdate is None or msgdate == 0:
            self.msg_date = "N/A"
        else:
            self.msg_date = convertdate(msgdate)

        # message text
        if text == "" or text is None:
            self.msg_text = None
        else:
            self.msg_text = text
            self.media_wa_type = "Text"

        # contact firstname
        if firstname == "" or firstname is None:
            self.contact_firstname = ""
        else:
            self.contact_firstname = firstname

        # contact lastname
        if lastname == "" or lastname is None:
            self.contact_lastname = ""
        else:
            self.contact_lastname = lastname

        if nickname == "" or nickname is None:
            self.nickname = ""
        else:
            self.nickname = nickname

        if self.contact_lastname != "" and self.contact_firstname != "":
            self.contact_from = self.contact_lastname + ", " + self.contact_firstname
        elif self.contact_lastname != "":
            self.contact_from = self.contact_lastname
        elif self.contact_firstname != "":
            self.contact_from = self.contact_firstname
        elif self.nickname != "":
            self.contact_from = nickname
        else:
            self.contact_from = contactfrom


        # status
        if msgstatus == "" or msgstatus is None:
            self.status = "N/A"
        else:
            self.status = msgstatus


        # media
        if imgid == "" or imgid is None:
            self.image_id = ""
            self.image_url = ""
        else:
            self.image_id = imgid
            self.image_url = ""
            self.media_wa_type = "Image"

        if imagesize == "" or imagesize is None:
            self.image_size = 0
        else:
            self.image_size = imagesize

        if imgthumbid == "" or imgthumbid is None:
            self.imgthumb_id = ""
            self.thumbnail_url = ""
        else:
            self.imgthumb_id = imgthumbid
            self.thumbnail_url = thumb_nail
            self.media_wa_type = "Image"

        if audioid == "" or audioid is None:
            self.audio_id = ""
        else:
            self.audio_id = audioid
            self.audio_url = ""
            self.media_wa_type = "Audio"

        if videoid == "" or videoid is None:
            self.video_id = ""
        else:
            self.video_id = videoid
            self.video_url = ""
            self.media_wa_type = "Video"

        if videosize == "" or videosize is None:
            self.video_size = ""
        else:
            self.video_size = videosize

        if deliverydate == "" or deliverydate is None:
            self.delivery_date = ""
        else:
            self.delivery_date = convertdate(deliverydate)


        if readdate == "" or readdate is None:
            self.read_date = ""
        else:
            self.read_date = convertdate(readdate)


        # GPS
        if latitude == "" or latitude is None:
            self.latitude = ""
        else:
            self.latitude = latitude
        if longitude == "" or longitude is None:
            self.longitude = ""
        else:
            self.longitude = longitude

    # comparison operator
    def __cmp__(self, other):
        if self.zpk == other.zpk:
            return 0
        return 1


################################################################################
# Whatsapp Contact obj definition
class WhatsappContact():
    def __init__(self, z_pk, zabuserid, zlastmodifieddate, zfirstname, zfullname, zindexname, wa_version=None):

        if z_pk == "" or z_pk is None:
            self.z_pk = ""
        else:
            self.z_pk = str(z_pk)

        if zabuserid == "" or zabuserid is None:
            self.zabuserid = ""
        else:
            self.zabuserid = str(zabuserid)

        if zlastmodifieddate == "" or zlastmodifieddate is None:
            self.zlastmodifieddate = ""
        else:
            self.zlastmodifieddate = convertdate(zlastmodifieddate)

        if zfirstname == "" or zfirstname is None:
            self.zfirstname = ""
        else:
            self.zfirstname = zfirstname

        if zfullname == "" or zfullname is None:
            self.zfullname = ""
        else:
            self.zfullname = zfullname

        if zindexname == "" or zindexname is None:
            self.zindexname = ""
        else:
            self.zindexname = zindexname

        self.favorite_zpk = ""
        self.status_zpk = ""
        self.zcallability = ""
        self.zdate = ""
        self.zpicturedate = ""
        self.zpictureid = ""
        self.zpicturepath = ""
        self.ztext = ""

        self.picture = ""
        self.waphone_list = []

        if wa_version == "" or wa_version is None:
            self.wa_version = 0
        else:
            self.wa_version = wa_version

    def set_waphonelist(self, waphonelist):
        self.waphone_list = waphonelist
        for phone in waphonelist:
            if phone.zfavorite != "" and phone.zfavorite is not None:
                self.favorite_zpk = str(phone.zfavorite)
            if phone.zstatus != "" and phone.zstatus is not None:
                self.status_zpk = str(phone.zstatus)

    def set_zwastatus(self, status):
        if status["ZCALLABILITY"] == "" or status["ZCALLABILITY"] is None:
            self.zcallability = ""
        else:
            self.zcallability = str(status["ZCALLABILITY"])

        if status["ZDATE"] == "" or status["ZDATE"] is None:
            self.zdate = ""
        else:
            self.zdate = convertdate(status["ZDATE"])

        if status["ZPICTUREDATE"] == "" or status["ZPICTUREDATE"] is None:
            self.zpicturedate = ""
        else:
            self.zpicturedate = convertdate(status["ZPICTUREDATE"])

        if status["ZPICTUREID"] == "" or status["ZPICTUREID"] is None:
            self.zpictureid = ""
        else:
            self.zpictureid = status["ZPICTUREID"]

        if status["ZPICTUREPATH"] == "" or status["ZPICTUREPATH"] is None:
            self.zpicturepath = ""
        else:
            self.zpicturepath = status["ZPICTUREPATH"]

        if status["ZTEXT"] == "" or status["ZTEXT"] is None:
            self.ztext = ""
        else:
            self.ztext = status["ZTEXT"]

    def set_zdate(self, zdate):
        if zdate == "" or zdate is None:
            return False
        try:
            self.zdate = convertdate(zdate)
            return True
        except:
            return False

    def contact_haspicture(self):
        if self.zpictureid != "" or self.zpicturepath != "":
            return True
        else:
            return False

    # comparison operator
    def __cmp__(self, other):
        if self.z_kp == other.z_pk:
            return 0
        return 1

class WhatsappPhone:
    def __init__(self, phonezbk, zcontact, zfavorite, zstatus, zlabel, zphone, zwhatsappid):

            #table zphone
        if phonezbk == "" or phonezbk is None:
            self.phonezbk = ""
        else:
            self.phonezbk = str(phonezbk)

        if zcontact == "" or zcontact is None:
            self.zcontact = ""
        else:
            self.zcontact = str(zcontact)

        if zfavorite == "" or zfavorite is None:
            self.zfavorite = ""
        else:
            self.zfavorite = str(zfavorite)

        if zstatus == "" or zstatus is None:
            self.zstatus = ""
        else:
            self.zstatus = str(zstatus)

        if zlabel == "" or zlabel is None:
            self.zlabel = ""
        else:
            self.zlabel = self.clean_zlabel(zlabel)

        if zphone == "" or zphone is None:
            self.zphone = ""
        else:
            self.zphone = zphone

        if zwhatsappid == "" or zwhatsappid is None:
            self.zwhatsappid = ""
        else:
            self.zwhatsappid = zwhatsappid

    def clean_zlabel(self, zlabel):
        if zlabel == "" or zlabel is None:
            return zlabel
        zlabel = zlabel.replace("_$!<", "")
        zlabel = zlabel.replace(">!$_", "")
        return zlabel

    def get_zwastatus_zpk(self):
        if self.zstatus == "" or self.zstatus is None:
            return ""
        else:
            return self.zstatus

    def get_zfavorite_zpk(self):
        if self.zfavorite == "" or self.zfavorite is None:
            return ""
        else:
            return self.zfavorite

    # comparison operator
    def __cmp__(self, other):
        if self.phonezbk == other.phonezpk:
            return 0
        return 1
################################################################################
# Whatsapp Chatsession obj definition
class WhatsappChatsession:

    # init
    def __init__(self,pkcs,contactname,contactid,
                 contactmsgcount,contactunread,contactstatus,lastmessagedate):

        # if invalid params are passed, sets attributes to invalid values
        # primary key
        if pkcs == "" or pkcs is None:
            self.pk_cs = -1
        else:
            self.pk_cs = pkcs

        # contact nick
        if contactname == "" or contactname is None:
            self.contact_name = "N/A"
        else:
            self.contact_name = contactname

        # contact id
        if contactid == "" or contactid is None:
            self.contact_id = "N/A"
        else:
            self.contact_id = contactid

        # contact msg counter
        if contactmsgcount == "" or contactmsgcount is None:
            self.contact_msg_count = "N/A"
        else:
            self.contact_msg_count = contactmsgcount

        # contact unread msg
        if contactunread == "" or contactunread is None:
            self.contact_unread_msg = "N/A"
        else:
            self.contact_unread_msg = contactunread

        # contact status
        if contactstatus == "" or contactstatus is None:
            self.contact_status = "N/A"
        else:
            self.contact_status = contactstatus

        # contact last message date
        if lastmessagedate == "" or lastmessagedate is None or lastmessagedate == 0:
            self.last_message_date = " N/A" #space is necessary for that the empty chats are placed at the end on sorting
        else:
            try:
                lastmessagedate = str(lastmessagedate)
                if lastmessagedate.find(".") > -1: #if timestamp is not like "304966548", but like "306350664.792749", then just use the numbers in front of the "."
                    lastmessagedate = lastmessagedate[:lastmessagedate.find(".")]
                self.last_message_date = datetime.datetime.fromtimestamp(int(lastmessagedate)+11323*60*1440)
                self.last_message_date = str( self.last_message_date )
            except (TypeError, ValueError) as msg:
                print('Error while reading chat #{}: {}'.format(self.pk_cs,msg))
                self.last_message_date = " N/A error"

        # chat session messages
        self.msg_list = []

    # comparison operator
    def __cmp__(self, other):
        if self.pk_cs == other.pk_cs:
                return 0
        return 1

################################################################################
# Whatsapp Message obj definition
class WhatsappMessage:

    # init
    def __init__(self,pkmsg,fromme,msgdate,text,contactfrom,msgstatus,
                 localurl, mediaurl,mediathumb,mediathumblocalurl,mediawatype,mediasize,latitude,longitude,vcardname,vcardstring):


        # if invalid params are passed, sets attributes to invalid values
        # primary key
        if pkmsg == "" or pkmsg is None:
            self.pk_msg = -1
        else:
            self.pk_msg = pkmsg

        # "from me" flag
        if fromme == "" or fromme is None:
            self.from_me = -1
        else:
            self.from_me = fromme

        # message timestamp
        if msgdate == "" or msgdate is None or msgdate == 0:
            self.msg_date = "N/A"
        else:
            try:
                msgdate = str(msgdate)
                if msgdate.find(".") > -1: #if timestamp is not like "304966548", but like "306350664.792749", then just use the numbers in front of the "."
                    msgdate = msgdate[:msgdate.find(".")]
                self.msg_date = datetime.datetime.fromtimestamp(int(msgdate)+11323*60*1440)
            except (TypeError, ValueError) as msg:
                print('Error while reading message #{}: {}'.format(self.pk_msg,msg))
                self.msg_date = "N/A error"

        # message text
        if text == "" or text is None:
            self.msg_text = "N/A"
        else:
            self.msg_text = text
        # contact from
        if contactfrom == "" or contactfrom is None:
            self.contact_from = "N/A"
        else:
            self.contact_from = contactfrom

        # media
        if localurl == "" or localurl is None:
            self.local_url = ""
        else:
            self.local_url = localurl
        if mediaurl == "" or mediaurl is None:
            self.media_url = ""
        else:
            self.media_url = mediaurl
        if mediathumb == "" or mediathumb is None:
            self.media_thumb = ""
        else:
            self.media_thumb = mediathumb
        if mediathumblocalurl == "" or mediathumblocalurl is None:
            self.media_thumb_local_url = ""
        else:
            self.media_thumb_local_url = mediathumblocalurl
        if mediawatype == "" or mediawatype is None:
            self.media_wa_type = ""
        else:
            self.media_wa_type = mediawatype
        if mediasize == "" or mediasize is None:
            self.media_size = ""
        else:
            self.media_size = mediasize

        #status
        if msgstatus == "" or msgstatus is None:
            self.status = "N/A"
        else:
            self.status = msgstatus

        #GPS
        if latitude == "" or latitude is None:
            self.latitude = ""
        else:
            self.latitude = latitude
        if longitude == "" or longitude is None:
            self.longitude = ""
        else:
            self.longitude = longitude

        #VCARD
        if vcardname == "" or vcardname is None:
            self.vcard_name = ""
        else:
            self.vcard_name = vcardname
        if vcardstring == "" or vcardstring is None:
            self.vcard_string = ""
        else:
            self.vcard_string = vcardstring

    def get_mediatype(self):
        if self.media_wa_type == '' or self.media_wa_type is None:
            mediatype = 0
        else:
            mediatype = int(self.media_wa_type)

        MEDIATYPE_TEXT  = 0
        MEDIATYPE_IMAGE = 1
        MEDIATYPE_VIDEO = 3

        if mediatype == MEDIATYPE_IMAGE:
            return MEDIATYPE_IMAGE
        elif mediatype == MEDIATYPE_VIDEO:
            return MEDIATYPE_VIDEO
        else:
            return MEDIATYPE_TEXT

    # comparison operator
    def __cmp__(self, other):
        if self.pk_msg == other.pk_msg:
                return 0
        return 1
