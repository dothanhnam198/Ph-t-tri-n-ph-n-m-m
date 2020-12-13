import logging
import multiprocessing
import os
import gc
import signal
import sys
import threading
from collections import namedtuple

import pikepdf
import requests
from builtins import Exception
from tempfile import mkdtemp

import os
import io
import json
import base64
import cv2
import numpy as np
import datetime
import img2pdf
from pikepdf import Pdf, PdfImage, Name
from pdf2image import convert_from_bytes
from django.core.files.base import ContentFile


from django.shortcuts import render
from django.http.response import JsonResponse
from django.http import HttpResponse
from django.views.generic.base import View, TemplateView
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageFilter, ImageFont, ImageDraw, ImageEnhance

#from tesserocr import PyTessBaseAPI, RIL, PSM, OEM, iterate_level

from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.generics import CreateAPIView, GenericAPIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.db.models import Q, F
import json
import datetime
from rest_framework.permissions import IsAuthenticated, AllowAny

from PyPDF2 import PdfFileWriter, PdfFileReader, PdfFileMerger

# Create your views here.
from .DjangoUtility import *
from .apimaster import *
from .models import *
from .serializers import *


class OcrFormView(TemplateView):
    template_name = 'ocr_form.html'
ocr_form_view = OcrFormView.as_view()


class OcrView(View):
    def ReturnResponse(self, starttime, utf8_text, totalfiles, totalpages, status):
        utf8_text = utf8_text + str((datetime.datetime.now() - starttime).total_seconds()) + 's.'+str(totalfiles) + ' files và '+str(totalpages) + ' pages.'
        #status = 'Thông báo: Do hệ thống đang demo với giới hạn 10 file hoặc 10 trang nhận dạng nên vui lòng thực hiện lại với file khác.'
        return JsonResponse({'timeexecute': utf8_text, 'results': [], 'status': status})

    def post(self, request, *args, **kwargs):
        print("POST OCR VIEW ocr")
        """
        input: lang: vie+eng, spell, PSM, OEM, ICom, Images, PDFs, areas, out-stt/all, out-type-pdf/text/json/xml
        input: deskew, clear background, clean final, pdf_renderer, lossless_reconstruction,

        logic:
        - client upload file vao FTP client, gui FTP client cho server
            hoac upload vao folder uploads cua server, hoac nhung noi dung base64 trong json request
        - server nhan request
        - doc noi dung file PDF/images (se chuyen thanh PDF) tu json hoac trong uploads hoac trong FTP client vao list PDF
        - voi moi noi dung trong list split PDF thanh cac file PDF voi so Node xu ly
        - upload len FTP share cua cac Node
        - tao cac du lieu request, noderequest
        - goi API cua cac Nodes
        - xu ly chuyen Node bi loi
        - OCR xong het thi merge files va ghi ve uploads + link list
        - neu co FTP client thi upload files
        - don dep temp/FTP share
        - callback lai client neu co

        """

        ipage = 1
        totalpage = 1
        pdfs = list()
        imagepdf = None
        results:OCRResult = []

        json_data = json.loads(str(request.POST['inputOCR']))
        try:
            starttime = datetime.datetime.now()
            utf8_text=''
            """
            tao images => PDF => PDFS
            tao Base64PDFS => PDFS            
            """
            # tao temp folder
            nodemaster = OCR_Nodes.objects.filter(Q(is_master=1) & Q(is_active=1)).first()
            work_temp_folder = mkdtemp(prefix="com.django-restfull.ocrmypdf.")
            folderUpload = 'uploads/' + json_data['temp_ocr_folder'] + '/'
            ftp_folderUpload = '/' + json_data['temp_ocr_folder'] + '/'
            folderUpload = os.path.join(settings.BASE_DIR, folderUpload)

            LOGUtil.log_reset(work_temp_folder+'/errors.log')
            LOGUtil.log_print(work_temp_folder)

            if not isinstance(json_data['file_input'], list):
                json_data['file_input'] = [json_data['file_input']]
                json_data['file_output'] = [json_data['file_output']]

            # ghi tu images, file_inputs
            # xu ly trang voi images TIFF
            pdfs, json_data = readListPDFOrImages(json_data, work_temp_folder, folderUpload)

            #ghi private FTP
            ftp_private, json_data = readPrivateFTP(json_data)

            # tao queue Node tu db request tu list files
            # list file ocr, split file => requests
            ipdf = 0
            totalpage = len(pdfs)
            countOfNodes = 0
            file_links = []
            # limit 10 pdfs, 10 pages
            print(totalpage)
            if totalpage > 10:
                #return self.ReturnResponse(starttime, utf8_text, totalpage, totalpage, 'Thông báo: Do hệ thống đang demo với giới hạn 10 file hoặc 10 trang nhận dạng nên vui lòng thực hiện lại với file khác.')
                pass
            if totalpage == 0:
                return self.ReturnResponse(starttime, utf8_text, totalpage, totalpage, 'Thông báo: Vui lòng chọn file ảnh hoặc scanned PDF')
            for pdf in pdfs:
                input_file, ocrrequest = createOCRRequest(json_data, ipdf)
                if ocrrequest is None:
                    continue

                #split file tren folder upload, copy ve FTP share
                orderbyList = ['waiting_page', '-cpu_no', 'time_avg_page']
                nodes = OCR_Nodes.objects.filter(Q(is_active=1) & (Q(is_master=0) | Q(is_master=None))).order_by(*orderbyList)
                for node in nodes:
                    print(node.url_api)
                countOfNodes = nodes.count()
                if not FILEUtil.fileexists(folderUpload+input_file):
                    with open(folderUpload+input_file, 'wb') as f:
                        f.write(pdf)
                countOfPages = len(Pdf.open(folderUpload+input_file).pages)
                totalpage = totalpage + countOfPages
                if countOfPages > 10:
                    #return self.ReturnResponse(starttime, utf8_text, totalpage, countOfPages, 'Thông báo: Do hệ thống đang demo với giới hạn 10 file hoặc 10 trang nhận dạng nên vui lòng thực hiện lại với file khác.')
                    pass
                pagesByNode = int(RoundUP(countOfPages / countOfNodes))
                cmd = 'qpdf --split-pages='+str(pagesByNode)+' "'+(folderUpload+input_file+'" "'+work_temp_folder+'/'+json_data['file_output'][ipdf]).replace(' ', ' ')+'"'
                try:
                    process = subprocess.call(cmd, shell=True)
                except:
                    pass
                LOGUtil.log_print('countOfPages')
                LOGUtil.log_print(countOfPages)
                LOGUtil.log_print(pagesByNode)
                LOGUtil.log_print(cmd)

                url_callback = json_data['api_callback']
                print(url_callback)
                timeavg = 0.0
                for node in nodes:
                    if not node.time_avg_page is None and timeavg < node.time_avg_page:
                        timeavg = float(node.time_avg_page)
                import requests
                cmd = ''
                if 'cmd=callback' not in url_callback:
                    cmd = 'cmd=callback&'
                if '?' in url_callback:
                    response = requests.get(str(url_callback) + '&' + cmd + 'progress=OK&start_time=' + str(time.time()) + '&total_page=' + str(totalpage) + '&avgtime=' + str(timeavg))
                else:
                    response = requests.get(str(url_callback) + '?' + cmd + 'progress=OK&start_time=' + str(time.time()) + '&total_page=' + str(totalpage) + '&avgtime=' + str(timeavg))

                # tao cac noderequest
                createOCRNodeRequestFromSplitted(nodes, json_data, work_temp_folder, folderUpload, ftp_folderUpload, pagesByNode, countOfPages, ftp_private, ocrrequest, ipdf)

                ipdf = ipdf + 1

                node_id_fail = []

                # chay queue Node cua request: -1: loi, 0/None=moi, 1: dang xu ly 2: success
                while True:
                    noderequests = OCR_NodeRequest.objects.filter(Q(request_id=ocrrequest.id) & (Q(status=0) | Q(status=-1)))

                    if len(noderequests) == 0:
                        root_json_data = json.loads(str(request.POST['inputOCR']))
                        file_merge_links = processMergeResults(ocrrequest, work_temp_folder, folderUpload, root_json_data)
                        if not file_merge_links is None:
                            file_links = [*file_links, *file_merge_links]
                        else:
                            LOGUtil.log_error('file_merge_links None, kg co file merge')
                        break
                    else:
                        if False:
                            from multiprocessing.dummy import Pool

                            initializer = worker_thread_init
                        else:
                            Pool = multiprocessing.Pool
                            initializer = worker_init
                        count_errors = 0
                        with Pool(
                                processes=len(noderequests), initializer=initializer, initargs=()
                        ) as pool:
                            # Phongnh: thuc hien xu ly song song
                            results = pool.imap_unordered(exec_api_sync, get_api_pools(nodemaster, noderequests))
                            while True:
                                try:
                                    page_result = results.next()

                                    id = page_result.options['noderequest_id']
                                    noderequest = OCR_NodeRequest.objects.get(id=id)

                                    LOGUtil.log_print(datetime.datetime.now())
                                    gc.collect()
                                    if page_result.error:
                                        count_errors=count_errors+1
                                        if count_errors>20:
                                            LOGUtil.log_print('Max retries exceeded errors')
                                            break
                                        id = page_result.options['noderequest_id']
                                        noderequest = OCR_NodeRequest.objects.filter(id=id).first()
                                        if noderequest:
                                            # lay node thuc hien nhanh, it
                                            LOGUtil.log_print('reasignAnotherNode')
                                            LOGUtil.log_print(page_result.text)
                                            node_id_fail = reasignAnotherNode(ocrrequest, noderequest, node_id_fail)
                                        else:
                                            pass
                                    else:
                                        # OCR xong, check trang thai, xu ly merge files
                                        pass

                                except StopIteration:
                                    break
                                except (Exception, KeyboardInterrupt) as e:
                                    LOGUtil.log_print('terminate')
                                    pool.terminate()
                                    raise

            result=None

            # set link output +
            results = createResultObjects(pdfs, file_links, json_data['image_names'], nodemaster.url_api)

            for fileTemp in json_data['image_names']:
                if FILEUtil.fileexists(folderUpload+'/'+fileTemp + '.image'):
                    FILEUtil.delfile(folderUpload+'/'+fileTemp)
                    FILEUtil.renameFile(folderUpload+'/'+fileTemp + '.image',folderUpload+'/'+fileTemp)

            # cleanup temp
            FILEUtil.removeFolder(work_temp_folder)

        except Exception as e:
            import traceback
            LOGUtil.log_error(str(traceback.format_exc()))
            utf8_text=utf8_text+'<br>'+('eeerrrr')
            utf8_text=utf8_text+'<br>'+(str(e))
            LOGUtil.log_error(e)
            results=[]

        utf8_text = utf8_text+str((datetime.datetime.now()-starttime).total_seconds())+' giây / '+str(len(pdfs))+' file. ' + str(totalpage) + ' trang cho ' + str(countOfNodes) + ' OCRNode xử lý';

        if (json_data['api_callback'] + '') != '':
            try:
                print('CALLBACK '+json_data['api_callback'])
                cmd = ''
                if 'cmd=callback' not in json_data['api_callback']:
                    cmd = 'cmd=callback&'
                response = requests.post(json_data['api_callback'] + '&' + cmd + 'status=OK&status_done='+utf8_text, json=results)
                # cleanup upload
                # FILEUtil.removeFolder(folderUpload)
                if str(response.status_code)!='OK':
                    return JsonResponse({'timeexecute': utf8_text, 'results': [], 'status':response.text })
                else:
                    return JsonResponse({'timeexecute': utf8_text, 'results': [], 'status':'OK' })
            except Exception as e:
                return JsonResponse({'timeexecute': utf8_text, 'results': [], 'status':str(e)})
        else:
            return JsonResponse({'timeexecute': utf8_text, 'results': results, 'status':'OK' })
ocr_api_view = csrf_exempt(OcrView.as_view())


class CallbackAPIView(ListCreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    serializer_class = OCR_NodesSerializer
    queryset = OCR_Nodes.objects.all()

    def post(self, request):
        cmd = request.query_params.get('cmd')
        print("POST CALLBACK VIEW " + str(cmd))
        json_data = []
        try:
            json_data = json.loads(str(request.POST['inputFile']))
        except:
            json_data = json.loads(str(request.data['inputFile']))
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        uploadFolder = os.path.join(BASE_DIR, 'uploads')
        uploadFile = os.path.join(uploadFolder, json_data['folder'], json_data['filename'])
        ret=[]
        # neu chua co folder=>make
        if not FILEUtil.fileexists( os.path.join(uploadFolder, json_data['folder'])):
            try:
                os.mkdir( os.path.join(uploadFolder, json_data['folder']), 0o700)
            except:
                pass

        if cmd=='uploadstart':
            FILEUtil.generate_big_sparse_file(uploadFile, json_data['size'])
            return JsonResponse({'done': 1, 'trunkno': -1})
        if cmd == 'uploadtrunk':
            trunkdata = CommonUtil.fromBase64ToByte(json_data['trunk'])
            FILEUtil.writechunk2file(uploadFile, trunkdata, json_data['trunkstart'])
            return JsonResponse({'done': 1, 'trunkno': json_data['trunkno']})

        return JsonResponse({'done':1})

    def get(self, request):
        cmd = request.query_params.get('cmd')
        print("GET CALLBACK VIEW " + cmd)

        #test
        if not True:
            nodes = OCR_Nodes.objects.filter(Q(is_active=1) & (Q(is_master=0) | Q(is_master=None)))
            if len(nodes) < 10:
                for i in range(1, 10):
                    node = nodes.first()
                    print(node)
                    print(i)
                    nodex = OCR_Nodes.objects.create()
                    nodex.node_name = node.node_name + ' instance ' + str(i)
                    port = str(i)
                    if len(port) == 1:
                        port = '0' + port
                    nodex.url_api = node.url_api.replace(':8001', ':80' + port)
                    if not node.url_callback is None:
                        nodex.url_callback = node.url_callback.replace(':8001', ':80' + port)
                    nodex.api_user = node.api_user
                    nodex.api_pwd = node.api_pwd
                    nodex.is_master = node.is_master
                    nodex.is_active = node.is_active
                    nodex.save()

        if cmd=='get_ftp':
            ftp_public = OCR_Config.objects.filter(is_public_ftp=1).first()
            client_ip = request.META['REMOTE_ADDR']
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            uploadFolder = os.path.join(BASE_DIR, 'uploads')
            client_folder = mkdtemp(prefix="eps.restful.ocr."+client_ip+".", dir=uploadFolder)
            client_folder = FILEUtil.getFileBaseName(client_folder)
            ocrfolder = OCR_Folder.objects.create()
            ocrfolder.client_info = client_ip
            ocrfolder.folder = client_folder
            ocrfolder.create_time = datetime.datetime.now()
            ocrfolder.save()
            def threadRemoveOldFolder(uploadFolder, foldername):
                ocrfolders = OCR_Folder.objects.all()
                for ocrfolder in ocrfolders:
                    if not ocrfolder is None and ocrfolder.create_time<datetime.date.today()-datetime.timedelta(days=1):
                        foldername=ocrfolder.folder
                        FILEUtil.removeFolder(os.path.join(uploadFolder, foldername))
                        ocrfolder.delete()
                pass
            threadRemove = threading.Thread(target=threadRemoveOldFolder, args=(uploadFolder, client_folder))
            threadRemove.start()

            if ftp_public:
                return JsonResponse({'ftp_ip': ftp_public.ftp_ip, 'ftp_port': ftp_public.ftp_port, 'ftp_user': ftp_public.ftp_user, 'ftp_pwd': ftp_public.ftp_pwd, 'client_folder': client_folder})
            else:
                return JsonResponse({'ftp_ip': '', 'ftp_port': '', 'ftp_user': '', 'ftp_pwd': '', 'client_folder': client_folder})

        elif cmd=='callback':
            noderequest_id = request.query_params.get('id')
            status = request.query_params.get('status')
            if noderequest_id is None:
                print('callback null wrong')
            else:
                noderequest = OCR_NodeRequest.objects.filter(id=noderequest_id).first()
                if noderequest:
                    if status is None:
                        progress = request.query_params.get('progress')
                        start_time = request.query_params.get('start_time')
                        page_time = request.query_params.get('page_time')
                        page_no = request.query_params.get('page_no')
                        cpu_no = request.query_params.get('cpu_no')
                        node_name = noderequest.node_id.node_name
                        url_callback = json.loads(str(noderequest.request_id.config_ocr))['api_callback']

                        nodesave = OCR_Nodes.objects.get(id=noderequest.node_id_id)
                        if nodesave.time_avg_page is None or nodesave.time_avg_page == 0:
                            if not page_no is None:
                                nodesave.time_avg_page = (float(page_time) - float(start_time)) / (int(page_no) + 1)
                        else:
                            if not page_no is None:
                                nodesave.time_avg_page = (float(nodesave.time_avg_page) + (float(page_time) - float(start_time)) / (int(page_no) + 1)) / 2
                        if not cpu_no is None and int(cpu_no) != 0:
                            nodesave.cpu_no = int(cpu_no)
                        nodesave.save()

                        import requests
                        cmd=''
                        if 'cmd=callback' not in url_callback:
                            cmd='cmd=callback&'
                        if '?' in url_callback:
                            response = requests.get(str(url_callback) + '&' + cmd + 'progress=OK&start_time=' + str(start_time) + '&page_time=' + str(page_time) + '&page_no=' + str(page_no) + '&node_name=' + str(node_name))
                        else:
                            response = requests.get(str(url_callback) + '?' + cmd + 'progress=OK&start_time=' + str(start_time) + '&page_time=' + str(page_time) + '&page_no=' + str(page_no) + '&node_name=' + str(node_name))
                    else:
                        if status=='OK':
                            noderequest.status = 2
                            noderequest.error_message = ''
                            noderequest.access_time = datetime.datetime.now()
                        else:
                            noderequest.status = -1
                            noderequest.error_message = status
                            noderequest.access_time = datetime.datetime.now()
                        noderequest.save()

                        nodesave = OCR_Nodes.objects.get(id=noderequest.node_id_id)
                        if nodesave.waiting_page is None:
                            nodesave.waiting_page = 0
                        nodesave.waiting_page = int(nodesave.waiting_page) - 1
                        nodesave.save()
                else:
                    print('Not found NodeRequest = ' + str(noderequest_id))

            return JsonResponse({'timeexecute': 1});
        else:
            return JsonResponse({'timeexecute': 1});
callback_api_view = csrf_exempt(CallbackAPIView.as_view())



class FtpAPIView(ListCreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        cmd = request.query_params.get('cmd')
        print("POST FTP VIEW " + str(cmd))
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        uploadFolder = os.path.join(BASE_DIR, 'uploads/ftp')
        uploadFile = ''
        if 'folder' in request.POST:
            uploadFile = os.path.join(BASE_DIR, CommonUtil.removeSlash('uploads/ftp/'+str(request.POST['folder'])+'/'+str(request.POST['filename'])))
        uploadFile = uploadFile.replace('//', '/')
        ret=[]

        # neu chua co folder=>make
        if not FILEUtil.fileexists(uploadFolder):
            try:
                os.mkdir(uploadFolder, 0o700)
            except:
                import traceback
                print(traceback.format_exc())
                pass
        if 'folder' in request.POST:
            if not FILEUtil.fileexists(os.path.join(uploadFolder, CommonUtil.removeSlash(request.POST['folder']))):
                try:
                    os.mkdir(os.path.join(uploadFolder, str(request.POST['folder'])), 0o700)
                except:
                    import traceback
                    print(traceback.format_exc())
                    pass

        if cmd=='upload':
            if str(request.POST['pos']) == '0':
                FILEUtil.generate_big_sparse_file(uploadFile, int(request.POST['size']))
            try:
                trunkdata = CommonUtil.fromBase64ToByte(request.POST['chunk'])
                FILEUtil.writechunk2file(uploadFile, trunkdata, int(request.POST['pos']))
            except:
                import traceback
                print(traceback.format_exc())


        return HttpResponse('OK')

    def get(self, request):
        cmd = request.query_params.get('cmd')
        print("GET FTP VIEW " + str(cmd))
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        uploadFolder = os.path.join(BASE_DIR, 'uploads/ftp')
        # neu chua co folder=>make
        if not FILEUtil.fileexists(os.path.join(uploadFolder, '')):
            try:
                os.mkdir(os.path.join(uploadFolder, ''), 0o700)
            except:
                pass
        if not request.query_params.get('folder') is None:
            if not FILEUtil.fileexists(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')))):
                try:
                    os.mkdir(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder'))), 0o700)
                except:
                    pass

        if cmd=='download':
            if FILEUtil.fileexists(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file')))):
                with open(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file'))), 'rb') as f:
                    return HttpResponse(f.read())
            else:
                return HttpResponse('')
        elif cmd=='makeFolder':
            if not FILEUtil.fileexists(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')))):
                try:
                    os.mkdir(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder'))), 0o700)
                except:
                    pass
            return HttpResponse('OK')
        elif cmd=='deleteFolder':
            if FILEUtil.fileexists(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')))):
                try:
                    FILEUtil.removeFolder(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder'))))
                except:
                    pass
            return HttpResponse('OK')
        elif cmd=='rename':
            if FILEUtil.fileexists(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file_to')))):
                try:
                    FILEUtil.delfile(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file_to'))))
                except:
                    pass
            FILEUtil.renameFile(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file_from'))), os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file_to'))))
            return HttpResponse('OK')
        elif cmd=='delete':
            if FILEUtil.fileexists(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file')))):
                try:
                    FILEUtil.delfile(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file'))))
                except:
                    pass
            return HttpResponse('OK')
        elif cmd=='isexist':
            if not FILEUtil.fileexists(os.path.join(uploadFolder, CommonUtil.removeSlash(request.query_params.get('folder')), CommonUtil.removeSlash(request.query_params.get('file')))):
                return HttpResponse('NotOK')
            else:
                return HttpResponse('OK')
        else:
            return HttpResponse('NotOK')
ftp_api_view = csrf_exempt(FtpAPIView.as_view())


