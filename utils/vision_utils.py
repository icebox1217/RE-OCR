import cv2
import base64
import json
import requests
import math
import numpy as np
import logger as log
from PIL import Image, ExifTags
from utils.config import *


# correlate the orientation of the input image with its meta infomation
# and then return the cv_mat(ndarray) image
def load_image(image_path):
    try:
        image = Image.open(image_path)
        orientation = None
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = dict(image._getexif().items())

        if exif[orientation] == 3:
            image = image.rotate(180, expand=True)
        elif exif[orientation] == 6:
            image = image.rotate(270, expand=True)
        elif exif[orientation] == 8:
            image = image.rotate(90, expand=True)

        cv_img = np.array(image)
        cv_img = cv_img[:, :, ::-1].copy()
        return cv_img
    except (AttributeError, KeyError, IndexError):
        # cases: image don't have getexif
        cv_img = cv2.imread(image_path)
        return cv_img


def rect_orientation(anno):
    points = anno['boundingBox']['vertices']
    cen_x = .0
    cen_y = .0
    for i in range(4):
        if 'x' not in points[i].keys():
            points[i]['x'] = 0
        if 'y' not in points[i].keys():
            points[i]['y'] = 0
        cen_x += points[i]['x']
        cen_y += points[i]['y']

    cen_x /= 4
    cen_y /= 4

    x0 = points[0]['x']
    y0 = points[0]['y']

    if x0 < cen_x:
        if y0 < cen_y:
            return ORIENTATION_NORMAL
        else:
            return ORIENTATION_270_DEGREE
    else:
        if y0 < cen_y:
            return ORIENTATION_90_DEGREE
        else:
            return ORIENTATION_180_DEGREE


def correlate_orientation(anno, orientation, img_width, img_height):
    points = anno['boundingBox']['vertices']

    for i in range(4):
        point = points[i]
        if 'x' not in point.keys():
            point['x'] = 0
        if 'y' not in point.keys():
            point['y'] = 0

        if orientation == ORIENTATION_NORMAL:
            new_x = point['x']
            new_y = point['y']
        elif orientation == ORIENTATION_270_DEGREE:
            new_x = img_height - point['y']
            new_y = point['x']
        elif orientation == ORIENTATION_90_DEGREE:
            new_x = point['y']
            new_y = img_width - point['x']
        elif orientation == ORIENTATION_180_DEGREE:
            new_x = img_width - point['x']
            new_y = img_height - point['y']

        points[i]['x'] = new_x
        points[i]['y'] = new_y


def make_request(cv_img, feature_types):
    request_list = []

    # Read the image and convert to the base string to send as json
    h, w = cv_img.shape[:2]
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    _ratio = math.sqrt(float(MAXIMUM_SIZE) / float(h * w))

    gray = cv2.resize(gray, (int(w * _ratio), int(h * _ratio)))
    resz_img = cv2.resize(cv_img, (int(w * _ratio), int(h * _ratio)))
    _quality = 100

    content_obj = {'content': base64.b64encode(
        cv2.imencode('.jpg', gray, [cv2.IMWRITE_JPEG_QUALITY, _quality])[1].tostring()).decode('UTF-8')}

    feature_obj = []
    for feature_type in feature_types:
        feature_obj.append({'type': feature_type})

    context_obj = {"languageHints": ['en']}

    request_list.append(
        {'image': content_obj,
         'features': feature_obj,
         'imageContext': context_obj
         }
    )
    return json.dumps({'requests': request_list}).encode(), resz_img


class VisionUtils:
    def __init__(self, show_result=True):
        self.endpoint_url = ENDPOINT_URL
        self.api_key = API_KEY
        self.show_result = show_result

    def __get_response(self, json_data):
        try:
            response = requests.post(
                url=self.endpoint_url,
                data=json_data,
                params={'key': self.api_key},
                headers={'Content-Type': 'application/json'})

            # print(response)
            ret_json = json.loads(response.text)
            return ret_json['responses'][0]

        except Exception as e:
            log.print("\t\texcept: {}".format(e))
            return None
    
    def __get_orientation(self, annos):
        oris = [0, 0, 0, 0]
        for anno in annos:
            ori = rect_orientation(anno=anno)
            oris[ori] += 1
        if self.show_result:
            log.print(" {}".format(oris))
        return oris.index(max(oris))

    def detect_text(self, path, idx, proc_queue):
        try:
            img = load_image(path)
            requests, resz_img = make_request(cv_img=img, feature_types=['DOCUMENT_TEXT_DETECTION', 'TEXT_DETECTION',
                                                                         'LABEL_DETECTION'])

            response = self.__get_response(requests)
            img = resz_img

            if response is None:
                result = None
            else:
                _flag = False
                for i in range(5):
                    if response['labelAnnotations'][i]['description'] != 'text':
                        _flag = True
                        break

                if not _flag:
                    ret_label = response['labelAnnotations'][0]
                    result = {'id': idx,
                              'annotations': None,
                              'label': ret_label,
                              'orientation': None,
                              'image': img}
                    log.print("\t Not proper Invoice Document{}".format(ret_label))
                else:
                    annos = []
                    document = response['fullTextAnnotation']
                    for page in document['pages']:
                        for block in page['blocks']:
                            for paragraph in block['paragraphs']:
                                for word in paragraph['words']:
                                    text = ""
                                    for symbol in word['symbols']:
                                        text += symbol['text']

                                    if type(text) is not str:
                                        text = text.encode("utf-8")

                                    anno = {
                                        'boundingBox': word['boundingBox'],
                                        'text': text
                                    }
                                    annos.append(anno)

                    # recognize the orientation                    
                    ori = self.__get_orientation(annos=annos)
                    
                    height, width = img.shape[:2]
                    if ori != ORIENTATION_NORMAL:
                        img = cv2.rotate(img, rotateCode=ori)
                    for anno in annos:
                        correlate_orientation(anno=anno, orientation=ori, img_width=width, img_height=height)
                        if self.show_result:  # display the line rect
                            pt0 = anno['boundingBox']['vertices'][0]
                            pt1 = anno['boundingBox']['vertices'][2]
                            cv2.line(img, (pt0['x'], pt0['y']), (pt1['x'], pt1['y']), (0, 255, 0), 1)

                    result = {'id': idx,
                              'annotations': annos,
                              'label': 'text',
                              'orientation': ori,
                              'image': img}

            proc_queue.put(result, True, 1)
        except Exception as e:
            log.print("\t exception :" + str(e))
            pass
