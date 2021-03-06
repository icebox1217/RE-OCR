import imutils
import math
import cv2
from logger import *


def rect_angle(anno):
    points = anno['boundingBox']['vertices']
    centerX = .0
    centerY = .0
    for i in range(4):
        if 'x' not in points[i].keys():
            points[i]['x'] = 0
        if 'y' not in points[i].keys():
            points[i]['y'] = 0
        centerX += points[i]['x'] / 4
        centerY += points[i]['y'] / 4
    x0 = points[0]['x']
    y0 = points[0]['y']

    if x0 < centerX and y0 < centerY:
        angle = 0.0
        for i in range(4):
            dx = points[(i + 1) % 4]['x'] - points[i]['x']
            dy = points[(i + 1) % 4]['y'] - points[i]['y']
            _atan = math.atan2(dy, dx)
            if _atan < 0: _atan += math.pi * 2
            radian = i * math.pi / 2 - _atan

            if radian < -math.pi:
                radian += math.pi * 2
            elif radian > math.pi:
                radian -= math.pi * 2

            angle += radian
        return angle / 4
    else:
        return None


def rotate_pt(pt, cen_pt, angle):
    angle = math.radians(-angle)
    dx = pt[0] - cen_pt[0]
    dy = pt[1] - cen_pt[1]

    new_dx = dx * math.cos(angle) - dy * math.sin(angle)
    new_dy = dx * math.sin(angle) + dy * math.cos(angle)

    new_x = new_dx + cen_pt[0]
    new_y = new_dy + cen_pt[1]
    return [int(new_x), int(new_y)]


def crop(content):
    # crop the image based on the page color(white)
    image = content['image']
    height, width = image.shape[:2]

    # find the border of the page entity
    left, top, right, bottom = width / 2, height / 2, width / 2, height / 2
    max_h = 0

    annos = content['annotations']
    for anno in annos:
        ul, ur, br, bl = anno['boundingBox']['vertices']
        _li_x = [ul['x'], ur['x'], br['x'], bl['x']]
        _li_y = [ul['y'], ur['y'], br['y'], bl['y']]

        left = min(min(_li_x), left)
        right = max(max(_li_x), right)
        top = min(min(_li_y), top)
        bottom = max(max(_li_y), bottom)

        max_h = max(max_h, math.fabs(bl['y']-ul['y']), math.fabs(br['y']-ur['y']))

    left = int(max(left - max_h, 0))
    top = int(max(top - max_h, 0))
    right = int(min(right + max_h, width))
    bottom = int(min(bottom + max_h, height))

    crop = image[top:bottom, left:right]
    content['image'] = crop

    # update the annos with new crop size
    for anno in annos:
        points = anno['boundingBox']['vertices']
        new_points = [{'x': point['x'] - left, 'y': point['y'] - top} for point in points]
        anno['boundingBox']['vertices'] = new_points


class PreProcUtils:
    def __init__(self, show_result=False):
        self.show_result = show_result

    def pre_proc(self, content):
        self.__align(content=content)
        crop(content=content)

        if self.show_result:
            image = content['image']
            for anno in content['annotations']:
                points = anno['boundingBox']['vertices']
                for i in range(len(points) - 1):
                    image = cv2.line(image, (points[i]['x'], points[i]['y']), (points[i + 1]['x'], points[i + 1]['y']),
                                     (255, 0, 0), 1)
            content['image'] = image

    def __align(self, content):
        deg_angle = self.__calc_angle(annos=content['annotations'])

        if math.fabs(deg_angle) < 0.5:
            return

        # rotate the image
        rotated = imutils.rotate(content['image'], deg_angle)
        content['image'] = rotated

        # update the annoataion rects with angles
        image = content['image']
        height, width = image.shape[:2]
        cen_pt = (width / 2, height / 2)
        for anno in content['annotations']:
            points = anno['boundingBox']['vertices']
            for point in points:
                new_pt = rotate_pt(pt=(point['x'], point['y']), cen_pt=cen_pt, angle=deg_angle)
                point['x'] = new_pt[0]
                point['y'] = new_pt[1]

    def __calc_angle(self, annos):
        # calculate the calibration rotated angle
        avg_angle = .0
        cnt = 0
        for anno in annos:
            angle = rect_angle(anno)
            if angle is not None and math.fabs(angle) < math.pi / 6:  # threshold with pi/6(30deg)
                cnt += 1
                avg_angle += angle

        avg_angle /= cnt
        avg_angle_deg = avg_angle * 180 / math.pi
        if self.show_result:
            log_print("\tCalibration Angle: {:0.2f}(deg)".format(avg_angle_deg))
        return -avg_angle_deg
