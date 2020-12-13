import django
django.setup()
import multiprocessing
import os
import signal
import datetime
import io
import time

import img2pdf
import json

from django.db.models import Q, F
from builtins import Exception
from collections import namedtuple

import PIL
from PIL import Image
from PyPDF2 import PdfFileMerger
from pikepdf._qpdf import Pdf

from .DjangoUtility import *
from .models import *
from pikepdf import Pdf, PdfImage, Name

ApiParam = namedtuple(
    'ApiParam', 'url_api, jsonData'
)
ApiResult = namedtuple(
    'ApiResult', 'error, options, text'
)

class OCRResult():
    class OCRPage():
        def __init__(self):
            self.page_number=0
            self.page_files: OCRResult.OCRFile = []
    class OCRFile():
        def __init__(self):
            self.file_name=''
            self.file_type=''
            self.file_size=0
            self.file_date=''
            self.file_link=''
            self.result_pages: OCRResult.OCRPage = []
    def __init__(self):
        self.file_number = 0
        self.file_input = ''
        self.result_files: OCRResult.OCRFile = []

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

def exec_api_sync(apiParam):
    APIUtil.api_url = apiParam.url_api.replace('/api/', '/')
    ret = ''
    err = False
    try:
        print('call '+APIUtil.api_url + '  '+str(apiParam.jsonData['noderequest_id']))
        # Chay anonymous
        # APIUtil.loginAPI(noderequest.node_id.api_user, noderequest.node_id.api_pwd)
        ret = APIUtil.postAPI('ocr/', {'inputOCR': json.dumps(apiParam.jsonData)})
        print(ret)
        if str(ret).find('TypeError:')>0 or str(ret).find('RuntimeError:')>0 or str(ret).find('error occurred: HTTPConnectionPool')>0:
            err=True
    except Exception as e:
        ret = str(e)
        print(e)
        print('exec_api_sync')
        err = True
    return ApiResult(error=err, options=apiParam.jsonData, text=ret)

def RoundUP(num):
    if num == int(num):
        return num
    return int(num + 1)

def base64_image(data, name=None):
    _format, _img_str = data.split(';base64,')
    _name, ext = _format.split('/')
    if not name:
        name = _name.split(":")[-1]
    stream = io.BytesIO(base64.b64decode(_img_str))

    return PIL.Image.open(stream)

def base64_blob(data, name=None):
    _format, _img_str = data.split(';base64,')
    _name, ext = _format.split('/')
    if not name:
        name = _name.split(":")[-1]
    stream = io.BytesIO(base64.b64decode(_img_str))

    return stream

def fileimage_as_base64(image_file, format='png'):
    """
    :param `image_file` for the complete path of image.
    :param `format` is format for image, eg: `png` or `jpg`.
    """
    if not os.path.isfile(image_file):
        return None

    encoded_string = ''
    with open(image_file, 'rb') as img_f:
        encoded_string = base64.b64encode(img_f.read())
    return 'data:image/%s;base64,%s' % (format, encoded_string)

def image_as_base64(image:Image):
    encoded_string = ''
    format = 'png'
    imgByteArr = io.BytesIO()
    image.save(imgByteArr, format=format)
    imgByteArr = imgByteArr.getvalue()
    encoded_string = base64.b64encode(imgByteArr)
    return 'data:image/%s;base64,%s' % (format, encoded_string.decode('ascii'))


def readPrivateFTP(json_data):
    ftp_private = OCR_Config.objects.get(is_public_ftp=0)
    json_data['ftp_ip'] = ftp_private.ftp_ip
    json_data['ftp_port'] = ftp_private.ftp_port
    json_data['ftp_user'] = ftp_private.ftp_user
    json_data['ftp_pwd'] = ftp_private.ftp_pwd
    return ftp_private, json_data


def readListPDFOrImages(json_data, work_temp_folder, folderUpload):
    pdfs = list()
    iimage=0
    page_list = []
    if json_data['page_number'] != '':
        pages = json_data['page_number'].split(',')
        for page in pages:
            if '-' in page:
                page_range = page.split('-')
                for page2 in range(int(page_range[0]), int(page_range[1]) + 1):
                    page_list.append(int(page2))
            else:
                page_list.append(int(page))
    page_list.sort()
    for img in json_data['images']:
        if not img is None:
            if str(img).find('data:application/pdf;') >= 0:
                # append base64PDF => binary PDFS
                imagepdf = base64_blob(img).read()
                fileTemp=folderUpload + '/' + json_data['image_names'][iimage]
                with open(fileTemp, 'wb') as f2:
                    f2.write(imagepdf)
                    f2.close()
                if page_list is None or page_list == []:
                    pdfs.append(imagepdf)
                else:
                    pdf = Pdf.open(fileTemp)
                    total_pages = len(pdf.pages)
                    for i in range(0, total_pages):
                        page_bottom = total_pages-i
                        if (page_bottom) not in page_list:
                            try:
                                del pdf.pages[page_bottom-1]
                            except:
                                print('Loi del page ' + str(total_pages-i+1))
                    pdf.save(fileTemp+'.xxx')
                    pdf.close()
                    FILEUtil.renameFile(fileTemp+'.xxx', fileTemp)
                    pdf = Pdf.open(fileTemp)
                    no_images = False
                    #3 trang dau kg co anh
                    if list(pdf.pages[0].images.keys()) == []:
                        no_images = True
                    if len(pdf.pages)>1:
                        if list(pdf.pages[1].images.keys()) == []:
                            no_images = no_images and True
                        else:
                            no_images = no_images and False
                    if len(pdf.pages)>2:
                        if list(pdf.pages[2].images.keys()) == []:
                            no_images = no_images and True
                        else:
                            no_images = no_images and False
                    if no_images:
                        pdf.close()
                        import pdf2image
                        from PIL import Image
                        PDF_PATH = fileTemp
                        DPI = 200
                        OUTPUT_FOLDER = None
                        FIRST_PAGE = None
                        LAST_PAGE = None
                        FORMAT = 'jpg'
                        THREAD_COUNT = 1
                        USERPWD = None
                        USE_CROPBOX = False
                        STRICT = False
                        print('start PDF text to image')
                        pil_images = pdf2image.convert_from_path(PDF_PATH, dpi=DPI, output_folder=OUTPUT_FOLDER, first_page=FIRST_PAGE, last_page=LAST_PAGE, fmt=FORMAT, thread_count=THREAD_COUNT, userpw=USERPWD, use_cropbox=USE_CROPBOX, strict=STRICT)
                        index = 1
                        #for image in pil_images:
                        pil_images[0].save(fileTemp+'.xxx.pdf', "PDF", resolution=100.0, save_all=True, append_images=pil_images[1:])
                        FILEUtil.renameFile(fileTemp+'.xxx.pdf', fileTemp)
                        print('end')
                    with open(fileTemp, 'rb') as f2:
                        pdfs.append(f2.read())
                        f2.close()
            elif str(img).find('data:image') >= 0:
                images = []
                return_data = io.BytesIO()
                tiffstack = PIL.Image.open(io.BytesIO(base64_blob(img).read()))
                try:
                    for i in range(tiffstack.n_frames):
                        tiffstack.seek(i)
                        tiffstack.save(return_data, 'TIFF')
                        if page_list is None or page_list == []:
                            images.append(return_data.getvalue())
                        elif i in page_list:
                            images.append(return_data.getvalue())
                except:
                    images.append(base64_blob(img).read())
                if len(images) > 0:
                    # This create a single page PDF
                    dpi = 200
                    layout_fun = img2pdf.get_fixed_dpi_layout_fun((dpi, dpi))
                    imagepdf = img2pdf.convert(images, with_pdfrw=True,
                                               layout_fun=layout_fun)  # , outputstream=imagepdf)

                    if not imagepdf is None:
                        pdfs.append(imagepdf)
                        fileTemp=folderUpload + '/' + json_data['image_names'][iimage]
                        with open(fileTemp, 'wb') as f2:
                            f2.write(imagepdf)
                            f2.close()
            iimage=iimage+1
    # doc tu folder upload truoc hoac FTP public truyen tu json_data
    if not json_data['file_input'] is None:
        for input_file in json_data['file_input']:
            # doc tu folder Uploads truoc roi moi FTP
            print(folderUpload + '/' + input_file)
            if FILEUtil.fileexists(folderUpload + '/' + input_file):
                fileTemp = folderUpload + '/' + input_file
                if FILEUtil.getFileExtension(input_file) == '.pdf':
                    # append base64PDF => binary PDFS
                    if page_list is None or page_list == []:
                        with open(fileTemp, 'rb') as f:
                            data = f.read()
                            pdfs.append(data)
                    else:
                        pdf = Pdf.open(fileTemp)
                        total_pages = len(pdf.pages)
                        for i in range(0, total_pages):
                            page_bottom = total_pages-i
                            if (page_bottom) not in page_list:
                                try:
                                    del pdf.pages[page_bottom-1]
                                except:
                                    print('Loi del page ' + str(total_pages-i-1))
                        pdf.save(fileTemp+'.xxx')
                        pdf.close()
                        FILEUtil.renameFile(fileTemp+'.xxx', fileTemp)

                    pdf = Pdf.open(fileTemp)
                    no_images = False
                    #3 trang dau kg co anh
                    if list(pdf.pages[0].images.keys()) == []:
                        no_images = True
                    if len(pdf.pages)>1:
                        if list(pdf.pages[1].images.keys()) == []:
                            no_images = no_images and True
                        else:
                            no_images = no_images and False
                    if len(pdf.pages)>2:
                        if list(pdf.pages[2].images.keys()) == []:
                            no_images = no_images and True
                        else:
                            no_images = no_images and False
                    if no_images:
                        pdf.close()
                        import pdf2image
                        from PIL import Image
                        PDF_PATH = fileTemp
                        DPI = 200
                        OUTPUT_FOLDER = None
                        FIRST_PAGE = None
                        LAST_PAGE = None
                        FORMAT = 'jpg'
                        THREAD_COUNT = 1
                        USERPWD = None
                        USE_CROPBOX = False
                        STRICT = False
                        print('start PDF text to image')
                        pil_images = pdf2image.convert_from_path(PDF_PATH, dpi=DPI, output_folder=OUTPUT_FOLDER, first_page=FIRST_PAGE, last_page=LAST_PAGE, fmt=FORMAT, thread_count=THREAD_COUNT, userpw=USERPWD, use_cropbox=USE_CROPBOX, strict=STRICT)
                        index = 1
                        #for image in pil_images:
                        pil_images[0].save(fileTemp+'.xxx.pdf', "PDF", resolution=100.0, save_all=True, append_images=pil_images[1:])
                        FILEUtil.renameFile(fileTemp+'.xxx.pdf', fileTemp)
                        print('end')
                    with open(fileTemp, 'rb') as f:
                        data = f.read()
                        pdfs.append(data)
                else:
                    images = []
                    return_data = io.BytesIO()
                    tiffstack = PIL.Image.open(fileTemp)
                    try:
                        for i in range(tiffstack.n_frames):
                            tiffstack.seek(i)
                            tiffstack.save(return_data, 'TIFF')
                            if page_list is None or page_list == []:
                                images.append(return_data.getvalue())
                            elif i in page_list:
                                images.append(return_data.getvalue())
                    except:
                        with open(fileTemp, 'rb') as f:
                            images.append(f.read())
                    if len(images)>0:
                        # This create a single page PDF
                        dpi = 200
                        layout_fun = img2pdf.get_fixed_dpi_layout_fun((dpi, dpi))
                        imagepdf = img2pdf.convert(images, with_pdfrw=True,
                                                   layout_fun=layout_fun)  # , outputstream=imagepdf)

                        if not imagepdf is None:
                            pdfs.append(imagepdf)
                            with open(fileTemp, 'rb') as f2:
                                with open(fileTemp+'.image', 'wb') as f3:
                                    f3.write(f2.read())
                                    f3.close()
                                    f2.close()
                            with open(fileTemp, 'wb') as f2:
                                f2.write(imagepdf)
                                f2.close()
            else:
                fileTemp = work_temp_folder + '/' + input_file
                FTPUtil.connect(json_data['ftp_ip'], json_data['ftp_port'], json_data['ftp_user'], json_data['ftp_pwd'],
                                json_data['client_folder'])
                FTPUtil.download(input_file, fileTemp)
                if FILEUtil.getFileExtension(input_file) == '.pdf':
                    # append base64PDF => binary PDFS
                    if page_list is None or page_list == []:
                        with open(fileTemp, 'rb') as f:
                            data = f.read()
                            pdfs.append(data)
                    else:
                        pdf = Pdf.open(fileTemp)
                        total_pages = len(pdf.pages)
                        for i in range(0, total_pages):
                            page_bottom = total_pages-i
                            if (page_bottom) not in page_list:
                                try:
                                    del pdf.pages[page_bottom-1]
                                except:
                                    pass
                        pdf.save(fileTemp+'.xxx')
                        pdf.close()
                        FILEUtil.renameFile(fileTemp+'.xxx', fileTemp)
                    pdf = Pdf.open(fileTemp)
                    no_images = False
                    #3 trang dau kg co anh
                    if list(pdf.pages[0].images.keys()) == []:
                        no_images = True
                    if len(pdf.pages)>1:
                        if list(pdf.pages[1].images.keys()) == []:
                            no_images = no_images and True
                        else:
                            no_images = no_images and False
                    if len(pdf.pages)>2:
                        if list(pdf.pages[2].images.keys()) == []:
                            no_images = no_images and True
                        else:
                            no_images = no_images and False
                    if no_images:
                        pdf.close()
                        import pdf2image
                        from PIL import Image
                        PDF_PATH = fileTemp
                        DPI = 200
                        OUTPUT_FOLDER = None
                        FIRST_PAGE = None
                        LAST_PAGE = None
                        FORMAT = 'jpg'
                        THREAD_COUNT = 1
                        USERPWD = None
                        USE_CROPBOX = False
                        STRICT = False
                        print('start PDF text to image')
                        pil_images = pdf2image.convert_from_path(PDF_PATH, dpi=DPI, output_folder=OUTPUT_FOLDER, first_page=FIRST_PAGE, last_page=LAST_PAGE, fmt=FORMAT, thread_count=THREAD_COUNT, userpw=USERPWD, use_cropbox=USE_CROPBOX, strict=STRICT)
                        index = 1
                        #for image in pil_images:
                        pil_images[0].save(fileTemp+'.xxx.pdf', "PDF", resolution=100.0, save_all=True, append_images=pil_images[1:])
                        FILEUtil.renameFile(fileTemp+'.xxx.pdf', fileTemp)
                        print('end')
                    with open(fileTemp, 'rb') as f:
                        data = f.read()
                        pdfs.append(data)
                else:
                    images = []
                    return_data = io.BytesIO()
                    tiffstack = PIL.Image.open(fileTemp)
                    try:
                        for i in range(tiffstack.n_frames):
                            tiffstack.seek(i)
                            tiffstack.save(return_data, 'TIFF')
                            if page_list is None or page_list == []:
                                images.append(return_data.getvalue())
                            elif i in page_list:
                                images.append(return_data.getvalue())
                    except:
                        with open(fileTemp, 'rb') as f:
                            images.append(f.read())
                    if len(images)>0:
                        # This create a single page PDF
                        dpi = 200
                        layout_fun = img2pdf.get_fixed_dpi_layout_fun((dpi, dpi))
                        imagepdf = img2pdf.convert(images, with_pdfrw=True,
                                                   layout_fun=layout_fun)  # , outputstream=imagepdf)

                        if not imagepdf is None:
                            pdfs.append(imagepdf)
                            with open(fileTemp, 'rb') as f2:
                                with open(fileTemp+'.image', 'wb') as f3:
                                    f3.write(f2.read())
                                    f3.close()
                                    f2.close()
                            with open(fileTemp, 'wb') as f2:
                                f2.write(imagepdf)
                                f2.close()

            json_data['image_names'].append(FILEUtil.getFileBaseName(input_file))

    # xoa file khoi inputOCR vi thay bang FTP private share cho song song
    json_data['images'] = []
    json_data['page_number'] = ''

    return pdfs, json_data


def createOCRRequest(json_data, ipdf):
    try:
        input_file = json_data['image_names'][ipdf]
        json_data['client_folder']=json_data['temp_ocr_folder']
        # moi file la 1 request => nhieu noderequest xu ly
        ocrrequest = OCR_Request.objects.create()
        ocrrequest.config_ocr = json.dumps(json_data)
        ocrrequest.ftp_path = json_data['client_folder']
        ocrrequest.file_ocr = input_file
        ocrrequest.save()
        return input_file, ocrrequest
    except:
        return None, None

def createOCRNodeRequestFromSplitted(nodes, json_data, work_temp_folder, folderUpload, ftp_folderUpload, pagesByNode, countOfPages, ftp_private, ocrrequest, ifile):
    iPages = 0
    for node in nodes:
        file_output = work_temp_folder + '/' + json_data['file_output'][ifile]
        format = '%0' + str(len(str(pagesByNode)) + 1) + 'd'
        split_range = (format % 1) + '-' + (format % pagesByNode)
        if iPages > 0:
            split_range = (format % (pagesByNode * iPages + 1)) + '-'
            if countOfPages < pagesByNode * iPages + pagesByNode:
                split_range = split_range + (format % (countOfPages))
            else:
                split_range = split_range + (format % (pagesByNode * iPages + pagesByNode))
        fileInByPages = FILEUtil.getFileName(file_output) + '-' + split_range + FILEUtil.getFileExtension(file_output)
        iPages = iPages + 1
        if not FILEUtil.fileexists(work_temp_folder + '/' + fileInByPages) and FILEUtil.fileexists(work_temp_folder + '/' + fileInByPages.replace('-0','-')):
            fileInByPages=fileInByPages.replace('-0','-')
        if pagesByNode==1:
            if FILEUtil.fileexists(work_temp_folder + '/' + FILEUtil.getFileName(file_output) + '-' + str(iPages) + FILEUtil.getFileExtension(file_output)):
                fileInByPages=FILEUtil.getFileName(file_output) + '-' + str(iPages) + FILEUtil.getFileExtension(file_output)
        if FILEUtil.fileexists(work_temp_folder + '/' + fileInByPages):
            # copy vao FTP
            FTPUtil.connect(ftp_private.ftp_ip, ftp_private.ftp_port, ftp_private.ftp_user, ftp_private.ftp_pwd, '')
            FTPUtil.makeFolder(ftp_folderUpload.replace('uploads/', ''))
            FTPUtil.connect(ftp_private.ftp_ip, ftp_private.ftp_port, ftp_private.ftp_user, ftp_private.ftp_pwd, ftp_folderUpload.replace('uploads/', ''))
            with open(work_temp_folder + '/' + fileInByPages, 'rb') as f:
                FTPUtil.uploadData((folderUpload + fileInByPages).replace('', ''),
                                   (fileInByPages).replace('uploads/', ''), f.read())
                f.close()
            noderequest = OCR_NodeRequest.objects.create()
            noderequest.node_id = node
            noderequest.request_id = ocrrequest
            noderequest.status = 0
            noderequest.file_ocr_input = fileInByPages
            noderequest.file_ocr_output = fileInByPages + 'output.pdf'
            noderequest.file_ocr_pages = len(Pdf.open(folderUpload + fileInByPages).pages)
            noderequest.file_ocr_page_start = pagesByNode * (iPages - 1) + 1
            noderequest.file_ocr_page_size = pagesByNode
            noderequest.save()

            nodesave = OCR_Nodes.objects.get(id=node.id)
            if nodesave.waiting_page is None:
                nodesave.waiting_page = 0
            nodesave.waiting_page = int(nodesave.waiting_page) + 1
            nodesave.save()

            FILEUtil.delfile(folderUpload + fileInByPages)
        else:
            print('Khong split duoc file '+work_temp_folder + '/' + fileInByPages)


def processMergeResults(ocrrequest, work_temp_folder, folderUpload, root_json_data):
    # private share FTP
    # download va merge ve uploads
    # abiword convert to WORD
    # upload public/client FTP tu upload
    if folderUpload[-1:]=='/':
        folderUpload=folderUpload[:len(folderUpload)-1]
    if folderUpload[-1:]=='/':
        folderUpload=folderUpload[:len(folderUpload)-1]
    if folderUpload[-1:]=='/':
        folderUpload=folderUpload[:len(folderUpload)-1]
    config = json.loads(ocrrequest.config_ocr)
    fileOutput = FILEUtil.getFileName(ocrrequest.file_ocr) + '_EPS_OCR_OUTPUT' + FILEUtil.getFileExtension(ocrrequest.file_ocr)
    pathOutput = ocrrequest.ftp_path
    tempPath = work_temp_folder
    tempFile = tempPath + '/' + 'xx.tmp'

    # noderequest da thanh cong
    noderequests = OCR_NodeRequest.objects.filter(Q(request_id=ocrrequest) & Q(status=2)).order_by('file_ocr_page_start')

    if len(noderequests) == 0:
        LOGUtil.log_error('No Node callback done.')

    FTPUtil.connect(config['ftp_ip'], config['ftp_port'], config['ftp_user'], config['ftp_pwd'], pathOutput)
    content_pdf = b''
    content_txt = ''
    content_xml = ''
    content_json = ''
    iPage = 0
    merger = PdfFileMerger()
    file_pages = []
    for noderequest in noderequests:
        # merge PDF, TXT, XML
        # noi tiep cac page => doi ten file
        if FTPUtil.isexist(noderequest.file_ocr_output)!='OK':
            print('FTP file is not exist')
            return
        FTPUtil.delete(FILEUtil.getFileBaseName(noderequest.file_ocr_input))
        # ghi file o temp thi merger loi
        FTPUtil.download(FILEUtil.getFileBaseName(noderequest.file_ocr_output), folderUpload+'/'+FILEUtil.getFileBaseName(noderequest.file_ocr_output))
        fd = open(folderUpload+'/'+FILEUtil.getFileBaseName(noderequest.file_ocr_output), 'rb')
        merger.append(fd)
        fd.close()
        FTPUtil.delete(FILEUtil.getFileBaseName(noderequest.file_ocr_output))
        FILEUtil.delfile(folderUpload+'/'+FILEUtil.getFileBaseName(noderequest.file_ocr_output))
        FTPUtil.download(FILEUtil.getFileName(noderequest.file_ocr_output) + '.txt', tempFile)
        with open(tempFile, 'r', encoding='utf-8') as f:
            content_txt = content_txt + f.read()
        FTPUtil.delete(FILEUtil.getFileName(noderequest.file_ocr_output) + '.txt')
        FTPUtil.download(FILEUtil.getFileName(noderequest.file_ocr_output) + '.xml', tempFile)
        with open(tempFile, 'r', encoding='utf-8') as f:
            content_xml = content_xml + f.read()
        FTPUtil.delete(FILEUtil.getFileName(noderequest.file_ocr_output) + '.xml')
        FTPUtil.download(FILEUtil.getFileName(noderequest.file_ocr_output) + '.json', tempFile)
        with open(tempFile, 'r', encoding='utf-8') as f:
            content_json = content_json + f.read()
        FTPUtil.delete(FILEUtil.getFileName(noderequest.file_ocr_output) + '.json')
        for i in range(noderequest.file_ocr_pages):
            FTPUtil.download(
                FILEUtil.getFileName(noderequest.file_ocr_output) + '_page_' + str(
                    i + 1) + '.txt',
                folderUpload + '/' + FILEUtil.getFileBaseName(fileOutput) + '_page_' + str(
                    iPage + 1) + '.txt')
            FTPUtil.delete(FILEUtil.getFileName(noderequest.file_ocr_output) + '_page_' + str(
                    i + 1) + '.txt')
            file_pages.append(folderUpload + '/' + FILEUtil.getFileBaseName(fileOutput) + '_page_' + str(
                    iPage + 1) + '.txt')
            FTPUtil.download(
                FILEUtil.getFileName(noderequest.file_ocr_output) + '_page_' + str(
                    i + 1) + '.png',
                folderUpload + '/' + FILEUtil.getFileBaseName(fileOutput) + '_page_' + str(
                    iPage + 1) + '.png')
            FTPUtil.delete(FILEUtil.getFileName(noderequest.file_ocr_output) + '_page_' + str(
                    i + 1) + '.png')
            file_pages.append(folderUpload + '/' + FILEUtil.getFileBaseName(fileOutput) + '_page_' + str(
                    iPage + 1) + '.png')
            FTPUtil.download(
                FILEUtil.getFileName(noderequest.file_ocr_output) + '_page_' + str(
                    i + 1) + '.json',
                folderUpload + '/' + FILEUtil.getFileBaseName(fileOutput) + '_page_' + str(
                    iPage + 1) + '.json')
            FTPUtil.delete(FILEUtil.getFileName(noderequest.file_ocr_output) + '_page_' + str(
                    i + 1) + '.json')
            file_pages.append(folderUpload + '/' + FILEUtil.getFileBaseName(fileOutput) + '_page_' + str(
                    iPage + 1) + '.json')

            iPage = iPage + 1

    # ghi merge ra file tam o uploads
    with open(folderUpload + '/' + FILEUtil.getFileName(fileOutput) + '.pdf', 'wb') as fout:
        merger.write(fout)

    # abiword
    #ret = CommonUtil.callprocess('abiword', '--to=docx "'+(folderUpload + '/' + FILEUtil.getFileName(fileOutput)).replace(' ', '*space*') + '.pdf"')
    # abiword not available on Windows
    # ret = subprocess.call('abiword --to=docx "'+(folderUpload + '/' + FILEUtil.getFileName(fileOutput)).replace(' ', ' ') + '.pdf"', shell=True)
    # content_doc=None
    # with open(folderUpload + '/' + FILEUtil.getFileName(fileOutput) + '.docx', 'rb') as fout:
    #     content_doc = fout.read()

    # doc du lieu merge tu file tam de put len FTP private
    with open(folderUpload + '/' + FILEUtil.getFileName(fileOutput) + '.pdf', 'rb') as fout:
        content_pdf = fout.read()
    with open(folderUpload + '/' + FILEUtil.getFileName(fileOutput) + '.txt', 'w', encoding='utf-8') as f:
        f.write(content_txt)
        f.close()
    with open(folderUpload + '/' + FILEUtil.getFileName(fileOutput) + '.txt', 'w', encoding='utf-8') as f:
        f.write(content_xml)
        f.close()
    with open(folderUpload + '/' + FILEUtil.getFileName(fileOutput) + '.txt', 'w', encoding='utf-8') as f:
        f.write(content_json)
        f.close()

    # del folder
    # FTPUtil.cdFolder('/')
    # FTPUtil.deleteFolder(pathOutput)
    # close share FTP
    FTPUtil.close()

    # upload len client FTP neu co
    if root_json_data['ftp_ip']!='':
        FTPUtil.connect(root_json_data['ftp_ip'], root_json_data['ftp_port'], root_json_data['ftp_user'], root_json_data['ftp_pwd'], root_json_data['client_folder'])

        FTPUtil.uploadData(tempFile, FILEUtil.getFileName(fileOutput) + '.pdf',
                           content_pdf)
        FTPUtil.uploadText(tempFile, FILEUtil.getFileName(fileOutput) + '.txt',
                           content_txt)
        FTPUtil.uploadText(tempFile, FILEUtil.getFileName(fileOutput) + '.xml',
                           content_xml)
        FTPUtil.uploadText(tempFile, FILEUtil.getFileName(fileOutput) + '.json',
                           content_json)
        FTPUtil.uploadData(tempFile, FILEUtil.getFileName(fileOutput) + '.docx',
                           content_doc)
        for file_page in file_pages:
            with open(file_page, 'rb') as f:
                FTPUtil.uploadData(tempFile, FILEUtil.getFileBaseName(file_page), f.read())

        FTPUtil.close()

    print(folderUpload)
    print(FILEUtil.getFileName(fileOutput) )
    #log file
    #copy vao uploads
    folderUploadRet = folderUpload #.replace(settings.BASE_DIR, '')
    from shutil import copyfile
    if LOGUtil.is_error:
        try:
            copyfile(LOGUtil.fileLog, folderUpload + '/errors.log')
        except:
            return [folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.json',
                    folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.txt',
                    folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.xml',
                    folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.docx',
                    folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.pdf', *file_pages]
            pass

        return [folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.json',
                folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.txt',
                folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.xml',
                folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.docx',
                folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.pdf',
                folderUploadRet + '/errors.log', *file_pages]
    else:
        return [folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.json',
                folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.txt',
                folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.xml',
                folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.docx',
                folderUploadRet + '/' + FILEUtil.getFileName(fileOutput) + '.pdf', *file_pages]


def createResultObjects(pdfs, file_links, image_names, master_link):
    ifile = 0
    file_output_name = ''
    results=[]
    if master_link[-1:]=='/':
        master_link=master_link[:len(master_link)-1]
    if master_link[-1:]=='/':
        master_link=master_link[:len(master_link)-1]
    if master_link[-1:]=='/':
        master_link=master_link[:len(master_link)-1]
    for pdf in pdfs:
        ifile=ifile+1

        _OCRresult = OCRResult()
        _OCRresult.file_number=ifile
        #print(file_links)
        if len(image_names)>ifile:
            _OCRresult.file_input=image_names[ifile]

        for file_link in file_links:
            if '.pdf_page_' in file_link:
                ocr_file = OCRResult.OCRFile()
                ocr_file.file_name = FILEUtil.getFileBaseName(file_link)
                ocr_file.file_link = (master_link + file_link).replace(settings.BASE_DIR, '').replace('/api/','').replace('/uploads/','/static/').replace('//','/').replace(':/','://').replace(':///','://')
                ocr_file.file_type = FILEUtil.getFileExtension(file_link)
                if FILEUtil.fileexists(file_link):
                    ocr_file.file_date = time.ctime(os.path.getctime(file_link))
                    ocr_file.file_size = os.path.getsize(file_link)

                # tao Page
                if FILEUtil.getFileExtension(file_link)=='.txt':
                    ipage = FILEUtil.getFileName(file_link).replace(file_output_name, '').split('.pdf_page_')[1]
                    ocr_page = OCRResult.OCRPage()
                    ocr_page.page_number = int(ipage)

                    ocr_page.page_files.append(ocr_file)

                    ocr_file_prev = _OCRresult.result_files[-1]
                    ocr_file_prev.result_pages.append(ocr_page)
                else: # add vao page
                    ocr_file_prev = _OCRresult.result_files[-1]
                    ocr_page=ocr_file_prev.result_pages[-1]
                    ocr_page.page_files.append(ocr_file)
            else:
                ocr_file = OCRResult.OCRFile()
                ocr_file.file_name = FILEUtil.getFileBaseName(file_link)
                ocr_file.file_link = (master_link + file_link).replace(settings.BASE_DIR, '').replace('/api/','').replace('/uploads/','/static/').replace('//','/').replace(':/','://').replace(':///','://')
                ocr_file.file_type = FILEUtil.getFileExtension(file_link)
                if FILEUtil.fileexists(file_link):
                    ocr_file.file_date = time.ctime(os.path.getctime(file_link))
                    ocr_file.file_size = os.path.getsize(file_link)
                file_output_name = FILEUtil.getFileName(file_link)

                _OCRresult.result_files.append(ocr_file)

        #results.append(_OCRresult)
        results.append(_OCRresult.toJSON())
    return results

def reasignAnotherNode(ocrrequest, noderequest, node_id_fail):
    if noderequest.id not in node_id_fail:
        node_id_fail.append(noderequest.id)
    q_objects = Q(id__in=[])
    for item in node_id_fail:
        q_objects.add(Q(pk=item), Q.AND)
    nodemin = OCR_NodeRequest.objects.exclude(q_objects).filter(Q(request_id=ocrrequest.id) & Q(status=1)).order_by('id').first()
    if not nodemin is None:
        noderequest.node_id = nodemin.node_id
        print('re-assign to ' + nodemin.node_id.url_api)
    else:
        # neu 1 trang vao api loi thi toi
        #nodeanother = OCR_Nodes.objects.exclude(Q(id=noderequest.node_id.id)).first()
        #noderequest = OCR_NodeRequest.objects.create()
        #noderequest.node_id = nodeanother
        print('re-assign to None')
        print(node_id_fail)
        nodemin = OCR_NodeRequest.objects.filter(Q(request_id=ocrrequest.id) & Q(status=1)).order_by('id').first()
        if not nodemin is None:
            noderequest.node_id = nodemin.node_id
        pass
    noderequest.status = 0
    noderequest.error_message = ''
    noderequest.access_time = datetime.datetime.now()
    nodesave = OCR_Nodes.objects.get(id=noderequest.node_id_id)
    if nodesave.waiting_page is None:
        nodesave.waiting_page = 0
    nodesave.waiting_page = int(nodesave.waiting_page) + 1
    nodesave.save()
    noderequest.save()
    return node_id_fail

def worker_init():
    """Initialize a process pool worker"""
    # Ignore SIGINT (our parent process will kill us gracefully)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

def worker_thread_init():
    pass

def get_api_pools(nodemaster, noderequests):
    for noderequest in noderequests:
        jsonData = json.loads(noderequest.request_id.config_ocr)
        print(noderequest.node_id.node_name)
        jsonData['api_callback'] = nodemaster.url_callback
        jsonData['client_folder'] = noderequest.request_id.ftp_path
        jsonData['image_names'] = [noderequest.file_ocr_input]
        jsonData['file_input'] = noderequest.file_ocr_input
        jsonData['file_output'] = noderequest.file_ocr_output
        jsonData['noderequest_id'] = noderequest.id
        noderequest.status=1
        noderequest.save()

        yield ApiParam(url_api=noderequest.node_id.url_api, jsonData=jsonData)

