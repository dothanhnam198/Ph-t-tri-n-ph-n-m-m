#!/usr/bin/env python3
# © 2015-19 James R. Barlow: github.com/jbarlow83
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
import base64
import logging
import os
import sys
from tempfile import mkdtemp

from ocrmypdfcs._version import __version__
from ocrmypdfcs._jobcontext import make_logger
from ocrmypdfcs._sync import run_pipeline
from ocrmypdfcs._validation import check_closed_streams, check_options
from ocrmypdfcs.api import Verbosity, configure_logging
from ocrmypdfcs.cli import parser
from ocrmypdfcs.exceptions import BadArgsError, ExitCode, MissingDependencyError

from OCRDjangoApi.DjangoUtility import FILEUtil
from OCRDjangoApi.ocrapi.views import OCRResult


def run(args=None):
    options = parser.parse_args(args=args)

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

    options.tessdata_path = '/usr/share/tesseract-ocr/4.00/tessdata/'
    options.page_number = ',,'
    if options.pages is None or len(options.pages)==0:
        options.page_number = ',,'
    else:
        options.page_number = ',' + ','.join(map(str, options.pages)) + ','
    options.config_template = None
    if not options.templates is None and options.templates+'' != '':
        with open(options.templates, 'r') as f:
            options.config_template = f.read()
            f.close()
    options.author = 'EPS-OCR'
    options.oversample = 1
    options.png_quality = 1
    options.quiet = True
    options.remove_vectors = True
    options.rotate_pages = True
    options.rotate_pages_threshold = 14.0
    options.subject = 'EPS'
    options.threshold = True
    options.title = 'None'
    options.verbose = 1
    options.force_ocr = True

    results = []
    pdfs = [options.input_file]
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
        # Phongnh: fix use SAMBA instead of temp
        options.work_temp_folder = mkdtemp(prefix="com.django-restfull.ocrmypdf.")

        print(options.work_temp_folder)

        print(options)

        result = run_pipeline(options=options)

        _OCRresult = OCRResult()
        _OCRresult.filename = options.input_file
        #if (json_data['output_type'] + '').find('PDF') >= 0:
        _OCRresult.output_pdf = base64.b64encode(options.result_pdf).decode('ascii')
        #if (json_data['output_type'] + '').find('TEXT') >= 0:
        _OCRresult.output_text = str(options.result_text)
        _OCRresult.output_json = str(options.result_templatedata_json)
        _OCRresult.output_xml = str(options.result_templatedata_xml)
        #if (json_data['output_type'] + '').find('PAGE') >= 0:
        if True:
            for page in options.result_pages:
                _OCRPage = OCRResult.OCRPage()
                _OCRPage.page_number = int(page[3])
                _OCRPage.page_text = str(page[2])
                _OCRPage.page_json = str(page[0])
                _OCRPage.page_image = base64.b64encode(page[1]).decode('ascii')
                _OCRresult.output_pages.append(_OCRPage)

        results.append(_OCRresult.toJSON())

        # write to file: PDF, TEXT, JSON, XML, PAGES: TEXT, JSON, IMAGE
        if not options.client_folder is None and len(options.client_folder) != 0:
            try:
                os.mkdir(options.client_folder, 0o700)
            except:
                pass
        output_file_name = options.client_folder+'/'+FILEUtil.getFileName(options.output_file)
        with open(output_file_name+'.pdf', 'wb') as f:
            f.write(options.result_pdf)
            f.close()
        with open(output_file_name+'.txt', 'w') as f:
            f.write(options.result_text)
            f.close()
        with open(output_file_name+'.json', 'w') as f:
            if options.result_templatedata_json is None or len(options.result_templatedata_json) == 0:
                f.write('[]')
            else:
                f.write(options.result_templatedata_json)
            f.close()
        with open(output_file_name+'.xml', 'w') as f:
            if options.result_templatedata_xml is None or len(options.result_templatedata_xml)==0:
                f.write('<Node />')
            else:
                f.write(options.result_templatedata_xml)
            f.close()
        for page in _OCRresult.output_pages:
            with open(output_file_name+'_page_'+str(page.page_number+1)+'.txt', 'w') as f:
                f.write(page.page_text)
                f.close()
            with open(output_file_name+'_page_'+str(page.page_number+1)+'.json', 'w') as f:
                f.write(page.page_json)
                f.close()
            with open(output_file_name+'_page_'+str(page.page_number+1)+'.png', 'wb') as f:
                f.write(base64.b64decode(page.page_image))
                f.close()

    return results

if __name__ == '__main__':
    sys.exit(run())
