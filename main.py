import os
import cv2
import sys
import numpy as np
import threading as thr
import collections

# import the needed modules from the lib directory
from utils.vision_utils import VisionUtils
from utils.pre_proc_utils import PreProcUtils
from utils.config import *
import logger as log
if sys.version_info[0] == 2:
    from utils.pdf_ubuntu_utils import PdfUbuntuUtils  # for ubuntu
    pdf_util = PdfUbuntuUtils()
    import Queue as qu
if sys.version_info[0] == 3:
    from utils.pdf_win_utils import PdfWinUtils  # for anaconda
    pdf_util = PdfWinUtils()
    import queue as qu


# initialize the google cloud api credentials
log.print("--- Config The Google Cloud OCR API ---")
vision_util = VisionUtils(show_result=SHOW_RESULT)
preproc_util = PreProcUtils(show_result=SHOW_RESULT)


# main ocr function
def ocr_func(pdf_file_path):
    log.print("\n== {} =========================================".format(os.path.split(dst_file_path)[1]))

    # check if the document file is uploaded successfully or not
    if not os.path.exists(dst_file_path):
        log.print("\t No exist such file! ")
        sys.exit(1)

    #
    """ -------------------------------------------------------------------------------------------------------- """
    """ ---------------------  OCR for Text Detection from documents ------------------------------------------- """
    """ -------------------------------------------------------------------------------------------------------- """
    log.print("\n -- OCR processing ---")

    # conver the document file to the list of image(.jpg) file per each page
    log.print(" convert to images ...")
    if dst_file_path[-3:].lower() == "pdf":
        page_img_paths = pdf.pdfTojpgs(pdf_path=dst_file_path)
        log.print("\tpages #: {}".format(len(page_img_paths)))
    else:
        page_img_paths = [dst_file_path]
    page_img_paths.sort()

    """ detect the text from the page images with google cloug vision ocr api  ------------------------------------- """
    log.print(" detect the text ...")
    pages_contents_queue = qu.Queue()
    threads = []

    # multi-threading for calling the google vision ocr api
    # a thread for a page image
    # response would be returned as a queue of the content object
    while pages_contents_queue.qsize() == 0:
        for path in page_img_paths:
            idx = page_img_paths.index(path)

            thread = thr.Thread(target=vis.detect_text, args=(path, idx, pages_contents_queue))
            threads.append(thread)
            thread.start()
        for thread in threads:
            if thread is not None and thread.isAlive():
                thread.join()
                thread = None
        if pages_contents_queue.qsize() == 0:
            log.print("error response on Google Vision API")
            break

    contents = []
    while pages_contents_queue.qsize() > 0:
        content = pages_contents_queue.get(True, 1)
        if content is None:
            continue
        contents.append(content)

    """ recongnize the TUR type ------------------------------------------------------------------------------------ """
    tur_flag = False
    for content in contents:
        if content['annotations'] is None:
            continue
        log.print("\t page {} ...".format(content['id'] + 1))
        log.print("\timage size: width x height = {} x {}".format(content['image'].shape[1], content['image'].shape[0]))
        log.print("\tnumber of annotations: {}".format(len(content['annotations'])))
        log.print("\torientation          : {}".format(content['orientation']))

        # preprocessing the content image and also align the annotations of the
        pre.pre_proc(content=content)

        # recognize the document type with existing the "tur"("PVPC")
        _flag = bil.recog_tur(content=content)  # add new field of "merged_ext_annos" to the content
        tur_flag = _flag or tur_flag

    """ find the main page ----------------------------------------------------------------------------------------- """
    log.print("\tTUR FLAGE: {}".format(tur_flag))
    list_len = []
    for content in contents:

        # align the text annotations to the expressions with its meaning
        # each expression is made of keyword and the list of string
        expressions, res_img = bil.ocr_express(content=content, tur_flag=tur_flag)

        cv2.imwrite(LOG_DIR + "recog_" + str(content['id']) + ".jpg", res_img)
        log.print("\tnumber of expressions: {}".format(len(expressions)))

        content["expressions"] = expressions
        list_len.append(len(expressions))

    # find out the main page
    if list_len is None or list_len == []:
        log.print("\tInternet connection Error")
        return "\tInternet connection Error"
    # max_len = max(list_len)
    # main_page_idx = list_len.index(max_len)
    # log.print(" main page: {}\n".format(contents[main_page_idx]['id'] + 1))
    # main_content = contents[main_page_idx]

    #
    """ -------------------------------------------------------------------------------------------------------- """
    """ ---------------------  Parsing The Expressions --------------------------------------------------------- """
    """ -------------------------------------------------------------------------------------------------------- """
    # parsing the expressions and get out the bill information (items with its values)
    total_expressions = []
    for content in contents:
        total_expressions.extend(content["expressions"])

    log.print("\n -- Parsing the expressions ---")
    # bill_info = bil.parse_expressions(expressions=main_content["expressions"])
    bill_info = bil.parse_expressions(expressions=total_expressions, tur_flag=tur_flag, bIsUnit=False)

    """ Display the Result info --------------------------------------------------------------------------------- """
    # show_bill_info_1(bill_info=bill_info)  # only for checking on local
    filt_ordered_info = filter_rename_bill_info(bill_info=bill_info, tur_flag=tur_flag)  # disable the unnecessary info fields
    return filt_ordered_info


# disable the unnecessary items
def filter_rename_bill_info(bill_info, tur_flag):
    filtered = {}

    if tur_flag:
        filtered["Type"] = "TUR"
    else:
        filtered["Type"] = "OTHER"

    #
    for key in bill_info.keys():

        # rename "Billing Period" -> "Periodo de facturacion"
        if key in [KEY_BILL_PERIOD]:  # rename
            splits = bill_info[KEY_BILL_PERIOD].split("/")
            if len(splits) == 2:
                day, month = splits[:2]
                try:
                    year = bill_info[KEY_ISSUE_DATE].split("/")[-1]
                    if len(year) != 4:
                        year = "0000"
                except Exception as e:
                    log.print("\t\texcept: {}".format(e))
                    year = "0000"
            elif len(splits) == 3:
                day, month, year = splits[:3]
            else:
                filtered["Periodo de facturacion"] = EMPTY
                continue
            value = "{:02}/{:02}/{:04}".format(int(day), int(month), int(year))
            filtered["Periodo de facturacion"] = value

        # rename "Name of Owner" -> "Nombre del Titular"
        elif key in [KEY_NAME]:
            filtered["Nombre del Titular"] = bill_info[key]

        elif key in [KEY_VARIABLE, KEY_VARIABLE_A, KEY_VARIABLE_E] + [KEY_FIXED, KEY_FIXED_A, KEY_FIXED_C]:
            if tur_flag:
                if key in [KEY_VARIABLE_A, KEY_VARIABLE_E] + [KEY_FIXED_A, KEY_FIXED_C]:
                    filtered[key] = bill_info[key]
                else:  # [KEY_VARIABLE, KEY_FIXED]
                    filtered[key] = EMPTY
            else:
                if key in [KEY_VARIABLE_A, KEY_VARIABLE_E] + [KEY_FIXED_A, KEY_FIXED_C]:
                    filtered[key] = EMPTY
                else:  # [KEY_VARIABLE, KEY_FIXED]
                    filtered[key] = bill_info[key]

        # disable the "Issue Number" and "Issue Date"
        elif key in [KEY_ISSUE_NUMBER, KEY_ISSUE_DATE]:
            log.print("\n\t{} is disabled".format(key))
            continue

        elif key in [KEY_ADDRESS]:
            filtered["Direccion del Suministro"] = bill_info[key]

        else:
            filtered[key] = bill_info[key]

    """ -------------------------------------------------------------------------- """
    # rearrnage the order of the dict with predefined order
    ordered_info = collections.OrderedDict()

    ordered_info[KEY_ACCESO] = filtered[KEY_ACCESO]
    ordered_info[KEY_CONSUMO] = filtered[KEY_CONSUMO]
    ordered_info[KEY_VARIABLE] = filtered[KEY_VARIABLE]
    try:
        ordered_info["================= CONSUMO x VP"] = float(filtered[KEY_CONSUMO]) * float(filtered[KEY_VARIABLE])
    except Exception:
        pass
    ordered_info[KEY_VARIABLE_A] = filtered[KEY_VARIABLE_A]
    ordered_info[KEY_VARIABLE_E] = filtered[KEY_VARIABLE_E]

    ordered_info[KEY_POTENCIA] = filtered[KEY_POTENCIA]
    ordered_info[KEY_FIXED] = filtered[KEY_FIXED]
    ordered_info[KEY_FIXED_A] = filtered[KEY_FIXED_A]
    ordered_info[KEY_FIXED_C] = filtered[KEY_FIXED_C]

    ordered_info[KEY_PERIODO] = filtered[KEY_PERIODO]
    ordered_info[KEY_IMPUESTO] = filtered[KEY_IMPUESTO]
    ordered_info[KEY_ALQUILER] = filtered[KEY_ALQUILER]

    ordered_info[KEY_DESCUENTO_PERCENT] = filtered[KEY_DESCUENTO_PERCENT]
    ordered_info[KEY_DESCUENTO_VALUE] = filtered[KEY_DESCUENTO_VALUE]
    ordered_info["================= CHECK DESCUENTO"] = filtered[KEY_DESCUENTO_VALUE]

    ordered_info[KEY_IVA] = filtered[KEY_IVA]
    ordered_info[KEY_CUPS] = filtered[KEY_CUPS]
    ordered_info[KEY_BILL_PERIOD] = filtered[KEY_BILL_PERIOD]
    ordered_info[KEY_NIF] = filtered[KEY_NIF]
    ordered_info[KEY_NAME] = filtered[KEY_NAME]
    ordered_info[KEY_ADDRESS] = filtered[KEY_ADDRESS]
    ordered_info["Type"] = filtered["Type"]

    log.print("\n -- ordered info ---")
    for key in ordered_info.keys():
        log.print("\t%s: %s" % (key, ordered_info[key]))

    return ordered_info


# print the extracted bill infomation as a format of equation
def show_bill_info_1(bill_info):
    log.print("\n --- bill info with Equation ---")
    log.print("\tCUPS       : %s" % (bill_info[KEY_CUPS]))
    log.print("\tIssueDate  : %s" % (bill_info[KEY_ISSUE_DATE]))
    log.print("\tIssueNumber: %s" % (bill_info[KEY_ISSUE_NUMBER]))
    log.print("\tNIF: %s" % (bill_info[KEY_NIF]))
    log.print("\tBillingPeriod: %s" % (bill_info[KEY_BILL_PERIOD]))
    log.print("\tNameOwner: %s" % (bill_info[KEY_NAME]))
    log.print("\tDelivery Address: %s" % (bill_info[KEY_ADDRESS]))

    log.print("\tAcceso   = %s" % (bill_info[KEY_ACCESO]))
    log.print("\tPotencia = Potencia x Periodo x FixedPrice")
    log.print("\t            %s x %s x %s" % (bill_info[KEY_POTENCIA], bill_info[KEY_PERIODO], bill_info[KEY_FIXED]))
    log.print("\t            FA: %s, FC: %s" % (bill_info[KEY_FIXED_A], bill_info[KEY_FIXED_C]))
    log.print("\tConsumo  = Consumo x VariablePrice")
    log.print("\t            %s x %s" % (bill_info[KEY_CONSUMO], bill_info[KEY_VARIABLE]))
    log.print("\t            VA: %s, VE: %s" % (bill_info[KEY_VARIABLE_A], bill_info[KEY_VARIABLE_E]))
    log.print("\tDescuento= %s" % (bill_info[KEY_DESCUENTO_PERCENT]))
    log.print("\tImpuesto = %s" % (bill_info[KEY_IMPUESTO]))
    log.print("\tAlquiler = %s" % (bill_info[KEY_ALQUILER]))
    log.print("\tIVA      = %s" % (bill_info[KEY_IVA]))


if __name__ == '__main__':
    # with open(result_path, 'w') as fp:
    #     for key in result.keys():
    #         line = "{}: {}\n".format(key, result[key])
    #         fp.write(line)
    data_dir = "data/"

    from files import *

    # fns = Test
    # for fn in fns:
    #     path = os.path.join(data_dir + "Facturast_check_Du", fn)
    #     result = main_ocr_proc(path)

    # fns = TUR
    # for fn in fns:
    #     path = os.path.join(data_dir + "TUR", fn)
    #     result = main_ocr_proc(path)

    # for fn in fns:
    #     path = os.path.join(data_dir + "NIF", fn)
    #     result = main_ocr_proc(path)

    # fns = Descuento
    # for fn in fns:
    #     path = os.path.join(data_dir + "Descuento", fn)
    #     result = main_ocr_proc(path)

    fns = [Descuento_C, "Descuento Consumo/"]
    # fns = [Descuento_P, "Descuento Potencia/"]
    # fns = [Descuento_T, "Descuento Total/"]
    # fns = [Descuento_M, "Mix/"]

    data_dir = "data/Descuento/"
    for fn in fns[0]:
        # if fn != "Est-Ib_10_v.pdf":
        #     continue
        path = os.path.join(data_dir + fns[1], fn)
        result = main_ocr_proc(path)

    # path = os.path.join(data_dir + fns[1], "Est-End_6_v-2.jpg")
    # result = main_ocr_proc(path)
    # sys.exit()
    # data_dir = "data/Descuento/"
