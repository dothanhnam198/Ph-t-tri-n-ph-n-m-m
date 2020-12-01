from ftplib import FTP

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