import io
import numpy as np
import cv2
from logger import *
from wand.image import Image as WandImage
from wand.color import Color as WandColor
from PyPDF2 import PdfFileReader, PdfFileWriter


class PdfWinUtils:
    def __init__(self, resolution=200):
        self.resolution = resolution  # DPI

    def pdfTojpgs(self, pdf_path):
        if not os.path.exists(pdf_path):
            log_print("\tNo exist such pdf file {}".format(pdf_path))
            sys.exit(1)
        trail, fname = os.path.split(pdf_path)
        base, ext = os.path.splitext(fname)
        file_type = ext[1:].upper()

        if file_type in EXT_DOC:  # pdf
            page_imgs = self.__pdf2imgs_wand(pdf_path)
            paths = []
            for id in range(len(page_imgs)):
                img = page_imgs[id]
                img_path = os.path.join(trail, (base + "-" + str(id + 1) + ".jpg"))
                cv2.imwrite(img_path, img)
                paths.append(img_path)
            # log_print("\tpages: # {}".format(len(paths)))
            return paths

        else:
            log_print("\tNot defined file type.")

    def __pdf2imgs_wand(self, _pdf_path):
        images = []
        reader = PdfFileReader(open(_pdf_path, "rb"))

        for page_num in range(reader.getNumPages()):
            src_page = reader.getPage(page_num)

            dst_pdf = PdfFileWriter()
            dst_pdf.addPage(src_page)

            pdf_bytes = io.BytesIO()
            dst_pdf.write(pdf_bytes)
            pdf_bytes.seek(0)

            with WandImage(file=pdf_bytes, resolution=self.resolution) as wand_img:
                # convert wand image to ndarray cv
                wand_img.background_color = WandColor('white')
                wand_img.format = 'tif'
                wand_img.alpha_channel = False
                img_buffer = np.asarray(bytearray(wand_img.make_blob()), dtype=np.uint8)

            if img_buffer is not None:
                cv_img = cv2.imdecode(img_buffer, cv2.IMREAD_GRAYSCALE)
            images.append(cv_img)
        return images


if __name__ == '__main__':
    pdfPath = '../data/020294-0020843.pdf'
    image_paths = PdfWinUtils().pdfTojpgs(pdfPath)
    print(image_paths)
