#! /usr/bin/env python
import imghdr
import os
import sys
import cv2
import time
import json
import traceback
import requests

sys.path.append('/var/www/cgi-bin/lib')
from inference_manager import get_inference_type, get_inference_url
from file_output import write_status, write_result
from mylogger import getLogger

logger = getLogger(__file__)
inference_type = get_inference_type('app_3dbb_detection')


def main(accident_id, images_dir, start_no, end_no, ec2_output_dir, s3_output_file, s3_progress_file, additional_args_str):
    tmp_inference_type = get_inference_type('app_car_detection')

    progress = 10

    # POSTパラメータ、GETパラメータ作成
    additional_args = json.loads(additional_args_str)
    if not 'vertical_angle' in additional_args.keys():
        logger.critical('"vertical_angle" is not found.')
        write_status(inference_type, 500, 'Internal error', '"vertical_angle" is not found', progress, ec2_output_dir, s3_progress_file)
        sys.exit()
    if not 'horizontal_angle' in additional_args.keys():
        logger.critical('"horizontal_angle" is not found.')
        write_status(inference_type, 500, 'Internal error', '"horizontal_angle" is not found', progress, ec2_output_dir, s3_progress_file)
        sys.exit()

    img = cv2.imread(os.path.join(images_dir, os.listdir(images_dir)[0]))
    height, width, _ = img.shape[:3]
    del img

    post_parameters = {
        'accident_dir_path': ec2_output_dir,
        'start_no': start_no,
        'end_no': end_no,
        'vfov': float(additional_args['vertical_angle']),
        'hfov': float(additional_args['horizontal_angle']),
        'width': width,
        'height': height
    }

    get_parameters = f'accident_dir_path={ec2_output_dir}'

    # 推論開始 POST
    response = requests.post(
        f'http://{get_inference_url(inference_type)}/',
        data = post_parameters
    )
    if response.status_code != 200:
        logger.critical('The docker container for app_3dbb_detection returned the following error: ' + response.text)
        write_status(inference_type, 500, 'Internal error', 'Inference process failed', progress, ec2_output_dir, s3_progress_file)
        sys.exit()

    # 推論進捗 GET
    while True:
        response = requests.get(f'http://{get_inference_url(inference_type)}/progress/')
        if response.status_code != 200:
            logger.critical('The docker container for app_3dbb_detection returned the following error: ' + response.text)
            write_status(inference_type, 500, 'Internal error', 'Inference process failed', progress, ec2_output_dir, s3_progress_file)
            sys.exit()

        response_dict = json.loads(response.text)
        progress = 10 + float(response_dict['progress'])*0.89
        write_status(inference_type, 200, response_dict['message'], response_dict['desc'], progress, ec2_output_dir, s3_progress_file)

        if int(response_dict['progress']) == 100:
            break

        time.sleep(1.0)

    # 推論結果 GET
    response = requests.get(f'http://{get_inference_url(inference_type)}/?{get_parameters}')
    if response.status_code != 200:
        logger.critical('The docker container for app_3dbb_detection returned the following error: ' + response.text)
        write_status(inference_type, 500, 'Internal error', 'Inference process failed', progress, ec2_output_dir, s3_progress_file)
        sys.exit()

    response_dict = json.loads(response.text)
    response_dict['result']['id'] = accident_id

    write_result(inference_type, response_dict, ec2_output_dir, s3_output_file)
    write_result(tmp_inference_type, response_dict, ec2_output_dir, s3_output_file)
    write_status(inference_type, 200, '', '', 100, ec2_output_dir, s3_progress_file)

if __name__ == '__main__':
    try:
        args = sys.argv
        main(args[1], args[2], int(args[3]), int(args[4]), args[5], args[6], args[7], args[8])
    except:
        write_status(inference_type, 500, 'Internal error', 'Inference process failed', 100, args[5], args[7])
