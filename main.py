import threading as thr
from utils.vision_utils import VisionUtils
from utils.pre_proc_utils import PreProcUtils
from logger import *
if sys.version_info[0] == 2:
    from utils.pdf_ubuntu_utils import PdfUbuntuUtils  # for ubuntu
    pdf_util = PdfUbuntuUtils()
    import Queue as qu
if sys.version_info[0] == 3:
    from utils.pdf_win_utils import PdfWinUtils  # for anaconda
    pdf_util = PdfWinUtils()
    import queue as qu


# initialize the google cloud api credentials
log_print("--- Config The Google Cloud OCR API ---")
vision_util = VisionUtils(show_result=SHOW_RESULT)
preproc_util = PreProcUtils(show_result=SHOW_RESULT)


# main ocr function
def ocr_func(pdf_path):
    log_print("\nPdf File:".format(os.path.split(pdf_path)[1]))

    # check if the document file is uploaded successfully or not
    if not os.path.exists(pdf_path):
        log_print("\t No exist such file! ")
        sys.exit(1)

    """ --- Convert the PDF to JPGs --- """
    log_print(" Convert PDF to JPGs ...")
    if pdf_path[-3:].lower() == "pdf":
        page_img_paths = pdf_util.pdfTojpgs(pdf_path=pdf_path)
        log_print("\tpages #: {}".format(len(page_img_paths)))
    else:
        page_img_paths = [pdf_path]
    page_img_paths.sort()

    """ detect the text from the page images with google cloug vision ocr api  ------------------------------------- """
    log_print(" Detect the text from Images ...")
    pages_contents_queue = qu.Queue()
    threads = []

    # multi-threading for calling the google vision ocr api
    # a thread for a page image
    # response would be returned as a queue of the content object
    while pages_contents_queue.qsize() == 0:
        for path in page_img_paths:
            idx = page_img_paths.index(path)

            thread = thr.Thread(target=vision_util.detect_text, args=(path, idx, pages_contents_queue))
            threads.append(thread)
            thread.start()
        for thread in threads:
            if thread is not None and thread.isAlive():
                thread.join()
                thread = None
        if pages_contents_queue.qsize() == 0:
            log_print("error response on Google Vision API")
            break

    contents = []
    while pages_contents_queue.qsize() > 0:
        content = pages_contents_queue.get(True, 1)
        if content is None:
            continue
        contents.append(content)

    """ Show the detect Text ------------------------------------------------------------------------------------ """
    tur_flag = False
    for content in contents:
        if content['annotations'] is None:
            continue
        log_print("\t page {} ...".format(content['id'] + 1))
        log_print("\timage size: width x height = {} x {}".format(content['image'].shape[1], content['image'].shape[0]))
        log_print("\tnumber of annotations: {}".format(len(content['annotations'])))
        log_print("\torientation          : {}".format(content['orientation']))

        # pre-processing the content image and also align the annotations of the
        preproc_util.pre_proc(content=content)


if __name__ == '__main__':
    data_dir = "./data"
    fns = [fn for fn in os.listdir(data_dir) if os.path.splitext(fn)[1] in EXT_DOC]
    for fn in fns:
        path = os.path.join(data_dir, fn)
        ocr_func(path)
