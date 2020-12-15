import logging
import os
import sys
import requests
from builtins import Exception
from tempfile import mkdtemp

from rest_framework.permissions import AllowAny

from .ocrmypdf import __version__
from .ocrmypdf._jobcontext import make_logger
from .ocrmypdf._sync import run_pipeline, cleanup_working_folder
from .ocrmypdf._validation import check_closed_streams, check_options
from .ocrmypdf.api import Verbosity, configure_logging
from .ocrmypdf.cli import parser
from .ocrmypdf.exceptions import BadArgsError, ExitCode, MissingDependencyError

import time
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
from django.views.generic.base import View, TemplateView
from django.views.decorators.csrf import csrf_exempt
from PIL import Image, ImageFilter, ImageFont, ImageDraw, ImageEnhance

#from tesserocr import PyTessBaseAPI, RIL, PSM, OEM, iterate_level
from rest_framework.generics import ListCreateAPIView

# Create your views here.
from .DjangoUtility import *


class OCRResult():
    class OCRPage():
        def __init__(self):
            self.page_number=0
            self.page_text=''
            self.page_json=''
    def __init__(self):
        self.filename = ''
        self.output_pdf = ''
        self.output_text = ''
        self.output_json = ''
        self.output_xml = ''
        self.output_pages: OCRResult.OCRPage = []

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)


class OcrFormView(TemplateView):
    template_name = 'ocr_form.html'
ocr_form_view = OcrFormView.as_view()


class OcrView(ListCreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def base64_image(self, data, name=None):
        _format, _img_str = data.split(';base64,')
        _name, ext = _format.split('/')
        if not name:
            name = _name.split(":")[-1]
        stream = io.BytesIO(base64.b64decode(_img_str))

        return Image.open(stream)

    def base64_blob(self, data, name=None):
        _format, _img_str = data.split(';base64,')
        _name, ext = _format.split('/')
        if not name:
            name = _name.split(":")[-1]
        stream = io.BytesIO(base64.b64decode(_img_str))

        return stream

    def fileimage_as_base64(self, image_file, format='png'):
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

    def image_as_base64(self, image:Image):
        encoded_string = ''
        format = 'png'
        imgByteArr = io.BytesIO()
        image.save(imgByteArr, format=format)
        imgByteArr = imgByteArr.getvalue()
        encoded_string = base64.b64encode(imgByteArr)
        return 'data:image/%s;base64,%s' % (format, encoded_string.decode('ascii'))

    def ocr(self, api, image:Image, area, rootimage:Image, component):
        try:
            utf8_text=''

            api.SetImage(image)

            api.Recognize()

            utf8_text = utf8_text + '<br>' + api.GetUTF8Text()

            # utf8_text = api.AllWordConfidences()

            #boxes = api.GetComponentImages(RIL.TEXTLINE, True)
            boxes = api.GetComponentImages(int(component), True)
            if not boxes is None:
                utf8_text = utf8_text + '<br>' + ('Found {} image components.'.format(len(boxes)))
                for i, (im, box, _, _) in enumerate(boxes):
                    # im is a PIL image object
                    # box is a dict with x, y, w and h keys)

                    # widening the box with delta can greatly improve the text output
                    delta = image.size[0] / 200
                    api.SetRectangle(box['x'] - delta, box['y'] - delta, box['w'] + 2 * delta, box['h'] + 2 * delta)
                    # api.SetRectangle(box['x'], box['y'], box['w'], box['h'])

                    ocrResult = api.GetUTF8Text()
                    conf = api.MeanTextConf()

                    if (ocrResult+'').strip() != '' or True:
                        # draw frames
                        draw = ImageDraw.Draw(rootimage)
                        if area is None:
                            realx = box['x']
                            realy = box['y']
                            realx2 = box['x'] + box['w']
                            realy2 = box['y'] + box['h']
                        else:
                            realx = area[0] + box['x']
                            realy = area[1] + box['y']
                            realx2 = area[0] + box['x'] + box['w']
                            realy2 = area[1] + box['y'] + box['h']

                        #draw.rectangle(((area[0]+box['x'], area[1]+box['y']), (area[0]+box['x']+box['w'], area[1]+box['y']+box['h'])), fill="white")
                        draw.line((realx, realy, realx, realy2), fill="red", width=5)
                        draw.line((realx, realy, realx2, realy), fill="red", width=5)
                        draw.line((realx2, realy, realx2, realy2), fill="red", width=5)
                        draw.line((realx, realy2, realx2, realy2), fill="red", width=5)

                        utf8_text = utf8_text + '<br>' + (u"Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
                                                          "confidence: {1}, text: {2}".format(i, conf, ocrResult, **box))
            """
            ri = api.GetIterator()
            for r in iterate_level(ri, RIL.WORD):
                # rectangle
                print(r.BoundingBox(RIL.WORD))
                # text
                print(r.GetUTF8Text(RIL.WORD))
            """
            it = api.AnalyseLayout()
            if not it is None:
                orientation, direction, order, deskew_angle = it.Orientation()
                utf8_text = utf8_text + '<br>' + ('Orientation: {:d}'.format(orientation))
                utf8_text = utf8_text + '<br>' + ('WritingDirection: {:d}'.format(direction))
                utf8_text = utf8_text + '<br>' + ('TextlineOrder: {:d}'.format(order))
                utf8_text = utf8_text + '<br>' + ('Deskew angle: {:.4f}'.format(deskew_angle))

        except Exception as e:
            print('ppppppppppp')
            print(e)
            utf8_text = utf8_text + '<br>' + ('er')
            utf8_text = utf8_text + '<br>' + (str(e))

        return utf8_text

    def preprocessimage(self, sharpened_image:Image):
        # 1. resize
        image = np.asarray(sharpened_image)
        try:
            width, height = sharpened_image.size
            scale = width / width
            image = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
            #image = cv2.resize(image, (int(width/2), int(height/2)), interpolation=cv2.INTER_AREA)

            # 2. Converting image to grayscale:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # 3. Applying dilation and erosion to remove the noise (you may play with the kernel size depending on your data set):
            kernel = np.ones((1, 1), np.uint8)
            image = cv2.dilate(image, kernel, iterations=1)
            image = cv2.erode(image, kernel, iterations=1)
            # 4.Applying blur, which can be done by using one of the following lines (each of which has its pros and cons, however, median blur and bilateral filter usually perform better than gaussian blur.):
            cv2.threshold(cv2.GaussianBlur(image, (5, 5), 0), 0, 255,
                          cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            cv2.threshold(cv2.bilateralFilter(image, 5, 75, 75), 0, 255,
                          cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            cv2.threshold(cv2.medianBlur(image, 3), 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            cv2.adaptiveThreshold(cv2.GaussianBlur(image, (5, 5), 0), 255,
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
            cv2.adaptiveThreshold(cv2.bilateralFilter(image, 9, 75, 75), 255,
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
            cv2.adaptiveThreshold(cv2.medianBlur(image, 3), 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 31, 2)
        except Exception as ex:
            print('ex in preprocessing')
            print(ex)

        print(image.shape)

        return Image.fromarray(image)

    def run_ocrmypdf(self,options):

        if not check_closed_streams(options):
            return ExitCode.bad_args

        if hasattr(os, 'nice'):
            os.nice(5)

        verbosity = options.verbose
        if not os.isatty(sys.stderr.fileno()):
            options.progress_bar = False
        if options.quiet:
            verbosity = Verbosity.quiet
            options.progress_bar = False
        configure_logging(
            verbosity, progress_bar_friendly=options.progress_bar, manage_root_logger=True
        )
        log = make_logger('ocrmypdf')
        log.debug('ocrmypdf ' + __version__)
        try:
            check_options(options)
        except ValueError as e:
            log.error(e)
            return ExitCode.bad_args
        except BadArgsError as e:
            log.error(e)
            return e.exit_code
        except MissingDependencyError as e:
            log.error(e)
            return ExitCode.missing_dependency

        result = run_pipeline(options=options)
        return result

    def post(self, request):
        """
        input: lang: vie+eng, spell, PSM, OEM, ICom, Images, PDFs, areas, out-stt/all, out-type-pdf/text/json/xml
        input: deskew, clear background, clean final, pdf_renderer, lossless_reconstruction,
        """
        ipage = 1
        totalpage = 1
        pdfs = list()
        imagepdf = None
        start_time=time.time()
        results:OCRResult = []
        if not 'inputOCR' in request.POST:
            return JsonResponse({'a':1})
        json_data = json.loads(str(request.POST['inputOCR']))
        #goi ra internet can doi lai IP public cua OCRMaster
        #json_data = json.loads(str(request.POST['inputOCR']).replace('/10.0.0.56:9002', '/14.248.83.163:9004').replace('/10.0.0.56', '/14.248.83.163'))
        errorLog = ''

        try:
            starttime = datetime.datetime.now()
            utf8_text=''
            """
            tao images => PDF => PDFS
            tao Base64PDFS => PDFS            
            """
            ifile=0
            #print(json_data)
            if json_data['images'] is None:
                json_data['images']=[]

            for img in json_data['images']:
                if not img is None:
                    if str(img).find('data:application/pdf;') >= 0:
                        # append base64PDF => binary PDFS
                        pdfs.append(self.base64_blob(img).read())
                    elif str(img).find('data:image') >= 0:
                        with self.base64_image(img) as image:
                            # This create a single page PDF
                            dpi = 200
                            layout_fun = img2pdf.get_fixed_dpi_layout_fun((dpi, dpi))
                            imagepdf=img2pdf.convert(self.base64_blob(img).read(), with_pdfrw=True, layout_fun=layout_fun)#, outputstream=imagepdf)

                            if not imagepdf is None:
                                pdfs.append(imagepdf)

            #tao option ocr chung
            options = parser.parse_args(args=None)

            options.tessdata_path = '/usr/share/tesseract-ocr/4.00/tessdata/'
            options.client_folder=json_data['client_folder']
            options.page_number = ''
            if json_data['page_number'] != '':
                options.page_number = json_data['page_number']
            options.page_number=','+str(options.page_number)+','
            options.page_number=options.page_number.replace(' ','')
            options.config_template = None
            if json_data['templates'] != '' and len(json_data['templates'])>0:
                options.config_template = json_data['templates']
            options.language = [str(json_data['lang'])]
            if json_data['lang']!='eng':
                options.language.append('eng')
            options.deskew = False
            if json_data['deskew'] != '':
                options.deskew = True
            options.remove_background = False
            if json_data['remove_background'] != '':
                options.remove_background = True
            options.clean = False
            if json_data['clean'] != '':
                options.clean = True
            options.clean_final = False
            if json_data['clean_final'] != '':
                options.clean_final = True
            if os.name == 'nt':
                options.clean = False
                options.clean_final = False
            options.tesseract_oem = None
            if json_data['OEM'] != '':
                options.tesseract_oem = int(json_data['OEM'])
            options.tesseract_pagesegmode = None
            if json_data['PSM'] != '':
                options.tesseract_pagesegmode = int(json_data['PSM'])
            options.user_words = None
            options.author='EPS-OCR'
            options.jbig2_lossy = False
            options.keep_temporary_files = False
            options.oversample = 1
            options.png_quality = 1
            options.quiet = True
            options.remove_vectors = True
            options.rotate_pages = True
            options.rotate_pages_threshold = 14.0
            options.subject = 'EPS'
            options.threshold = True
            options.title = 'None'
            #options.use_threads = not False
            options.verbose = 1
            options.force_ocr = True
            #options.redo_ocr = not False
            #options.skip_text = not False
            # options.pdf_renderer='hocr'
            options.api_callback=str(json_data['api_callback']) + ''
            options.noderequest_id=str(json_data['noderequest_id']) + ''
            options.start_time=start_time

            options.work_temp_folder = mkdtemp(prefix="com.django-restfull.ocrmypdf.")

            # doc tu FTP
            if not json_data['file_input'] is None and str(json_data['file_input'])!='':
                input_file=json_data['file_input']
                fileTemp=options.work_temp_folder+'/'+input_file
                if json_data['ftp_ip']+''=='':
                    fileTemp=input_file
                    with open(fileTemp, 'rb') as f:
                        data = f.read()
                        pdfs.append(data)                
                else:
                    FTPUtil.connect(json_data['ftp_ip'], json_data['ftp_port'], json_data['ftp_user'], json_data['ftp_pwd'], json_data['client_folder'])
                    FTPUtil.download(input_file, fileTemp)
                    if FILEUtil.getFileExtension(input_file)=='.pdf':
                        # append base64PDF => binary PDFS
                        with open(fileTemp, 'rb') as f:
                            data = f.read()
                            pdfs.append(data)
                    else:
                        with open(fileTemp, 'rb') as f:
                            # This create a single page PDF
                            dpi = 200
                            layout_fun = img2pdf.get_fixed_dpi_layout_fun((dpi, dpi))
                            imagepdf = img2pdf.convert(f.read(), with_pdfrw=True, layout_fun=layout_fun)  # , outputstream=imagepdf)

                            if not imagepdf is None:
                                pdfs.append(imagepdf)

            ipdf = 0
            totalpage = len(pdfs)
            for pdf in pdfs:
                ipdf = ipdf + 1
                options.result_pdf = None
                options.result_text = ''
                options.result_data = ''
                options.result_templatedata_json = ''
                options.result_templatedata_xml = ''
                options.result_pages = []
                options.input_file = options.work_temp_folder+'/'+'pdf_input_'+str(ipdf)+'.pdf'
                if len(pdfs)>1:
                    options.output_file = options.work_temp_folder.replace('/tmp/','')+'_'+'pdf_output_'+str(ipdf)+'.pdf'
                else:
                    options.output_file = json_data['file_output']
                #options.output_file = 'pdf_output_' + str(ipdf) + '.pdf'

                print(options.work_temp_folder)

                #with open(json_data['image_names'][ifile], 'wb') as f:
                #    f.write(pdf)
                #    f.close()

                if len(pdf)>0:
                    with open(options.input_file, 'wb') as f:
                        f.write(pdf)
                        f.close()

                    result = self.run_ocrmypdf(options)
                    
                    _OCRresult = OCRResult()
                    if len(json_data['image_names'])>ifile:
                        _OCRresult.filename=json_data['image_names'][ifile]
                    if not (not json_data['file_input'] is None and str(json_data['file_input']) != ''):
                        if (json_data['output_type'] + '').find('PDF') >= 0:
                            _OCRresult.output_pdf=base64.b64encode(options.result_pdf).decode('ascii')
                        if (json_data['output_type'] + '').find('TEXT') >= 0:
                            _OCRresult.output_text = str(options.result_text)
                        _OCRresult.output_json = str(options.result_templatedata_json)
                        _OCRresult.output_xml = str(options.result_templatedata_xml)
                    if (json_data['output_type']+'').find('PAGE')>=0:
                        for page in options.result_pages:
                            _OCRPage = OCRResult.OCRPage()
                            _OCRPage.page_number = int(page[3])
                            if not (not json_data['file_input'] is None and str(json_data['file_input']) != ''):
                                _OCRPage.page_text = str(page[2])
                            _OCRPage.page_json = str(page[0])
                            _OCRPage.page_image = base64.b64encode(page[1]).decode('ascii')
                            _OCRresult.output_pages.append(_OCRPage)

                    results.append(_OCRresult.toJSON())
                    #print(results)

                    if json_data['ftp_ip']+''!='':
                        if not json_data['file_input'] is None and str(json_data['file_input']) != '':
                            # ghi ra FTP
                            FTPUtil.connect(json_data['ftp_ip'], json_data['ftp_port'], json_data['ftp_user'], json_data['ftp_pwd'], json_data['client_folder'])
                            # write to file: PDF, TEXT, JSON, XML, PAGES: TEXT, JSON, IMAGE
                            output_file_name = FILEUtil.getFileName(options.output_file)

                            options.client_folder = os.path.join(options.work_temp_folder, CommonUtil.removeSlash(options.client_folder)) + '/'


                            if not FILEUtil.fileexists(options.client_folder):
                                try:
                                    os.mkdir(options.client_folder, 0o700)
                                except:
                                    pass
                            FTPUtil.uploadData(options.client_folder+FILEUtil.getFileBaseName(output_file_name + '.pdf'), output_file_name + '.pdf', options.result_pdf)
                            FTPUtil.uploadText(options.client_folder+FILEUtil.getFileBaseName(output_file_name + '.txt'), output_file_name + '.txt', options.result_text)
                            if options.result_templatedata_json is None or len(options.result_templatedata_json) == 0:
                                options.result_templatedata_json="[]"
                            FTPUtil.uploadText(options.client_folder+FILEUtil.getFileBaseName(output_file_name + '.json'), output_file_name + '.json', options.result_templatedata_json)
                            if options.result_templatedata_xml is None or len(options.result_templatedata_xml) == 0:
                                options.result_templatedata_xml='<Node />'
                            FTPUtil.uploadText(options.client_folder+FILEUtil.getFileBaseName(output_file_name + '.xml'), output_file_name + '.xml', options.result_templatedata_xml)
                            for page in options.result_pages:
                                page_number = int(page[3])
                                FTPUtil.uploadText(options.client_folder+FILEUtil.getFileBaseName(output_file_name + '_page_' + str(page_number + 1) + '.txt'), output_file_name + '_page_' + str(page_number + 1) + '.txt', str(page[2]))
                                FTPUtil.uploadText(options.client_folder+FILEUtil.getFileBaseName(output_file_name + '_page_' + str(page_number + 1) + '.json'), output_file_name + '_page_' + str(page_number + 1) + '.json', str(page[0]))
                                FTPUtil.uploadData(options.client_folder+FILEUtil.getFileBaseName(output_file_name + '_page_' + str(page_number + 1) + '.png'), output_file_name + '_page_' + str(page_number + 1) + '.png', page[1])

            if json_data['ftp_ip']+''!='':
                # cleanup_working_folder(options=options)
                print('ko xoa folder')

            ifile=ifile+1
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            utf8_text=utf8_text+'<br>'+('eeerrrr')
            utf8_text=utf8_text+'<br>'+(str(e))
            print(e)

        utf8_text = utf8_text+str((datetime.datetime.now()-starttime).total_seconds())+'s/'+str(totalpage)+'files'

        if json_data['ftp_ip'] + '' != '':
            FTPUtil.close()
        else:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            staticFile = os.path.join(BASE_DIR, 'assets', 'optimize.pdf')
            import shutil
            shutil.copy(options.work_temp_folder + '/optimize.pdf', staticFile)
            utf8_text = utf8_text + '<br><a href="/static/optimize.pdf">Tai file</a>'

        if LOGUtil.is_error:
            return JsonResponse({'timeexecute': utf8_text, 'results': results, 'status': LOGUtil.errorLog})

        results=[] # kg can tra ve vi luu tren FTP roi

        if str(json_data['api_callback']) + '' != '':
            try:
                response = requests.get(json_data['api_callback'] + '&id=' + str(json_data['noderequest_id']) + '&status=OK')
                if str(response.status_code)!='OK':
                    return JsonResponse({'timeexecute': utf8_text, 'results': [], 'status':response.text })
                else:
                    return JsonResponse({'timeexecute': utf8_text, 'results': [], 'status':'OK' })
            except Exception as e:
                return JsonResponse({'timeexecute': utf8_text, 'results': [], 'status':str(e)})
        else:
            return JsonResponse({'timeexecute': utf8_text, 'results': results, 'status':'OK' })

ocr_view = csrf_exempt(OcrView.as_view())
