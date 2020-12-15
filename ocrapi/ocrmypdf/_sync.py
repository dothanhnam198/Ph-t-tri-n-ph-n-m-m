# © 2016 James R. Barlow: github.com/jbarlow83
#
# This file is part of OCRmyPDF.
#
# OCRmyPDF is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OCRmyPDF is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with OCRmyPDF.  If not, see <http://www.gnu.org/licenses/>.

import logging
import logging.handlers
import multiprocessing
import os
import signal
import sys
import json
import threading
from collections import namedtuple
from tempfile import mkdtemp

from tqdm import tqdm

from ._graft import OcrGrafter
from ._jobcontext import PDFContext, cleanup_working_files, make_logger
from ._pipeline import (
    convert_to_pdfa,
    copy_final,
    create_ocr_image,
    create_pdf_page_from_image,
    create_visible_page_jpg,
    generate_postscript_stub,
    get_orientation_correction,
    get_pdfinfo,
    is_ocr_required,
    merge_sidecars,
    metadata_fixup,
    ocr_tesseract_hocr,
    ocr_tesseract_textonly_pdf,
    optimize_pdf,
    preprocess_clean,
    preprocess_deskew,
    preprocess_remove_background,
    rasterize,
    rasterize_preview,
    render_hocr_page,
    should_visible_page_image_use_jpg,
    triage,
    validate_pdfinfo_options,
)
from ._validation import (
    check_requested_output_file,
    create_input_file,
    report_output_file_size,
)
from .exceptions import ExitCode, ExitCodeException
from .exec import qpdf
from .helpers import available_cpu_count
from .pdfa import file_claims_pdfa
# Phongnh: inject
from ._pipeline import ocr_tesseract_data

# Phongnh: inject
PageResult = namedtuple(
    'PageResult', 'pageno, pdf_page_from_image, ocr, text, orientation_correction, text_out_ocr, data_out_ocr, image_out_ocr, templatedata_json, templatedata_xml'
)


def preprocess(page_context, image, remove_background, deskew, clean):
    if remove_background:
        image = preprocess_remove_background(image, page_context)
    if deskew:
        image = preprocess_deskew(image, page_context)
    if clean:
        image = preprocess_clean(image, page_context)
    return image


def exec_page_sync(page_context):
    options = page_context.options
    orientation_correction = 0
    pdf_page_from_image_out = None
    ocr_out = None
    text_out = None
    if is_ocr_required(page_context):
        if options.rotate_pages:
            # Rasterize
            rasterize_preview_out = rasterize_preview(page_context.origin, page_context)
            orientation_correction = get_orientation_correction(
                rasterize_preview_out, page_context
            )

        rasterize_out = rasterize(
            page_context.origin,
            page_context,
            correction=orientation_correction,
            remove_vectors=False,
        )

        if not any([options.clean, options.clean_final, options.remove_vectors]):
            ocr_image = preprocess_out = preprocess(
                page_context,
                rasterize_out,
                options.remove_background,
                options.deskew,
                clean=False,
            )
        else:
            if not options.lossless_reconstruction:
                preprocess_out = preprocess(
                    page_context,
                    rasterize_out,
                    options.remove_background,
                    options.deskew,
                    clean=options.clean_final,
                )
            if options.remove_vectors:
                rasterize_ocr_out = rasterize(
                    page_context.origin,
                    page_context,
                    correction=orientation_correction,
                    remove_vectors=True,
                    output_tag='_ocr',
                )
            else:
                rasterize_ocr_out = rasterize_out
            ocr_image = preprocess(
                page_context,
                rasterize_ocr_out,
                options.remove_background,
                options.deskew,
                clean=options.clean,
            )

        # Phongnh: rasterize_out: da tach anh
        # Phongnh: ocr_image: da xu ly deskew, xoa nen

        # Phongnh: ocr_image_out: xu ly ?
        ocr_image_out = create_ocr_image(ocr_image, page_context)


        pdf_page_from_image_out = None
        if not options.lossless_reconstruction:
            visible_image_out = preprocess_out
            if should_visible_page_image_use_jpg(page_context.pageinfo):
                visible_image_out = create_visible_page_jpg(
                    visible_image_out, page_context
                )
            # Phongnh: dung image2pdf chuyen anh thanh PDF tung page
            pdf_page_from_image_out = create_pdf_page_from_image(
                visible_image_out, page_context
            )

        # Phongnh: inject result type
        def same_crop(imagesrc, x, y, w, h):
            import cv2
            import numpy as np

            image = cv2.imread(imagesrc)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            white_bg = 255 * np.ones_like(image)

            roi = image[y:y + h, x:x + w]
            white_bg[y:y + h, x:x + w] = roi

            cv2.imwrite(imagesrc.replace('.png', '_template.png'), white_bg)
            # box.save(image.replace('.png', '_template.png'))

            return imagesrc.replace('.png', '_template.png')

        def getskewangle(imagesrc, x, y, w, h):
            return 0.0
            # load the image from disk
            import cv2
            import numpy as np

            angle = 0

            try:
                x=int(x)
                y=int(y)
                w=int(w)
                h=int(h)
                image = cv2.imread(imagesrc)
                white_bg = 255 * np.ones_like(image)
                roi = image[y:y + h, x:x + w]
                white_bg[y:y + h, x:x + w] = roi
                image = white_bg
                print('yyyyyyyyy')
                # convert the image to grayscale and flip the foreground
                # and background to ensure foreground is now "white" and
                # the background is "black"
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                gray = cv2.bitwise_not(gray)

                # threshold the image, setting all foreground pixels to
                # 255 and all background pixels to 0
                thresh = cv2.threshold(gray, 0, 255,
                                       cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
                # grab the (x, y) coordinates of all pixel values that
                # are greater than zero, then use these coordinates to
                # compute a rotated bounding box that contains all
                # coordinates
                coords = np.column_stack(np.where(thresh > 0))
                angle = cv2.minAreaRect(coords)[-1]
            except Exception as e:
                print('e')
                print(e)

            print(angle)
            # the `cv2.minAreaRect` function returns values in the
            # range [-90, 0); as the rectangle rotates clockwise the
            # returned angle trends to 0 -- in this special case we
            # need to add 90 degrees to the angle
            if angle < -45:
                angle = -(90 + angle)

            # otherwise, just take the inverse of the angle to make
            # it positive
            else:
                angle = -angle
            """
            # rotate the image to deskew it
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h),
            	flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
            """
            angle=int(angle)
            print(angle)
            return angle

        def ocrtemplate2json(data):

            return data
        def ocrtemplate2xml(data):

            return data

        def ocrdata2json(data, text, imagesrc):
            jstext = text.split()
            jsi = 0
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            jsdata = [[str(m) for m in n.split('\t')] for n in str(data).split('\n')]
            jsout = []
            for n in jsdata:
                try:
                    if n[10] == 'conf':
                        pass
                    elif n[10] == '-1':
                        jsout.append(
                            json.loads('{' + '"left":"{0}","top":"{1}","width":"{2}","height":"{3}","box":"{4}","text":"{5}","angle":"0"'.format(
                                n[6], n[7], n[8], n[9], 1, '') + '}'))
                    else:
                        jsout.append(
                            json.loads('{' + '"left":"{0}","top":"{1}","width":"{2}","height":"{3}","box":"{4}","text":"{5}","angle":"{6}"'.format(
                                n[6], n[7], n[8], n[9], 0, jstext[jsi], getskewangle(imagesrc, n[6], n[7], n[8], n[9])) + '}'))
                        jsi = jsi + 1
                except:
                    pass
            return jsout
        text_out_ocred = ''
        data_out_ocred = None
        ocr_image_out_ocred = None
        templatedata_json=''
        templatedata_xml=''
        # Phongnh: xu ly mau template
        if options.config_template is None or len(options.config_template)==0:
            # Phongnh: khi boi text co hien thi text, hocr_out: la file HTML can vi tri text + thong tin text
            if options.pdf_renderer == 'hocr':
                (hocr_out, text_out) = ocr_tesseract_hocr(ocr_image_out, page_context)
                # Phongnh: Helvetica + Canvas => pdf, drawImage, drawText at position
                ocr_out = render_hocr_page(hocr_out, page_context)

            # Phongnh: khi boi text kg hien thi text, transparent
            if options.pdf_renderer == 'sandwich':
                (ocr_out, text_out) = ocr_tesseract_textonly_pdf(
                    ocr_image_out, page_context
                )

            # Phongnh: inject result type
            with open(text_out, 'r', encoding="utf8") as file:
                text_out_ocred = file.read()
            with open(text_out.replace('.txt', '.tsv'), 'rb') as file:
                data_out_ocred = file.read()
            with open(ocr_image_out, 'rb') as file:
                ocr_image_out_ocred = file.read()
            data_out_ocred=ocrdata2json(data_out_ocred,text_out_ocred,ocr_image_out)
        else:
            text_out_ocred=''
            data_out_ocred=[]
            ocr_image_out_ocred=b''

            for con_temp in options.config_template:
                # xu ly lai anh, ten file
                ocr_image_out2=same_crop(ocr_image_out, int(con_temp['x']*con_temp['r']), int(con_temp['y']*con_temp['r']), int(con_temp['w']*con_temp['r']), int(con_temp['h']*con_temp['r']))

                # Phongnh: khi boi text co hien thi text, hocr_out: la file HTML can vi tri text + thong tin text
                if options.pdf_renderer == 'hocr':
                    (hocr_out, text_out) = ocr_tesseract_hocr(ocr_image_out2, page_context)
                    # Phongnh: Helvetica + Canvas => pdf, drawImage, drawText at position
                    ocr_out = render_hocr_page(hocr_out, page_context)

                # Phongnh: khi boi text kg hien thi text, transparent
                if options.pdf_renderer == 'sandwich':
                    (ocr_out, text_out) = ocr_tesseract_textonly_pdf(
                        ocr_image_out2, page_context
                    )

                # Phongnh: inject result type
                text_out_ocred2=''
                data_out_ocred2=None
                ocr_image_out_ocred2=None
                with open(text_out, 'r') as file:
                    text_out_ocred2 = file.read()
                with open(text_out.replace('.txt','.tsv'), 'rb') as file:
                    data_out_ocred2=file.read()
                with open(ocr_image_out, 'rb') as file:
                    ocr_image_out_ocred2=file.read()

                data_out_ocred2 = ocrdata2json(data_out_ocred2.decode('utf-8'), text_out_ocred2,ocr_image_out)

                if templatedata_json=='':
                    templatedata_json = templatedata_json + '{'+(' "title":"{0}", "value":"{1}", "description":"{2}" '.format(con_temp['title'], text_out_ocred2, con_temp['description']))+'}'
                else:
                    templatedata_json = templatedata_json + ',{'+(' "title":"{0}", "value":"{1}", "description":"{2}" '.format(con_temp['title'], text_out_ocred2, con_temp['description']))+'}'

                if templatedata_xml=='':
                    templatedata_xml = templatedata_xml + '{'+(' "title":"{0}", "value":"{1}", "description":"{2}" '.format(con_temp['title'], text_out_ocred2, con_temp['description']))+'}'
                else:
                    templatedata_xml = templatedata_xml + ',{'+(' "title":"{0}", "value":"{1}", "description":"{2}" '.format(con_temp['title'], text_out_ocred2, con_temp['description']))+'}'

                text_out_ocred = text_out_ocred + text_out_ocred2
                data_out_ocred = [*data_out_ocred, *data_out_ocred2]
                ocr_image_out_ocred = ocr_image_out_ocred + ocr_image_out_ocred2


    # Phongnh: text_out: chi text nhan dang dc
    # Phongnh: pdf_page_from_image_out: chi pdf voi anh goc
    # Phongnh: ocr_out: chi pdf voi layer transparent text
    return PageResult(
        pageno=page_context.pageno,
        pdf_page_from_image=pdf_page_from_image_out,
        ocr=ocr_out,
        text=text_out,
        orientation_correction=orientation_correction,
        # Phongnh them gia tri tra ra
        text_out_ocr=text_out_ocred,
        data_out_ocr=data_out_ocred,
        image_out_ocr=ocr_image_out_ocred,
        templatedata_json=templatedata_json,
        templatedata_xml=templatedata_xml,
    )


def post_process(pdf_file, context):
    # Phongnh: pdf_file da co 2 layers
    pdf_out = pdf_file
    if context.options.output_type.startswith('pdfa'):
        # Phongnh: tao file Postscript ps tu mau template => script cho Ghostscript gen PDF/A
        ps_stub_out = generate_postscript_stub(context)
        # Phongnh: xu ly NULL bytes va dung Ghostscript tao file PDF/A
        pdf_out = convert_to_pdfa(pdf_out, ps_stub_out, context)

    # Phongnh: pdf_out da co 2 layers + format PDF/A
    # Phongnh: viet noi dung metadata, dung Pikepdf + toi uu hoa file
    pdf_out = metadata_fixup(pdf_out, context)
    # Phongnh: dung Pikepdf doc, ghi file pdf de toi uu image, nen images..
    return optimize_pdf(pdf_out, context)


def worker_init(queue):
    """Initialize a process pool worker"""

    # Ignore SIGINT (our parent process will kill us gracefully)
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    # Reconfigure the root logger for this process to send all messages to a queue
    h = logging.handlers.QueueHandler(queue)
    root = logging.getLogger()
    root.handlers = []
    root.addHandler(h)


def worker_thread_init(_queue):
    pass


def log_listener(queue):
    """Listen to the worker processes and forward the messages to logging

    For simplicity this is a thread rather than a process. Only one process
    should actually write to sys.stderr or whatever we're using, so if this is
    made into a process the main application needs to be directed to it.

    See https://docs.python.org/3/howto/logging-cookbook.html#logging-to-a-single-file-from-multiple-processes
    """

    while True:
        try:
            record = queue.get()
            if record is None:
                break
            logger = logging.getLogger(record.name)
            logger.handle(record)
        except Exception:
            import traceback

            print("Logging problem", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)


def exec_concurrent(context):
    """Execute the pipeline concurrently"""

    # Run exec_page_sync on every page context
    max_workers = min(len(context.pdfinfo), context.options.jobs)
    if max_workers<=0:
        max_workers=1
    if max_workers > 1:
        context.log.info("Start processing %d pages concurrent", max_workers)

    # Tesseract 4.x can be multithreaded, and we also run multiple workers. We want
    # to manage how many threads it uses to avoid creating total threads than cores.
    # Performance testing shows we're better off
    # parallelizing ocrmypdf and forcing Tesseract to be single threaded, which we
    # get by setting the envvar OMP_THREAD_LIMIT to 1. But if the page count of the
    # input file is small, then we allow Tesseract to use threads, subject to the
    # constraint: (ocrmypdf workers) * (tesseract threads) <= max_workers.
    # As of Tesseract 4.1, 3 threads is the most effective on a 4 core/8 thread system.
    tess_threads = min(3, context.options.jobs // max_workers)
    if context.options.tesseract_env is None:
        context.options.tesseract_env = os.environ.copy()
    context.options.tesseract_env.setdefault('OMP_THREAD_LIMIT', str(tess_threads))
    if tess_threads > 1:
        context.log.info("Using Tesseract OpenMP thread limit %d", tess_threads)

    if context.options.use_threads:
        from multiprocessing.dummy import Pool

        initializer = worker_thread_init
    else:
        Pool = multiprocessing.Pool
        initializer = worker_init

    sidecars = [None] * len(context.pdfinfo)
    ocrgraft = OcrGrafter(context)

    log_queue = multiprocessing.Queue(-1)
    listener = threading.Thread(target=log_listener, args=(log_queue,))
    listener.start()
    with tqdm(
        total=(2 * len(context.pdfinfo)),
        desc='OCR',
        unit='page',
        unit_scale=0.5,
        disable=not context.options.progress_bar,
    ) as pbar, Pool(
        processes=max_workers, initializer=initializer, initargs=(log_queue,)
    ) as pool:
        # Phongnh: thuc hien tien xu ly anh, nhan dang
        results = pool.imap_unordered(exec_page_sync, context.get_page_contexts())
        while True:
            try:
                page_result = results.next()
                sidecars[page_result.pageno] = page_result.text
                pbar.update()

                # Phongnh: inject result type by pages
                context.options.result_text = context.options.result_text + page_result.text_out_ocr
                context.options.result_pages.append((page_result.data_out_ocr, page_result.image_out_ocr, page_result.text_out_ocr, page_result.pageno))

                if context.options.result_templatedata_json!='':
                    context.options.result_templatedata_json = context.options.result_templatedata_json+','+page_result.templatedata_json+''
                else:
                    context.options.result_templatedata_json = context.options.result_templatedata_json+page_result.templatedata_json+''
                if context.options.result_templatedata_xml!='':
                    context.options.result_templatedata_xml = context.options.result_templatedata_xml+'\n'+page_result.templatedata_xml+''
                else:
                    context.options.result_templatedata_xml = context.options.result_templatedata_xml+page_result.templatedata_xml+''

                ocrgraft.graft_page(page_result)
                pbar.update()
                if 'api_callback' in context.options and str(context.options.api_callback) + '' != '' and str(context.options.api_callback) + '' != 'None':
                    try:
                        import requests
                        import time
                        page_time = time.time()
                        response = requests.get(str(context.options.api_callback) + '&id=' + str(context.options.noderequest_id) + '&progress=OK&start_time=' + str(context.options.start_time) + '&page_time=' + str(page_time) + '&page_no=' + str(page_result.pageno))
                    except:
                        print('Error callback master')
            except StopIteration:
                break
            except (Exception, KeyboardInterrupt):
                print('terminate')
                pool.terminate()
                log_queue.put_nowait(None)  # Terminate log listener
                # Don't try listener.join() here, will deadlock
                raise

    log_queue.put_nowait(None)
    listener.join()

    # Output sidecar text
    if context.options.sidecar:
        text = merge_sidecars(sidecars, context)
        # Copy text file to destination
        # Phongnh: copy noi dung file, text theo tung trang co \f = FormFeed
        copy_final(text, context.options.sidecar, context)

    # Merge layers to one single pdf
    # Phongnh: chi la ghi lai file pdf ra output kg o temp nua dung Pikepdf
    pdf = ocrgraft.finalize()

    # PDF/A and metadata
    # Phongnh: tao file PDF/A dung Ghostscript: pdfmark + Postscript file
    pdf = post_process(pdf, context)

    # Copy PDF file to destination
    # Phongnh: copy noi dung file
    copy_final(pdf, context.options.output_file, context)

    # Phongnh: inject result type
    with open(context.options.output_file, 'rb') as file:
        context.options.result_pdf = file.read()


class NeverRaise(Exception):
    """An exception that is never raised"""

    pass  # pylint: disable=unnecessary-pass


def run_pipeline(options, api=False):
    log = make_logger(options, __name__)

    # Any changes to options will not take effect for options that are already
    # bound to function parameters in the pipeline. (For example
    # options.input_file, options.pdf_renderer are already bound.)
    if not options.jobs:
        options.jobs = available_cpu_count()

    if 'api_callback' in options and str(options.api_callback) + '' != '' and str(
            options.api_callback) + '' != 'None':
        try:
            import requests
            response = requests.get(str(options.api_callback) + '&id=' + str(
                options.noderequest_id) + '&progress=OK&cpu_no=' + str(available_cpu_count()))
        except:
            print('callback cpu wrong '+ str(options.api_callback) + '&id=' + str(
                options.noderequest_id) + '&progress=OK&cpu_no=' + str(available_cpu_count()))
            pass
    else:
        print('No api_callback')


    #work_folder = mkdtemp(prefix="com.github.ocrmypdf.")
    # Phongnh: make temp folder tu dau
    work_folder = options.work_temp_folder

    try:
        check_requested_output_file(options)
        start_input_file = create_input_file(options, work_folder)

        # Triage image or pdf
        origin_pdf = triage(
            start_input_file, os.path.join(work_folder, 'origin.pdf'), options, log
        )

        # Gather pdfinfo and create context
        pdfinfo = get_pdfinfo(
            origin_pdf,
            detailed_page_analysis=options.redo_ocr,
            progbar=options.progress_bar,
            # Phongnh add page_number
            page_number = options.page_number,
        )
        context = PDFContext(options, work_folder, origin_pdf, pdfinfo)

        # Validate options are okay for this pdf
        validate_pdfinfo_options(context)

        # Execute the pipeline
        exec_concurrent(context)
        bsamefile = False
        if os.name != 'nt':
            try:
                bsamefile = os.path.samefile(options.output_file, os.devnull)
            except:
                pass
        if options.output_file == '-':
            log.info("Output sent to stdout")
        elif bsamefile:
            pass  # Say nothing when sending to dev null
        else:
            if options.output_type.startswith('pdfa'):
                pdfa_info = file_claims_pdfa(options.output_file)
                if pdfa_info['pass']:
                    log.info(
                        "Output file is a %s (as expected)", pdfa_info['conformance']
                    )
                else:
                    log.warning(
                        "Output file is okay but is not PDF/A (seems to be %s)",
                        pdfa_info['conformance'],
                    )
                    return ExitCode.pdfa_conversion_failed

            if not qpdf.check(options.output_file, log):
                log.warning('Output file: The generated PDF is INVALID')
                return ExitCode.invalid_output_pdf
            report_output_file_size(options, start_input_file, options.output_file)

    except (KeyboardInterrupt if not api else NeverRaise) as e:
        if options.verbose >= 1:
            log.exception("KeyboardInterrupt")
        else:
            log.error("KeyboardInterrupt")
        return ExitCode.ctrl_c
    except (ExitCodeException if not api else NeverRaise) as e:
        if str(e):
            log.error("%s: %s", type(e).__name__, str(e))
        else:
            log.error(type(e).__name__)
        return e.exit_code
    except (Exception if not api else NeverRaise) as e:
        import traceback
        print(traceback.format_exc())
        log.exception("An exception occurred while executing the pipeline")
        return ExitCode.other_error
    finally:
        #cleanup_working_files(work_folder, options)
        # Phongnh
        #os.remove(options.output_file)
        pass

    return ExitCode.ok

# Phongnh
def cleanup_working_folder(options):
    work_folder = options.work_temp_folder
    cleanup_working_files(work_folder, options)
    # Phongnh
    try:
        os.remove(options.output_file)
    except:
        pass