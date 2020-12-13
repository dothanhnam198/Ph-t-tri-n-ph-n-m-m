import sys, os, subprocess
import binascii
import hashlib
import base64
import json
import re, uuid
import shutil
import requests
from requests import HTTPError
import pickle

from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import PKCS1_v1_5
from base64 import b64decode
from base64 import b64encode
from ftplib import FTP
from subprocess import Popen, PIPE


class RSAUtil:
    # tao khoa RSA
    def createRSAKey(iLength=2048):
        key = RSA.generate(iLength)
        private_key = key.export_key()
        file_out = open("private.pem", "wb")
        file_out.write(private_key)

        public_key = key.publickey().export_key()
        file_out = open("receiver.pem", "wb")
        file_out.write(public_key)
        return 1

    # mã hóa RSA với public key PEM data
    def rsaEncrypt(stringData):

        pubKey = RSA.importKey("""-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAqls0M+9/3WWu99z/+0Tg
SkhtHm0wapT3Joc5/wB754Durm4MlFcEHTi09g4MXa6mZr9eqxzl2M3Wn2tRXMmp
6VJnhGzI0FveNiX59LzfGInnMyN0N6Z5cxfo/DZLDJzOQmV5B2w+99RAUG5oABLD
/+N07Y/NA9qOifB6TkECu03s0OVfT6ukezGkhKYfFxczemZjzloo9PUwcnmdFBHn
2FrORPNUiLFqGvuoR2ea43+4AzO60A1Pf1HMhXKXsawhnVrsdDLT009m79GYdCqV
T/hSZcQf40vMb9MghjHDWdBMWUvDrF7MsB4eG0XaiPtQpDIC2r1o1qle8wP40Kyw
XwIDAQAB
-----END PUBLIC KEY-----""")

        cipher = PKCS1_v1_5.new(pubKey)

        ciphertext = ''
        for s in CommonUtil.splitByLength(b64encode(bytes(stringData, "utf-8")), 240):
            if ciphertext != '':
                ciphertext = ciphertext + 'XXXXX' + b64encode(cipher.encrypt(s)).decode('ascii')
            else:
                ciphertext = ciphertext + '' + b64encode(cipher.encrypt(s)).decode('ascii')

        return ciphertext

    # giải mã RSA với private key PEM data
    def rsaDecrypt(stringData):
        # private key
        priKey = RSA.importKey("""-----BEGIN RSA PRIVATE KEY-----
MIIEowIBAAKCAQEAqls0M+9/3WWu99z/+0TgSkhtHm0wapT3Joc5/wB754Durm4M
lFcEHTi09g4MXa6mZr9eqxzl2M3Wn2tRXMmp6VJnhGzI0FveNiX59LzfGInnMyN0
N6Z5cxfo/DZLDJzOQmV5B2w+99RAUG5oABLD/+N07Y/NA9qOifB6TkECu03s0OVf
T6ukezGkhKYfFxczemZjzloo9PUwcnmdFBHn2FrORPNUiLFqGvuoR2ea43+4AzO6
0A1Pf1HMhXKXsawhnVrsdDLT009m79GYdCqVT/hSZcQf40vMb9MghjHDWdBMWUvD
rF7MsB4eG0XaiPtQpDIC2r1o1qle8wP40KywXwIDAQABAoIBAAJ2de4qRw3LK6s5
pYdtiJ5BJu4dGo4UdvB/pj786s2jrmHwTnv2gYC4W26A58YAphKdCsS+gH1Hl+9G
Dwp7yP7Ayjd1lpGaQmQfJiOgLjl5KXZ7y5W9zKX1TND0BbG6IE7uj3cRuGUIOQ7w
m/KSCbx6bCwHlwTc9SKQOI/ZDC2iImvIclOiLJxG/L+iuC3uFb/eMsiH2D5QAo83
Fgwa2OJ/kH+X9tv7ZplnC2l2FVrodrR1BjPhdZ/tM+UqCPr6vxJ0wzZa16rEKfwq
GleYGUfuPQxI4zMmENFFXsfPmrVEOF/w3qFq2eyumV3No87cA5CuPLadoGCM0mdM
nOpnbkECgYEAwv8anFN2Dux6lzIU51sJwa24f9+7uL5KaXaIl8qz3F4gD/PjabHE
aWw2/ZSE1CkOcB6XVHcj4kII6EukVBMX0oRc5XRlTyMAnr5ie2gVxzyLUFWNPt/R
wivKATwA5BCcxU+HwIh9AhW/FRgr4HvqSLcmoCCfxgefaWlWQR4LyIsCgYEA36a1
9v9RAIONZRYvYFJK1D59ABFr5NKLqT1FwWnb7LJPjNOP30YaUTflpLHdOpJE/pyT
9gGcb6TlqJq2Xqy0LeKIYn1lDw/txLUdrvZsRPVK7e1Cca3nhVmGLLZmipeeZN8f
fviOvv6XdNS9hGpfvSlkaIStgLcXXboeOB4nXf0CgYAWP/GTYNqZvVYHpolIFNU6
Kk5hGPBclin7erD/UPvQ61SRPWz3hHc66EQmDypQ4xZoqLTvyGBp0ssdZnQru7n+
JWhMLknZC89oTaUDG89QWpIy6nAhenx+wWxdU7FuVI7u3LJKv8gz0rNo/scS6FDF
V1Cq+M4CVKBV8NUMvRbvHQKBgCbLXDUEBKD6MMSgHIewvpoiXLxuSTDf9KnenwL1
wdhE9dePux0Xo+kCsSroT1+hj6Y6ss+xZ9lV2SBt9cRmYLq02MN8zNLYCH5ejE+V
HyK3CdBLn4Loj4hqBwQqf476zdbhfS0hIGGw98SkQlt9uC2vyGL44L+7AqqXZjaF
xH5hAoGBALtz1E5b6I0Q3BxsVC+Lxc1LBZCoGMXK1yEMPvIaiYewTExEZORDUBU+
+HuB5Vo4qYwnIUGkRsF0ntFgTVe1lFCCSB7OfFGqvddQqVy4OrGdBcDtQvuU7/au
NPuOIsR/amd8jRgC1FrI57wagKYulHuVq8Q29TuX9h4LOmnVQKO6
-----END RSA PRIVATE KEY-----""")

        cipher = PKCS1_v1_5.new(priKey)

        plaintext = ''
        for s in stringData.split('XXXXX'):
            if s != '':
                # LOGUtil.log_print(cipher.decrypt(b64decode(s), "Error while decrypting").decode('ascii'))
                plaintext = plaintext + '' + cipher.decrypt(b64decode(s), "Error while decrypting").decode('ascii')

        return b64decode(plaintext).decode("utf-8")

class CommonUtil:

    # HASH md5 dữ liệu file, toàn bộ dữ liệu, theo các block
    @staticmethod
    def md5_for_file(filePath, block_size=2 ** 20):
        if os.path.isfile(filePath):
            with open(filePath, "rb") as f:
                md5 = hashlib.md5()
                while True:
                    data = f.read(block_size)
                    if not data:
                        break
                    md5.update(data)
                return md5.hexdigest()
        else:
            LOGUtil.log_print(filePath + ': File not found!')
            return ''

    # HASH md5 dữ liệu file video cho kiểm tra tính toàn vẹn, video tính dữ liệu từ DURATIOND để bỏ qua phần metadata thay đổi được
    @staticmethod
    def md5_for_videofile(filePath, block_size=2 ** 20):
        if os.path.isfile(filePath):
            ipos = 0
            size = 0
            with open(filePath, "rb") as f:
                while True:
                    data = f.read(block_size * 10)
                    f.seek(0, os.SEEK_END)
                    size = f.tell()
                    break
            # kg lay metadata
            ipos = (data.find(b"DURATIOND")) + 123  # het 2 DURATIOND vi van sai lech time
            # LOGUtil.log_print(ipos)
            with open(filePath, "rb") as f:
                md5 = hashlib.md5()
                data = f.read(ipos)
                while True:
                    data = f.read(block_size)
                    ipos = ipos + len(data)
                    if ipos == size and len(data) > 0:
                        # xoa 120 bytes cuoi cung thay doi do metadata
                        data = data[:len(data) - int(ipos / 2)]  # 2313
                    # LOGUtil.log_print(str(ipos) +" "+str(size) +" "+str(len(data)))
                    if not data:
                        break
                    md5.update(data)
                return md5.hexdigest()
        else:
            LOGUtil.log_print(filePath + ': File not found!')
            return ''

    # đổi chuổi sang Base64, lưu metadata cho dễ đọc từ mã hóa
    @staticmethod
    def toBase64(stringData):
        encodedBytes = base64.b64encode(stringData.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")

        return encodedStr

    # đổi chuổi từ Base64
    @staticmethod
    def fromBase64(stringData):
        decodedBytes = base64.b64decode(stringData)
        decodedStr = str(decodedBytes, "utf-8")

        return decodedStr

    # Ä‘á»•i chuá»•i tá»« Base64 to bytes
    @staticmethod
    def fromBase64ToByte(stringData):
        decodedBytes = base64.b64decode(stringData)
        decodedStr = decodedBytes

        return decodedStr

    # Tách chuổi thành các chuỗi con bằng nhau cho metadata max 1000
    @staticmethod
    def splitByLength(stringData, x=1000):
        return [stringData[y - x:y] for y in range(x, len(stringData) + x, x)]

    @staticmethod
    def removeSlash(s):
        s = str(s).replace('//', '/').replace('//', '/')
        if s.startswith('/'):
            s = s[1:]
        if s.endswith('/'):
            s = s[:-1]
        return s

    # lấy địa chỉ MAC address
    @staticmethod
    def getMACAddress():
        return ':'.join(re.findall('..', '%012x' % uuid.getnode()))

    # lấy không gian trống ổ cứng
    @staticmethod
    def getFreeSpace():
        total, used, free = shutil.disk_usage("/")
        return (free / (2 ** 30))

    # lấy không gian trống ổ cứng quy đổi thời gian video chứa được. dự tính 3 luồng video chính, tạm, merged tương đương số phút video
    @staticmethod
    def calcFreeSpaceForVideoTime():
        total, used, free = shutil.disk_usage("/")
        # số luồng file video, file tạm cần xử lý merge, add metadata
        flow = 3
        # số Mb cho 1 phút video
        sizeMbVideoMinute = 0.02

        remainVideoMinutes = int(free / (2 ** 30) / flow / sizeMbVideoMinute)
        hours = int(remainVideoMinutes / (60 * 60))
        minutes = int(remainVideoMinutes / (60))
        return '{0}:{1}'.format(hours, minutes)

    # đổi chuổi sang Base64, lưu metadata cho dễ đọc từ mã hóa
    @staticmethod
    def toJson(jsonStringData):
        return json.loads(jsonStringData)

    # đổi chuổi từ Base64
    @staticmethod
    def fromJson(jsonObject):
        return json.JSONEncoder.default(jsonObject, object)
        # return json.dumps(jsonObject)

    # thông báo
    @staticmethod
    def alert(title, message, buttons=None):
        import PyQt5

        if buttons is None:
            buttons = PyQt5.QtWidgets.QMessageBox.Ok
        msg = PyQt5.QtWidgets.QMessageBox()
        msg.setIcon(PyQt5.QtWidgets.QMessageBox.Warning)

        msg.setText(message)
        msg.setWindowTitle(title)
        if not (buttons is None):
            msg.setStandardButtons(buttons)

        return msg.exec_()


    @staticmethod
    def callprocess(cmd, params):
        #s = subprocess.check_output(["echo", "Hello World!"])
        p = list(''+x.strip().replace('*space*', ' ') for x in (' '+params.strip()).split(' '))[1:]
        LOGUtil.log_print(cmd+' '+params)
        LOGUtil.log_print(p)
        process = Popen([cmd, *p], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        return stdout.decode('utf-8')+stderr.decode('utf-8')
        """p1 = Popen(["ifconfig", "wlp7s0"],stdout=PIPE)
        p2 = Popen(["grep", "ether"],stdin=p1.stdout,stdout=PIPE,stderr=PIPE)
        p1.stdout.close()
        out, err = p2.communicate()
        LOGUtil.log_print(out)"""

    @staticmethod
    def get_dvd_mount_point(disc_name):
        disks = psutil.disk_partitions(all=True)
        for disk in disks:
            if not disk.device or disk.device is None:
                continue
            if disk.device == disc_name or (disc_name=='/dev/cdrom' and disk.device=='/dev/sr0'):
                return disk.mountpoint
        return ''

class APIUtil:
    # lưu token cho các API khác
    api_token = ''
    # lưu url
    api_url = 'http://localhost/EPS.CSDLGIA.Services.WebAPI/'
    siteapi_code = 'OCR_API'

    # gọi API login
    @classmethod
    def loginAPI(cls, username, password, apiLoginMethod='users/login/', tokenname='auth_token'):
        data = {'username': username, 'password': password, 'grant_type': 'password'}
        headers = {'Content-Type': 'application/x-www-form-urlencoded', 'Data-Type': 'Json', 'SITE-CODE': cls.siteapi_code}
        try:
            print('login')
            print(cls.api_url + apiLoginMethod)
            LOGUtil.log_print(cls.api_url + apiLoginMethod)
            response = requests.post(cls.api_url + apiLoginMethod, data, headers=headers, verify=False)
            jsonRet = response.json()
            cls.api_token = jsonRet[tokenname]
            return jsonRet
        except HTTPError as http_err:
            #LOGUtil.log_print(f'HTTP error occurred: {http_err}')  # Python 3.6
            pass
        except Exception as err:
            #LOGUtil.log_print(f'Other error occurred: {err}')  # Python 3.6
            pass
        else:
            pass
        return ''

    # gọi API GET
    @classmethod
    def getAPI(cls, apiMethod, query):
        headers = {'Authorization': 'Token {0}'.format(cls.api_token), 'SITE-CODE': cls.siteapi_code}
        try:
            response = requests.get((cls.api_url + '' + apiMethod).replace('/api/fake_ftp/', '/api_fake_ftp/'), params=query, headers=headers, verify=False)
            try:
                return response.json()
            except:
                return response.content.decode('utf-8')
        except HTTPError as http_err:
            LOGUtil.log_error(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            LOGUtil.log_error(f'Other error occurred: {err}')  # Python 3.6
        else:
            pass
        return ''

    # gọi API POST
    @classmethod
    def postAPI(cls, apiMethod, data):
        headers = {'Authorization': 'Token {0}'.format(cls.api_token), 'SITE-CODE': cls.siteapi_code}
        try:
            response = requests.post((cls.api_url + '' + apiMethod).replace('/api/fake_ftp/', '/api_fake_ftp/'), data=data, headers=headers, verify=False)
            try:
                return response.json()
            except:
                return response.content.decode('utf-8')
        except HTTPError as http_err:
            return f'HTTP error occurred: {http_err}'  # Python 3.6
        except Exception as err:
            return f'Other error occurred: {err}'  # Python 3.6
        else:
            pass
        return ''

    # gọi API download
    @classmethod
    def download(cls, link):
        headers = {'Authorization': 'Token {0}'.format(cls.api_token), 'SITE-CODE': cls.siteapi_code}
        try:
            response = requests.get(link, headers=headers)
            try:
                return response.content
            except:
                return response.content.decode('utf-8')
        except HTTPError as http_err:
            return f'HTTP error occurred: {http_err}'  # Python 3.6
        except Exception as err:
            return f'Other error occurred: {err}'  # Python 3.6
        else:
            pass
        return ''


    # gọi API download
    @classmethod
    def downloadAPI(cls, apiMethod, query):
        headers = {'Authorization': 'Token {0}'.format(cls.api_token), 'SITE-CODE': cls.siteapi_code}
        try:
            response = requests.get((cls.api_url + '' + apiMethod).replace('/api/fake_ftp/', '/api_fake_ftp/'), params = query, headers=headers, verify=False)
            try:
                return response.content
            except:
                return response.content.decode('utf-8')
        except HTTPError as http_err:
            return f'HTTP error occurred: {http_err}'  # Python 3.6
        except Exception as err:
            return f'Other error occurred: {err}'  # Python 3.6
        else:
            pass
        return ''

class METADATAUtil:
    # tạo metadatas từ đối tượng thông tin phiên hỏi cung, mã hóa toàn bộ phiên và tự phân tách thành các sub-metadata cho chứa đủ 1000 ký tự
    @staticmethod
    def generateMetadataFromJSONObject(chosenSession):
        metaData = ' -metadata SO_HIEU_PHIEN_HOI_CUNG="{0}" -metadata NGAY_HOI_CUNG="{1}" -metadata GIO_HOI_CUNG="{2}" '.format(
            chosenSession.sessionNo,
            chosenSession.sessionDate,
            chosenSession.sessionTime
        )
        i = 1
        for metaThongTin in CommonUtil.splitByLength(
                CommonUtil.toBase64(RSAUtil.rsaEncrypt(b64encode(pickle.dumps(chosenSession)).decode('ascii')))):
            metaData = metaData + '-metadata THONG_TIN_{0}="{1}" '.format(i, metaThongTin)
            i = i + 1
        return metaData

    # tạo metadata HASH dữ liệu file video cho kiểm tra toàn ven file
    @staticmethod
    def generateHashMetadataFromVideo(filePath):
        if os.path.isfile(filePath):
            metaData = '-metadata HASH_VIDEO_GOC="' + CommonUtil.md5_for_videofile(filePath) + '" '
            return metaData
        else:
            LOGUtil.log_print(filePath + ': File not found!')
            return ''

    # ghi metadata ra video bằng ffmpeg
    @staticmethod
    def setMetadataToVideo(filePath, metaData):
        if os.path.isfile(filePath + '_tmpVideo.mkv'):
            os.remove(filePath + '_tmpVideo.mkv')
        cmd = 'ffmpeg -y -i ' + filePath + ' -c copy ' + metaData + ' ' + filePath + '_tmpVideo.mkv'
        process = subprocess.call(cmd, shell=True)
        if os.path.isfile(filePath):
            os.remove(filePath)
        try:
            os.rename(filePath + '_tmpVideo.mkv', filePath)
            pass
        except Exception as inst:
            LOGUtil.log_error(inst)
            pass

    # đọc thông tin metadata từ video ra các chuỗi theo cặp name, value, tự gộp lại và giải mã THONG_TIN
    @staticmethod
    def getMetadataFromVideo(filePath):
        if os.path.isfile(filePath + '_metadataVideo.txt'):
            os.remove(filePath + '_metadataVideo.txt')
        cmd = 'ffmpeg -i ' + filePath + ' -f ffmetadata ' + filePath + '_metadataVideo.txt'
        process = subprocess.call(cmd, shell=True)
        if os.path.isfile(filePath + '_metadataVideo.txt'):
            metaDatas = [line.strip('\n').replace(';FFMETADATA1', 'FFMETADATA1==', 1).split('=', 1) for line in
                         open(filePath + '_metadataVideo.txt', 'r', encoding="utf-8", errors="surrogateescape")]

            if os.path.isfile(filePath + '_metadataVideo.txt'):
                os.remove(filePath + '_metadataVideo.txt')
            i = 1
            metaThongTin = ''
            for i in range(1000):
                for name, value in metaDatas:
                    if name == 'THONG_TIN_' + str(i):
                        metaThongTin = metaThongTin + value
            for i in range(1000):
                for meta in metaDatas:
                    name, value = meta
                    if name == 'THONG_TIN_' + str(i):
                        metaDatas.remove(meta)
            if metaThongTin != '':
                metaDatas.append(['THONG_TIN', b64decode(RSAUtil.rsaDecrypt(CommonUtil.fromBase64(metaThongTin)))])
                pass
            return metaDatas
        else:
            LOGUtil.log_print(filePath + ': Wrong VIDEO file. Can not read Metadata')
            return None

    @staticmethod
    def getHashFromMetadata(metaDatas):
        for meta in metaDatas:
            name, value = meta
            if name == 'HASH_VIDEO_GOC':
                return value

    @staticmethod
    def getSessionDTOFromMetadata(metaDatas):
        for meta in metaDatas:
            name, value = meta
            if name == 'THONG_TIN':
                return pickle.loads(value)

class FILEUtil:
    # merge file audio, video với metadata ra file MKV chuẩn MP4
    @staticmethod
    def mergeVideo(outputAudio, outputVideo, mergedVideo, metaData):
        if os.path.isfile(mergedVideo):
            os.remove(mergedVideo)
        # -f mp4
        cmd = 'ffmpeg -y -i ' + outputAudio + ' -r 30 -i ' + outputVideo + ' -filter:a aresample=async=1 -c:a flac -c:v copy ' + metaData + ' ' + mergedVideo
        LOGUtil.log_print(cmd)
        process = subprocess.call(cmd, shell=True)

    # kiểm tra tính toàn vẹn file Video từ metadata
    @staticmethod
    def validVideo(filePath):
        if os.path.isfile(filePath):
            metaHash = ''
            hash = CommonUtil.md5_for_videofile(filePath)
            metaDatas = METADATAUtil.getMetadataFromVideo(filePath)
            for name, value in metaDatas:
                if name == 'HASH_VIDEO_GOC':
                    metaHash = value
            return str(hash) == str(metaHash)
        else:
            LOGUtil.log_print(filePath + ': File not found!')
            return False

    # kiểm tra license hợp lệ
    @staticmethod
    def validLicense(fileLicense, MACAddress):
        if os.path.isfile(fileLicense):
            dataReal = ''
            for line in open(fileLicense, 'rb'):
                dataReal = dataReal + b64encode(line).decode('ascii')
            return RSAUtil.rsaDecrypt(dataReal) == MACAddress
        else:
            LOGUtil.log_print(fileLicense + ': File not found!')
            return False

    # ghi ra license
    @staticmethod
    def exportLicense(fileLicense, MACAddress):
        if os.path.isfile(fileLicense):
            os.remove(fileLicense)
        with open(fileLicense, 'wb') as f:
            f.write(b64decode(RSAUtil.rsaEncrypt(MACAddress)))

    # đổi tên file
    @staticmethod
    def renameFile(filePathFrom, filePathTo):
        if os.path.isfile(filePathTo):
            os.remove(filePathTo)
        try:
            os.rename(filePathFrom, filePathTo)
        except Exception as inst:
            LOGUtil.log_error(inst)
            pass

    @staticmethod
    def imageFromURL(url):
        import cv2
        cap = cv2.VideoCapture(url)
        if (cap.isOpened()):
            ret, img = cap.read()
            return img
        else:
            return None

    # get time file
    @staticmethod
    def getFileTime(filePath):
        try:
            return os.path.getmtime(filePath)
        except Exception as inst:
            LOGUtil.log_error(inst)
            return str(inst)

    # get time file
    @staticmethod
    def getFileExtension(filePath):
        try:
            paths = os.path.splitext(filePath)
            ext = paths[1].lower()
            return ext
        except Exception as inst:
            LOGUtil.log_error(inst)
            return str(inst)

    # get time file
    @staticmethod
    def getFileName(filePath):
        try:
            paths = os.path.splitext(os.path.basename(filePath))
            name = paths[0]
            return name
        except Exception as inst:
            LOGUtil.log_error(inst)
            return str(inst)

    # get time file
    @staticmethod
    def getFileBaseName(filePath):
        try:
            return os.path.basename(filePath)
        except Exception as inst:
            LOGUtil.log_error(inst)
            return str(inst)

    # get time file
    @staticmethod
    def scanFileExtension(path, ext):
        try:
            for _, _, dirfiles in os.walk(path):
                matches = (f for f in dirfiles if f.endswith(ext))
                break
            return matches
        except Exception as inst:
            LOGUtil.log_error(inst)
            return str(inst)

    @staticmethod
    def generate_big_random_bin_file(filename, size):
        """
        generate big binary file with the specified size in bytes
        :param filename: the filename
        :param size: the size in bytes
        :return:void
        """
        import os
        with open('%s' % filename, 'wb') as fout:
            fout.write(os.urandom(size))  # 1
        pass

    # generate_big_random_bin_file("temp_big_bin.dat",1024*1024)
    @staticmethod
    def generate_big_sparse_file(filename, size):
        f = open(filename, "wb")
        f.seek(size - 1)
        f.write(b"\1")
        f.close()
        pass

    @staticmethod
    def writechunk2file(filename, data, pos):
        f = open(filename, "r+b")
        f.seek(pos)
        f.write(data)
        f.close()
        pass

    @staticmethod
    def appendchunk2file(filename, data):
        f = open(filename, "ab")
        f.write(data)
        f.close()
        pass

    @staticmethod
    def fileexists(filename):
        if os.path.isfile(filename):
            return True
        else:
            if os.path.isdir(filename):
                return True
            else:
                return False

    @staticmethod
    def delfile(filename):
        if os.path.isfile(filename):
            os.remove(filename)

    # get time file
    @staticmethod
    def removeFolder(path):
        try:
            import shutil
            shutil.rmtree(path, ignore_errors=True)
        except Exception as inst:
            LOGUtil.log_error(inst)

class FTPUtil0:
    from ftplib import FTP
    # lưu
    ftp = FTP()

    # gọi FTP login
    @classmethod
    def connect(cls, ftpIP, ftpPort, ftpAccount, ftpPassword, ftpFolder, debugLevel=0):
        from ftplib import FTP
        ret = 'OK'
        try:
            cls.ftp = FTP(timeout=3000)
            cls.ftp.set_debuglevel(int(debugLevel))
            cls.ftp.connect(str(ftpIP), int(ftpPort))
            cls.ftp.login(str(ftpAccount), str(ftpPassword))
            if str(ftpFolder) != '':
                try:
                    cls.ftp.cwd(str(ftpFolder))
                except:
                    cls.ftp.mkd(str(ftpFolder))
                    cls.ftp.cwd(str(ftpFolder))
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = (str(e))
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def close(cls):
        try:
            cls.ftp.quit()
            cls.ftp.close()
        except:
            import traceback
            LOGUtil.log_error(traceback.format_exc())

    # gọi upload
    @classmethod
    def upload(cls, filePath, chunkSize=1024):
        from ftplib import FTP
        ret = 'OK'
        try:
            localfile = filePath
            with open(localfile, 'rb') as fp:
                cls.ftp.storbinary('STOR %s' % (localfile), fp, chunkSize) #os.path.basename
                fp.close()
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    # gá»i upload
    @classmethod
    def uploadData(cls, filePathLocal, filePathFtp, data, chunkSize=1024):
        from ftplib import FTP
        ret = 'OK'
        try:
            with open(filePathLocal, 'wb') as f:
                f.write(data)
                f.close()
            with open(filePathLocal, 'rb') as fp:
                cls.ftp.storbinary('STOR %s' % (filePathFtp), fp, chunkSize) # os.path.basename
                fp.close()
        except Exception as e:
            LOGUtil.log_error(filePathFtp)
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    # gá»i upload
    @classmethod
    def uploadText(cls, filePathLocal, filePathFtp, text, chunkSize=1024):
        from ftplib import FTP
        ret = 'OK'
        try:
            with open(filePathLocal, 'wb') as f:
                f.write(text.encode('utf-8'))
                f.close()
            with open(filePathLocal, 'rb') as fp:
                cls.ftp.storbinary('STOR %s' % (filePathFtp), fp, chunkSize) #os.path.basename
                fp.close()
        except Exception as e:
            LOGUtil.log_error(filePathFtp)
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    # gọi download
    @classmethod
    def download(cls, filePath, fileTemp):
        from ftplib import FTP
        ret = 'OK'
        try:
            with open(fileTemp, 'wb') as fp:
                cls.ftp.retrbinary('RETR %s' % (filePath), fp.write) #os.path.basename
                fp.close()
        except Exception as e:
            LOGUtil.log_print(filePath)
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    # gọi tao folder
    @classmethod
    def makeFolder(cls, path):
        from ftplib import FTP
        ret = 'OK'
        try:
            cls.ftp.mkd(path)
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def deleteFolder(cls, path):
        from ftplib import FTP
        ret = 'OK'
        try:
            cls.ftp.rmd(path)
            pass
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def cdFolder(cls, path):
        from ftplib import FTP
        ret = 'OK'
        try:
            cls.ftp.cwd(path)
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def rename(cls, fileFrom, fileTo):
        from ftplib import FTP
        ret = 'OK'
        try:
            cls.ftp.rename(fileFrom, fileTo)
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def delete(cls, filePath):
        from ftplib import FTP
        ret = 'OK'
        try:
            cls.ftp.delete(filePath)
            pass
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def isexist(cls, filePath):
        from ftplib import FTP
        ret = 'OK'
        try:
            if FILEUtil.getFileBaseName(filePath) in cls.ftp.nlst():
                ret = 'OK'
            else:
                ret = 'Not OK'
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

class FTPUtil:
    from ftplib import FTP
    # lưu
    ftp = FTP()
    ftpFolder = ''
    ftpIP = ''

    # gọi FTP login
    @classmethod
    def connect(cls, ftpIP, ftpPort, ftpAccount, ftpPassword, ftpFolder, debugLevel=0):
        from ftplib import FTP
        ret = 'OK'
        try:
            cls.ftpIP = ftpIP
            if ':' in cls.ftpIP:
                APIUtil.api_url = ftpIP
                APIUtil.loginAPI(ftpAccount, ftpPassword, 'api-token-auth', 'token')
                cls.ftpFolder = ftpFolder
            else:
                cls.ftp = FTP(timeout=3000)
                cls.ftp.set_debuglevel(int(debugLevel))
                cls.ftp.connect(str(ftpIP), int(ftpPort))
                cls.ftp.login(str(ftpAccount), str(ftpPassword))
                if str(ftpFolder) != '':
                    try:
                        cls.ftp.cwd(str(ftpFolder))
                    except:
                        cls.ftp.mkd(str(ftpFolder))
                        cls.ftp.cwd(str(ftpFolder))
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = (str(e))
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def close(cls):
        try:
            if ':' not in cls.ftpIP:
                cls.ftp.quit()
                cls.ftp.close()
        except:
            import traceback
            LOGUtil.log_error(traceback.format_exc())

    # gọi upload
    @classmethod
    def upload(cls, filePath, chunkSize=1024):
        from ftplib import FTP
        ret = 'OK'
        try:
            localfile = filePath

            filePathLocal = filePath
            filePathFtp = filePath
            if ':' in cls.ftpIP:
                # doc tung chunk
                if chunkSize is None or chunkSize <= 1024:
                    chunkSize = 2 * 1024 * 1024
                pos = 0
                f = open(filePathLocal, 'rb')
                size = os.path.getsize(filePathLocal)
                piece = None
                postData = None
                while True:
                    piece = f.read(chunkSize)
                    if not piece:
                        break
                    postData = {'folder': cls.ftpFolder,
                                'filename': filePathFtp,
                                'pos': pos * chunkSize,
                                'size': size,
                                'chunk': str(base64.b64encode(piece), "utf-8"),
                                }
                    ret = ''
                    iLoop = 0
                    while ret != 'OK':
                        ret = APIUtil.postAPI('fake_ftp/?cmd=upload', postData)
                        iLoop = iLoop + 1
                        if iLoop > 100:
                            break

                    postData = {}
                    piece = b''
                    pos = pos + 1
                f.close()
            else:
                with open(localfile, 'rb') as fp:
                    cls.ftp.storbinary('STOR %s' % (localfile), fp, chunkSize) #os.path.basename
                    fp.close()
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    # gá»i upload
    @classmethod
    def uploadData(cls, filePathLocal, filePathFtp, data, chunkSize=1024):
        from ftplib import FTP
        ret = 'OK'
        if data is None:
            return ret
        try:
            if ':' in cls.ftpIP:
                with open(filePathLocal, 'wb') as f:
                    f.write(data)
                    f.close()
                # doc tung chunk
                if chunkSize is None or chunkSize <= 1024:
                    chunkSize = 2 * 1024 * 1024
                pos = 0
                f = open(filePathLocal, 'rb')
                size = os.path.getsize(filePathLocal)
                piece = None
                postData = None
                while True:
                    piece = f.read(chunkSize)
                    if not piece:
                        break
                    postData = {'folder': cls.ftpFolder,
                                'filename': filePathFtp,
                                'pos': pos * chunkSize,
                                'size': size,
                                'chunk': str(base64.b64encode(piece), "utf-8"),
                                }
                    ret = ''
                    iLoop = 0
                    while ret != 'OK':
                        ret = APIUtil.postAPI('fake_ftp/?cmd=upload', postData)
                        iLoop = iLoop + 1
                        if iLoop > 100:
                            break

                    postData = {}
                    piece = b''
                    pos = pos + 1
                f.close()
            else:
                with open(filePathLocal, 'wb') as f:
                    f.write(data)
                    f.close()
                with open(filePathLocal, 'rb') as fp:
                    cls.ftp.storbinary('STOR %s' % (filePathFtp), fp, chunkSize) # os.path.basename
                    fp.close()
        except Exception as e:
            LOGUtil.log_error(filePathFtp)
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    # gá»i upload
    @classmethod
    def uploadText(cls, filePathLocal, filePathFtp, text, chunkSize=1024):
        from ftplib import FTP
        ret = 'OK'
        try:
            if ':' in cls.ftpIP:
                with open(filePathLocal, 'wb') as f:
                    f.write(text.encode('utf-8'))
                    f.close()
                # doc tung chunk
                if chunkSize is None or chunkSize <= 1024:
                    chunkSize = 2 * 1024 * 1024
                pos = 0
                f = open(filePathLocal, 'rb')
                size = os.path.getsize(filePathLocal)
                piece = None
                postData = None
                while True:
                    piece = f.read(chunkSize)
                    if not piece:
                        break
                    postData = {'folder': cls.ftpFolder,
                                'filename': filePathFtp,
                                'pos': pos * chunkSize,
                                'size': size,
                                'chunk': str(base64.b64encode(piece), "utf-8"),
                                }
                    ret = ''
                    iLoop = 0
                    while ret != 'OK':
                        ret = APIUtil.postAPI('fake_ftp/?cmd=upload', postData)
                        iLoop = iLoop + 1
                        if iLoop > 100:
                            break

                    postData = {}
                    piece = b''
                    pos = pos + 1
                f.close()
            else:
                with open(filePathLocal, 'wb') as f:
                    f.write(text.encode('utf-8'))
                    f.close()
                with open(filePathLocal, 'rb') as fp:
                    cls.ftp.storbinary('STOR %s' % (filePathFtp), fp, chunkSize) #os.path.basename
                    fp.close()
        except Exception as e:
            LOGUtil.log_error(filePathFtp)
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    # gọi download
    @classmethod
    def download(cls, filePath, fileTemp):
        from ftplib import FTP
        ret = 'OK'
        try:
            if ':' in cls.ftpIP:
                with open(fileTemp, 'wb') as fp:
                    data = APIUtil.downloadAPI('fake_ftp/?cmd=download', 'folder=' + str(cls.ftpFolder) + '&file=' + str(filePath))
                    if len(data) == 0:
                        print('FTP len is 0 in ' + filePath)
                    fp.write(data)
                    fp.close()
            else:
                with open(fileTemp, 'wb') as fp:
                    cls.ftp.retrbinary('RETR %s' % (filePath), fp.write) #os.path.basename
                    fp.close()
        except Exception as e:
            LOGUtil.log_print(filePath)
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    # gọi tao folder
    @classmethod
    def makeFolder(cls, path):
        from ftplib import FTP
        ret = 'OK'
        try:
            if ':' in cls.ftpIP:
                ret = APIUtil.getAPI('fake_ftp/?cmd=makeFolder', 'folder=' + str(path))
            else:
                cls.ftp.mkd(path)
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def deleteFolder(cls, path):
        from ftplib import FTP
        ret = 'OK'
        try:
            if ':' in cls.ftpIP:
                ret = APIUtil.getAPI('fake_ftp/?cmd=deleteFolder', 'folder=' + str(path))
            else:
                cls.ftp.rmd(path)
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def cdFolder(cls, path):
        from ftplib import FTP
        ret = 'OK'
        try:
            if ':' in cls.ftpIP:
                cls.ftpFolder = path
            else:
                cls.ftp.cwd(path)
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def rename(cls, fileFrom, fileTo):
        from ftplib import FTP
        ret = 'OK'
        try:
            if ':' in cls.ftpIP:
                ret = APIUtil.getAPI('fake_ftp/?cmd=rename', 'folder=' + str(cls.ftpFolder) + '&file_from=' + str(fileFrom) + '&file_to=' + str(fileTo))
            else:
                cls.ftp.rename(fileFrom, fileTo)
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def delete(cls, filePath):
        from ftplib import FTP
        ret = 'OK'
        try:
            if ':' in cls.ftpIP:
                ret = APIUtil.getAPI('fake_ftp/?cmd=delete', 'folder=' + str(cls.ftpFolder) + '&file=' + str(filePath))
            else:
                cls.ftp.delete(filePath)
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

    @classmethod
    def isexist(cls, filePath):
        from ftplib import FTP
        ret = 'OK'
        try:
            if ':' in cls.ftpIP:
                ret = APIUtil.getAPI('fake_ftp/?cmd=isexist', 'folder=' + str(cls.ftpFolder) + '&file=' + str(filePath))
            else:
                if FILEUtil.getFileBaseName(filePath) in cls.ftp.nlst():
                    ret = 'OK'
                else:
                    ret = 'Not OK'
        except Exception as e:
            LOGUtil.log_error(str(e))
            ret = str(e)
            import traceback
            LOGUtil.log_error(traceback.format_exc())
        return ret

class LOGUtil:
    fileLog = ''
    is_error = False
    errorLog = ''

    # tao lai file
    @classmethod
    def log_reset(cls, fileLog):
        FILEUtil.delfile(fileLog)
        cls.fileLog = fileLog

    # ghi log + print log
    @classmethod
    def log_print(cls, log_text):
        print(log_text)

    # set status
    @classmethod
    def log_error(cls, log_text):
        cls.is_error = True
        cls.errorLog = str(log_text) + ' error occurred '
        LOGUtil.log_print(log_text)
        if cls.fileLog!='':
            try:
                with open(cls.fileLog, 'a+') as f:
                    f.write(str(log_text))
                    f.write('\r\n')
            except:
                pass

