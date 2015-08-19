from Crypto.Cipher import AES
from hashlib import sha1
from struct import unpack
import os, re, StringIO

MBDB_SIGNATURE = 'mbdb\x05\x00'

MASK_SYMBOLIC_LINK = 0xa000
MASK_REGULAR_FILE = 0x8000
MASK_DIRECTORY = 0x4000

def warn(msg):
    print("WARNING: %s" % msg)
    
class MBFileRecord(object):
    def __init__(self, mbdb):
        self.domain = self._decode_string(mbdb)
        if self.domain is None:
            warn("Domain name missing from record")

        self.path = self._decode_string(mbdb)
        if self.path is None:
            warn("Relative path missing from record")

        self.target= self._decode_string(mbdb) # for symbolic links

        self.digest = self._decode_string(mbdb)
        self.encryption_key = self._decode_data(mbdb)

        data = mbdb.read(40) # metadata, fixed size

        self.mode, = unpack('>H', data[0:2])
        if not(self.is_regular_file() or self.is_symbolic_link() or self.is_directory()):
            print(self.mode)
            warn("File type mising from record mode")

        if self.is_symbolic_link() and self.target is None:
            warn("Target required for symblolic links")

        self.inode_number = unpack('>Q', data[2:10])
        self.user_id, = unpack('>I', data[10:14])
        self.group_id = unpack('>I', data[14:18])
        self.last_modification_time, = unpack('>i', data[18:22])
        self.last_status_change_time, = unpack('>i', data[22:26])
        self.birth_time, = unpack('>i', data[26:30])
        self.size, = unpack('>q', data[30:38])

        if self.size != 0 and not self.is_regular_file():
            warn("Non-zero size for a record which is not a regular file")

        self.protection_class = ord(data[38])

        self.num_attributes = ord(data[39])
        if self.num_attributes == 0:
            self.extended_attributes = None
        else:
            self.extended_attributes = {}
            for i in xrange(self.num_attributes):
                k = self._decode_string(mbdb)
                v = self._decode_data(mbdb)
                self.extended_attributes[k] = v

    def _decode_string(self, s):
        s_len, = unpack('>H', s.read(2))
        if s_len == 0xffff:
            return None
        return s.read(s_len)

    def _decode_data(self, s):
        return self._decode_string(s)

    def type(self):
        return self.mode & 0xf000

    def is_symbolic_link(self):
        return self.type() == MASK_SYMBOLIC_LINK

    def is_regular_file(self):
        return self.type() == MASK_REGULAR_FILE

    def is_directory(self):
        return self.type() == MASK_DIRECTORY

    def is_domain(self, domain):
        ret = False
        if domain.lower() in self.domain.lower():
            ret = True
        elif domain.lower() in self.domain.lower() + "-" + self.path.lower():
            ret = True
        else:
            ret = False
        return ret

class MBFileRecordFromDB(object):
    def __init__(self, record):
        self.domain = record['domain']
        if self.domain is None or self.domain == "":
            warn("Domain name missing from record")

        self.path = record['path']
        if self.path is None or self.path == "":
            warn("Relative path missing from record")

        self.target= record['target'] # for symbolic links

        self.digest = record['digest']
        self.encryption_key = record['encryption_key']

        self.mode = record['mode']

#        self.inode_number = unpack('>Q', record['inode_number'])
        self.inode_number = record['inode_number']
        self.user_id = record['user_id']
        self.group_id = record['group_id']
        self.last_modification_time = record['mtime']
        self.last_status_change_time = record['atime']
        self.birth_time = record['ctime']
        self.size = record['size']
        self.protection_class = record['protection_class']
        self.num_attributes = record['num_attributes']
        self.extended_attributes = record['extended_attributes']

        self.fileid = record['fileid']

        self.mbdomain_type = record['mbdomain_type']
        self.mbapp_name = record['mbapp_name']
        self.mbfile_name = record['mbfile_name']
        self.mbfile_path = record['mbfile_path']
        self.mbfile_rights = record['mbfile_rights']
        self.mbfile_type = record['mbfile_type']
        self.mbdata_hash = record['mbdata_hash']

    def _decode_string(self, s):
        s_len, = unpack('>H', s.read(2))
        if s_len == 0xffff:
            return None
        return s.read(s_len)

    def _decode_data(self, s):
        return self._decode_string(s)

    def type(self):
        return self.mode & 0xf000

    def is_symbolic_link(self):
        return self.type() == MASK_SYMBOLIC_LINK

    def is_regular_file(self):
        return self.type() == MASK_REGULAR_FILE

    def is_directory(self):
        return self.type() == MASK_DIRECTORY

    '''
    def is_symbolic_link(self):
        return self.type == 'l'

    def is_regular_file(self):
        return self.type == '-'

    def is_directory(self):
        return self.type == 'd'
    '''
    def is_domain(self, domain):
        ret = False
        if domain.lower() in self.domain.lower():
            ret = True
        elif domain.lower() in self.domain.lower() + "-" + self.path.lower():
            ret = True
        else:
            ret = False
        return ret


class MBDB(object):
    def __init__(self, path):
        self.files = {}
        self.backup_path = path
        self.keybag = None
        self.numoffiles = 0

        # open the database
        mbdb = file(path + '/Manifest.mbdb', 'rb')

        # skip signature
        signature = mbdb.read(len(MBDB_SIGNATURE))
        if signature != MBDB_SIGNATURE:
            raise Exception("Bad mbdb signature")
        try:
            i = 0
            while True:
                i += 1
                rec = MBFileRecord(mbdb)
                fn = rec.domain + "-" + rec.path
                sb = sha1(fn).digest().encode('hex')
                if len(sb) % 2 == 1:
                    sb = '0'+sb  
                self.files[sb] = rec
            self.numoffiles = i
        except:
            mbdb.close()

    def print_filenames(self):
        for record in self.files.values():
            print("Domain: %s" %str(record.domain))

    def get_file_by_name(self, filename):
        for (k, v) in self.files.iteritems():
            if v.path == filename:
                return (k, v)
        return None

    def extract_backup(self, output_path):
        for record in self.files.values():
            # create directories if they do not exist
            # makedirs throw an exception, my code is ugly =)
            if record.is_directory():
                try:
                    os.makedirs(os.path.join(output_path, record.domain, record.path))
                except:
                    pass

        for (filename, record) in self.files.items():
            # skip directories
            if record.is_directory():
                continue
            self.extract_file(filename, record, output_path)

    def extract_backup_from_db(self, record, output_path):
#        app_path = os.path.join(output_path, record.domain, record.path)
        app_path = os.path.join(output_path, record.mbdomain_type, record.mbapp_name, record.mbfile_path)
        try:
            os.makedirs(app_path)
        except:
            pass

        if not record.is_directory():
            record.domain = os.path.join(record.mbdomain_type, record.mbapp_name)
            self.extract_file(record.fileid, record, output_path)

    def extract_file(self, filename, record, output_path):
        # adjust output file name
        if record.is_symbolic_link():
            out_file = record.target
        else:
            out_file = record.path

        #print("outfile: %s" %out_file)
        # read backup file
        try:
            f1 = file(os.path.join(self.backup_path, filename), 'rb')
        except(IOError):
            warn("File %s (%s) has not been found" % (filename, record.path))
            return

        # write output file
        out_file = re.sub(r'[:|*<>?"]', "_", out_file)
        output_path = os.path.join(output_path, record.domain, out_file)
        #print("Writing %s" % output_path)
        f2 = file(output_path, 'wb')

        aes = None

        if record.encryption_key is not None and self.keybag: # file is encrypted!
            key = self.keybag.unwrapKeyForClass(record.protection_class, record.encryption_key[4:])
            if not key:
                warn("Cannot unwrap key")
                return
            aes = AES.new(key, AES.MODE_CBC, "\x00"*16)

        while True:
            data = f1.read(8192)
            if not data:
                break
            if aes:
                data2 = data = aes.decrypt(data)
            f2.write(data)

        f1.close()
        if aes:
            c = data2[-1]
            i = ord(c)
            if i < 17 and data2.endswith(c*i):
                f2.truncate(f2.tell() - i)
            else:
                warn("Bad padding, last byte = 0x%x !" % i)

        f2.close()

    def readBackupFile(self, record):
        blob = None

        filename = record.fileid

        # read backup file
        try:
            f1 = file(os.path.join(self.backup_path, filename), 'rb')
        except(IOError):
            warn("File %s (%s) has not been found" % (filename, record.path))
            return blob

        # write output file
        f2 = StringIO.StringIO()
        aes = None

        if record.encryption_key is not None and self.keybag: # file is encrypted!
            key = self.keybag.unwrapKeyForClass(record.protection_class, record.encryption_key[4:])
            if not key:
                warn("Cannot unwrap key")
                return blob
            aes = AES.new(key, AES.MODE_CBC, "\x00"*16)

        while True:
            data = f1.read(8192)
            if not data:
                break
            if aes:
                data2 = data = aes.decrypt(data)
            f2.write(data)

        f1.close()
        if aes:
            c = data2[-1]
            i = ord(c)
            if i < 17 and data2.endswith(c*i):
                f2.truncate(f2.tell() - i)
            else:
                warn("Bad padding, last byte = 0x%x !" % i)

        blob = f2.getvalue()
        f2.close()
        return blob