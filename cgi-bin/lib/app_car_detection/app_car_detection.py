#! /usr/bin/env python
import imghdr
import os
import sys
import traceback
import numpy as np

from yolo import Yolo

sys.path.append('/var/www/cgi-bin/lib')
from inference_manager import get_inference_type
from file_output import write_status, write_result
from image_type_manager import is_jpg
from mylogger import getLogger

logger = getLogger(__file__)
inference_type = get_inference_type('app_car_detection')

INFERENCE_ROOT = '/var/www/cgi-bin/lib/app_car_detection/'
STATIC_PARAMS = {
    'model_path': INFERENCE_ROOT + 'model_data/app_car_detection.h5',
    'anchors_path': INFERENCE_ROOT + 'model_data/app_car_detection_anchors.txt',
    'classes_path': INFERENCE_ROOT + 'model_data/app_car_detection.names',
}

def main(accident_id, images_dir, start_no, end_no, ec2_output_dir, s3_output_file, s3_progress_file):
    # Prepare for result
    return_dict = {}
    result_data = {'id': accident_id}

    # Yolo class initialization
    model_path = STATIC_PARAMS['model_path']
    anchors_path = STATIC_PARAMS['anchors_path']
    classes_path = STATIC_PARAMS['classes_path']
    yolo = Yolo(model_path, anchors_path, classes_path)

    progress = 10

    frame_array = []

    file_sum = len([name for name in sorted(os.listdir(images_dir)) if os.path.isfile(os.path.join(images_dir, name))])
    file_counter = 0
    object_id = 1

    # Detect cars for frame by frame
    for image_file in sorted(os.listdir(images_dir)):
        file_counter += 1
        try:
            image_type = imghdr.what(os.path.join(images_dir, image_file))
            is_jpg_file = is_jpg(os.path.join(images_dir, image_file))
            if not image_type and not is_jpg_file:
                continue
        except IsADirectoryError:
            continue

        frame_data = {}
        frame_data['no'] = file_counter

        boxes = yolo.predict(os.path.join(images_dir, image_file))

        object_array = []

        for top, left, bottom, right in boxes:
            x = np.floor((right + left) / 2).astype('int32')
            y = np.floor((bottom + top) / 2).astype('int32')
            w = np.floor(right - left).astype('int32')
            h = np.floor(bottom - top).astype('int32')

            detected_object = {'id': str(object_id), 'bbox': {}, 'bev': None}
            detected_object['bbox']['x'] = int(x)
            detected_object['bbox']['y'] = int(y)
            detected_object['bbox']['w'] = int(w)
            detected_object['bbox']['h'] = int(h)

            object_array.append(detected_object)
            object_id += 1

        frame_data['cars'] = object_array
        frame_array.append(frame_data)

        # Progress report
        progress = 0.1 + 0.9*(float(file_counter)/float(file_sum))
        if progress>0.99:
            progress = 0.99
        write_status(inference_type, 200, "","", int(progress*100), ec2_output_dir, s3_progress_file)

    result_data['frames'] = frame_array
    return_dict['result'] = result_data

    write_result(inference_type, return_dict, ec2_output_dir, s3_output_file)
    write_status(inference_type, 200, '', '', 100, ec2_output_dir, s3_progress_file)

if __name__ == '__main__':
    try:
        args = sys.argv
        main(args[1], args[2], int(args[3]), int(args[4]), args[5], args[6], args[7])
    except:
        write_status(inference_type, 500, 'Internal error', 'Internal error', 100, args[5], args[7])
