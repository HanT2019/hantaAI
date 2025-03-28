#! /usr/bin/env python
import imghdr
import os
import sys
import numpy as np
import traceback

from yolo import Yolo

sys.path.append('/var/www/cgi-bin/lib')
from inference_manager import get_inference_type
from file_output import write_status, write_result
from image_type_manager import is_jpg
from reshape_return_dict import reshape_signal
from mylogger import getLogger

logger = getLogger(__name__)
inference_type = get_inference_type('app_signal_detection')

INFERENCE_ROOT = '/var/www/cgi-bin/lib/app_signal_detection/'
STATIC_PARAMS = {
    'model_path': INFERENCE_ROOT + 'model_data/app_signal_detection.h5',
    'anchors_path': INFERENCE_ROOT + 'model_data/app_signal_detection_anchors.txt',
    'classes_path': INFERENCE_ROOT + 'model_data/app_signal_detection.names',
}
COLORS = {
    'none': '00',
    'unknown': '00',
    'blue': '01',
    'blue_red': '02',
    'blue_yellow': '03',
    'red': '04',
    'yellow': '06',
    'yellow_red': '07',
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

    image_file_list = [os.path.join(images_dir, '{:0=4}.jpg'.format(i)) for i in range(start_no, end_no + 1)]
    file_sum = len(image_file_list)
    file_counter = 0
    object_id = 1

    # Detect signals for frame by frame
    for image_file in image_file_list:
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

        for class_name, top, left, bottom, right in boxes:
            x = np.floor((right + left) / 2).astype('int32')
            y = np.floor((bottom + top) / 2).astype('int32')
            w = np.floor(right - left).astype('int32')
            h = np.floor(bottom - top).astype('int32')

            detected_object = {}
            detected_object['id'] = object_id
            detected_object['x'] = int(x)
            detected_object['y'] = int(y)
            detected_object['w'] = int(w)
            detected_object['h'] = int(h)
            detected_object['color'] = 'unknown'

            for color in ['red', 'yellow', 'blue']:
                if color in class_name:
                    detected_object['color'] = color
                    break

            object_array.append(detected_object)
            object_id += 1

        frame_data['signals'] = object_array
        frame_array.append(frame_data)

        # Progress report
        progress = 0.1 + 0.8*(float(file_counter)/float(file_sum))
        if progress>0.89:
            progress = 0.89
        write_status(inference_type, 200, "","", int(progress*100), ec2_output_dir, s3_progress_file)

    result_data['frames'] = frame_array
    return_dict['result'] = result_data

    return_dict = reshape_signal(return_dict)
    return_dict['result']['judgements']['signal_color_code'] = COLORS[return_dict['result']['judgements']['signal_color_code']]

    if object_id > 1:
        return_dict['result']['judgements']['signal_flag_code'] = '01'
    else:
        return_dict['result']['judgements']['signal_flag_code'] = '02'
        return_dict['result']['judgements']['signal_color_code'] = COLORS['none']

    write_result(inference_type, return_dict, ec2_output_dir, s3_output_file)
    write_status(inference_type, 200, '', '', 100, ec2_output_dir, s3_progress_file)

if __name__ == '__main__':
    try:
        args = sys.argv
        main(args[1], args[2], int(args[3]), int(args[4]), args[5], args[6], args[7])
    except:
        logger.critical(traceback.print_exc())
        write_status(inference_type, 500, 'Internal error', 'Internal error', 100, args[5], args[7])
