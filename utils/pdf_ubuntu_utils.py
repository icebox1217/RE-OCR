import logger as log
from logger import *


class PdfUbuntuUtils:
    def __init__(self):
        pass

    def pdfTojpgs(self, pdf_path):
        if not os.path.isfile(pdf_path):
            log_print("\tNo exist such pdf file {}".format(pdf_path))
            sys.exit(1)

        _, ext = os.path.splitext(os.path.basename(pdf_path))
        if ext.lower() in EXT_DOC:
            page_imgs = self.__pdf2imgs_ppm(pdf_path)
            # log_print("\tpages: # {}".format(len(page_imgs)))
            return page_imgs
        else:  # not yet
            log_print("Not defined file type.")
            sys.exit(1)

    def __pdf2imgs_ppm(self, _pdf_path):
        # get the base name for the converted jpg image files
        dir, fname = os.path.split(_pdf_path)
        base, ext = os.path.splitext(fname)
        out_base, _ = os.path.splitext(_pdf_path)

        # convert the pdf file to the jpg images
        command = 'pdftoppm %s %s -jpeg' % (_pdf_path.replace(' ', '\ '), out_base.replace(' ', '\ '))
        os.system(command)

        paths = []
        # convert the jpg files to the list of cv image
        for f in os.listdir(dir):
            path = os.path.join(dir, f)
            if os.path.exists(path) and f.find(base) != -1 and os.path.splitext(f)[1].find('jpg') != -1:
                paths.append(path)

        return paths


if __name__ == '__main__':
    pdfPath = '../data/020294-0020843.pdf'
    image_paths = PdfUbuntuUtils().pdfTojpgs(pdf_path=pdfPath)
    print(image_paths)
