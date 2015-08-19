#!/usr/bin/python
# coding=utf-8
#
#
#
'''
backup_tool.py and corresponding python scripts (backups, crypto, keystore and util) are from the
iphone-data-protection project: https://code.google.com/p/iphone-dataprotection/

'''
from backups.backup3 import decrypt_backup3
from backups.backup4 import MBDB
from keystore.keybag import Keybag
from util import readPlist, makedirs
from backups.backup4 import MBFileRecordFromDB
from iOSForensicClasses import makeTmpDir
import getpass
from argparse import ArgumentParser
import os
import sys
import plistlib
import sqlite3


showinfo = ["Device Name", "Display Name", "Last Backup Date", "IMEI",
            "Serial Number", "Product Type", "Product Version", "iTunes Version"]

ios8_defaultapps = ["Accounts", "AddressBook", "Calendar", "CallHistoryDB", "Mail", "Notes", "Passes", "SMS", "Safari", "Voicemail"]

def getIDeviceProductName(product_type):
    """
    Given an iDevice "Product Type" (e.g. "iPhone3,1") returns the product name (e.g. "iPhone 4").
    Returns "Unknown Model (type)" if the model is not recognized.
    """
    types = {"iPad1,1": "iPad 1",
             "iPad2,1": "iPad 2",
             "iPad2,2": "iPad 2",
             "iPad2,3": "iPad 2",
             "iPad2,4": "iPad 2",
             "iPad3,1": "iPad 3",
             "iPad3,3": "iPad 3",
             "iPad3,2": "iPad 3",
             "iPad3,4": "iPad 4",
             "iPad2,5": "iPad mini",
             "iPad2,6": "iPad mini",
             "iPad2,7": "iPad mini",
             "iPhone1,1": "iPhone 1",
             "iPhone1,2": "iPhone 3G",
             "iPhone2,1": "iPhone 3GS",
             "iPhone3,1": "iPhone 4",
             "iPhone3,3": "iPhone 4",
             "iPhone4,1": "iPhone 4S",
             "iPhone5,1": "iPhone 5",
             "iPhone5,2": "iPhone 5",
             "iPhone6,1": "iPhone 5S",
             "iPhone7,2": "iPhone 6",
             "iPod1,1": "iPod touch 1",
             "iPod2,1": "iPod touch 2",
             "iPod3,1": "iPod touch 3",
             "iPod4,1": "iPod touch 4",
             "iPod5,1": "iPod touch 5"}

    if product_type in types:
        return types[product_type]

    return "Unknown Model (%s)" % (product_type)

def readManifest(backup_path):
    if not os.path.exists(backup_path + "/Manifest.plist"):
        return None
    manifest = readPlist(backup_path + "/Manifest.plist")
    return manifest

def readInfo(backup_path):
    if not os.path.exists(backup_path + "/Info.plist"):
        #print "Manifest.plist not found"
        return None
    info = readPlist(backup_path + "/Info.plist")
    return info


def extract_backup(backup_path, output_path, password="", app=None):
    '''
    if not os.path.exists(backup_path + "/Manifest.plist"):
        print "Manifest.plist not found"
        return
    manifest = readPlist(backup_path + "/Manifest.plist")
    '''
    manifest = readManifest(backup_path)
    if manifest is None:
        print("Manifest.plist not found")
        return

#    dict = manifest['Applications']
#    for apps in dict.iteritems():
#        print "App Name: " + apps[0]
#        for key, value in apps[1].iteritems():
#            print key + " : " + value
#        print "####################################"

    showinfo = readInfo(backup_path)
    if showinfo is None:
        print("Info.plist not found")
        return
    for i in showinfo:
        value = unicode(showinfo.get(i, "missing"))
        if i == "Product Type":
            value = value + " (" + getIDeviceProductName(value) + ")"
        print(i + " : " + value + "...")

#    print "Extract backup to %s ? (y/n)" % output_path
#    if raw_input() == "n":
#        return

    print("Backup is %sencrypted" % (int(not manifest["IsEncrypted"]) * "not "))

    if manifest["IsEncrypted"] and password == "":
        print ("Enter backup password : ")
        password = getpass.getpass()

    if not manifest.has_key("BackupKeyBag"):
        print ("No BackupKeyBag in manifest, assuming iOS 3.x backup")
        decrypt_backup3(backup_path, output_path, password)
    else:
        mbdb = MBDB(backup_path)

        kb = Keybag.createWithBackupManifest(manifest, password)
        if not kb:
            return
        manifest["password"] = password
        makedirs(output_path)
        plistlib.writePlist(manifest, output_path + "/Manifest.plist")

        mbdb.keybag = kb

        database, cursor = iOSBackupDB()


        store2db(cursor, mbdb)
        database.commit()
        print_domains(cursor)
        cursor.execute("Select * from indice where mbapp_name= ?", (app,))
        records = cursor.fetchall()
        for record in records:
            dbrecord = MBFileRecordFromDB(record)
            mbdb.extract_backup_from_db(dbrecord, output_path)

        #mbdb.extract_backup(output_path)

def iOSBackupDB(dbname=None):
    if dbname is None:
        database = sqlite3.connect(':memory:')  # Create a database file in memory
    else:
        try:
            try:
                os.remove(dbname)
            except OSError:
                pass
            database = sqlite3.connect(dbname)
        except:
            print ("Could not create database %s" %dbname)
            return None, None

    database.row_factory = sqlite3.Row
    database.text_factory = str
    cursor = database.cursor()  # Create a cursor

    cursor.execute(
        "CREATE TABLE indice (" +
        "id INTEGER PRIMARY KEY AUTOINCREMENT," +
        "domain VARCHAR(100)," +
        "path VARCHAR(100)," +
        "target VARCHAR(100)," +
        "digest VARCHAR(100)," +
        "encryption_key BLOB,"
        "mode INT," +
        "inode_number INT," +
        "user_id VARCHAR(8)," +
        "group_id VARCHAR(8)," +
        "mtime INT," +
        "atime INT," +
        "ctime INT," +
        "size INT," +
        "protection_class INT,"
        "num_attributes INT," +
        "extended_attributes BLOB,"
        "fileid VARCHAR(50)," +
        "mbdomain_type VARCHAR(100)," +
        "mbapp_name VARCHAR(100)," +
        "mbfile_name VARCHAR(100)," +
        "mbfile_path VARCHAR(100)," +
        "mbfile_rights VARCHAR(1)," +
        "mbfile_type VARCHAR(1)," +
        "mbdata_hash VARCHAR(100)"
        ");"
    )

    cursor.execute(
        "CREATE TABLE properties (" +
        "id INTEGER PRIMARY KEY AUTOINCREMENT," +
        "file_id INTEGER," +
        "property_name VARCHAR(100)," +
        "property_val VARCHAR(100)" +
        ");"
    )

    return database, cursor


def print_domains(cursor):
    # retrieve domain families
    cursor.execute("SELECT DISTINCT(mbdomain_type) FROM indice")
    domain_types = cursor.fetchall()

    for domain_type_u in domain_types:
        domain_type = str(domain_type_u[0])
        print (domain_type)

        # retrieve domains for the selected family
        query = "SELECT DISTINCT(mbapp_name) FROM indice WHERE mbdomain_type = ? ORDER BY mbdomain_type"
        cursor.execute(query, (domain_type,))
        domain_names = cursor.fetchall()

        for domain_name_u in domain_names:
            domain_name = str(domain_name_u[0])
            if domain_name != "":
                print ("\t" + domain_name)

            # retrieve paths for selected domain
            query = "SELECT path, mbfile_path, mbfile_name, size, fileid, mbfile_type FROM indice WHERE mbdomain_type = ? AND mbapp_name = ? ORDER BY mbfile_path, mbfile_name"
            cursor.execute(query, (domain_type, domain_name))
            nodes = cursor.fetchall()

            for nodeData in nodes:
                path = str(nodeData[0])

                if path != "":
                    if path.find('/') == -1:
                        print "\t\t" + path
                    else:
                        print "\t\t\t" + path
######

#### Store Manifest.mbdb data in sqlite3 DB
def modestr(val):
    def mode(val):
        if (val & 0x4): r = 'r'
        else: r = '-'
        if (val & 0x2): w = 'w'
        else: w = '-'
        if (val & 0x1): x = 'x'
        else: x = '-'
        return r+w+x
    return mode(val>>6) + mode((val>>3)) + mode(val)

def filetype(val):
    ret = ""
    # decoding element type (symlink, file, directory)
    if (val & 0xE000) == 0xA000:
        ret = 'l'  # symlink
    elif (val & 0xE000) == 0x8000:
        ret = '-'  # file
    elif (val & 0xE000) == 0x4000:
        ret = 'd'  # dir
    return ret

def hex2nums(src):
    return ' '.join(["%02X" % ord(x) for x in src])

def store2db(cursor, mbdb):
    dbcursor = cursor
    for key, value in mbdb.files.iteritems():

        if value.domain is None:
            domain = ""
            mb_domain = ""
            mbapp_name = ""
            dapp_name = ""
            dpath = ""
        else:
            domain = value.domain
            # separates domain type (AppDomain, HomeDomain, ...) from domain name
            mbdomain_type, sep, mbapp_name = value.domain.partition('-')
            if (mbdomain_type == "AppDomain") or (mbdomain_type == "AppDomainGroup"):
               mbdomain_type = mbdomain_type.replace("'", "''")
               mbapp_name = mbapp_name.replace("'", "''")
            else:
                mbapp_name = ""


        if value.path is None:
            path = ""
        else:
            path = value.path
            # separates file name from file path
            mbfile_path, sep, mbfile_name = value.path.rpartition('/')
            mbfile_name = mbfile_name.replace("'", "''")
            mbfile_path = mbfile_path.replace("'", "''")

        if value.target is None:
            target = ""
        else:
            target = value.target

        if value.digest is None:
            digest = ""
            mbdata_hash = ""
        else:
            digest = value.digest
            mbdata_hash = hex2nums(value.digest)

        # Insert record in database
        if value.encryption_key is None:
            encryption_key = ""
        else:
            encryption_key = sqlite3.Binary(value.encryption_key)

        if value.mode is None:
            mode = 0
            mbfile_rights = ""
            mbfile_type = ""
        else:
            mode = value.mode
            mbfile_rights = modestr(value.mode & 0x0FFF)
            mbfile_type = filetype(value.mode)
            if (mbfile_type == 'd'):
                mbfile_path = value.path
                mbfile_name = ""

        if value.inode_number is None:
            inode_number = 0
        else:
            inode_number, = value.inode_number

        if value.user_id is None:
            user_id = ""
        else:
            user_id = value.user_id

        if value.group_id is None:
            group_id = ""
        else:
            group_id, = value.group_id

        if value.last_modification_time is None:
            mtime = 0
        else:
            mtime = value.last_modification_time

        if value.last_status_change_time is None:
            atime = 0
        else:
            atime = value.last_status_change_time

        if value.birth_time is None:
            ctime = 0
        else:
            ctime = value.birth_time

        if value.size is None:
            size = 0
        else:
            size = value.size

        if value.protection_class is None:
            protection_class = 0
        else:
            protection_class = value.protection_class

        if value.num_attributes is None:
            num_attributes = 0
        else:
            num_attributes = value.num_attributes

        if value.extended_attributes is None:
            extended_attributes = ""
        else:
            #extended_attributes = sqlite3.Binary(value.extended_attributes)
            extended_attributes = ""


        query = "INSERT INTO indice(domain, path, target, digest, encryption_key, mode, inode_number, user_id, group_id, mtime, atime, ctime, size, protection_class, num_attributes, extended_attributes, fileid, mbdomain_type, mbapp_name, mbfile_name, mbfile_path, mbfile_rights, mbfile_type, mbdata_hash)"
        query += " VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"


        dbcursor.execute(query, [domain, path, target, digest, encryption_key, mode, inode_number, user_id, group_id, mtime, atime, ctime, size, protection_class, num_attributes, extended_attributes, key, mbdomain_type, mbapp_name, mbfile_name, mbfile_path, mbfile_rights, mbfile_type, mbdata_hash])




        # check if file has properties to store in the properties table
        if (value.num_attributes > 0):

            query = "SELECT id FROM indice WHERE domain = ? AND fileid = ? LIMIT 1;"

            dbcursor.execute(query, (domain.replace("'", "''"), key))
            id = dbcursor.fetchall()

            if (len(id) > 0):
                index = id[0][0]
                properties = value.extended_attributes

                query = "INSERT INTO properties(file_id, property_name, property_val) VALUES (?, ?, ?);"
                rows = ((index, name, hex2nums(val)) for name, val in properties.items())
                dbcursor.executemany(query, rows);

            #print("File: %s, properties: %i"%(domain + ":" + filepath + "/" + filename, fileinfo['numprops']))
            #print(fileinfo['properties'])


    dbcursor.execute('CREATE INDEX indice_domain_path on indice (mbdomain_type, mbapp_name, mbfile_path);')
    dbcursor.execute('CREATE INDEX properties_file_id on properties (file_id);')
######

# print "You can decrypt the keychain using the following command : "
# print "python keychain_tool.py -d \"%s\" \"%s\"" % (output_path + "/KeychainDomain/keychain-backup.plist", output_path + "/Manifest.plist")

def extract_all():
    if sys.platform == "win32":
        mobilesync = os.environ["APPDATA"] + "/Apple Computer/MobileSync/Backup/"
    elif sys.platform == "darwin":
        mobilesync = os.environ["HOME"] + "/Library/Application Support/MobileSync/Backup/"
    else:
        print ("Unsupported operating system")
        return
    print ("-" * 60)
    print ("Searching for iTunes backups")
    print ("-" * 60)

    for udid in os.listdir(mobilesync):
        extract_backup(mobilesync + "/" + udid, udid + "_extract")

def main():
    # parser options
    parser = ArgumentParser(description='Extract iOS Backup.')
    parser.add_argument('-b', '--backup', dest='ibackup', help="path to iOS backup")
    parser.add_argument('-o', '--opath', dest='opath', help="output path")
    parser.add_argument('-a', '--app', dest='app', help="single app to extract")
    options = parser.parse_args()

    if options.ibackup is not None:
        if not os.path.exists(options.ibackup):
            print('"{}" ios backup not found!'.format(options.ibackup))
            sys.exit(1)

    backup_path = options.ibackup

    output_path = os.path.dirname(backup_path) + "_extract"

    if options.opath is not None:
        output_path = options.opath

    if options.app == "" or options.app is None:
        app = None
    else:
        app = options.app

    if backup_path == "icloud":
        from icloud.backup import download_backup

        print ("Downloading iCloud backup")
        download_backup(None, None, output_path)
    else:
        extract_backup(backup_path, output_path, app=app)


if __name__ == "__main__":
    main()
