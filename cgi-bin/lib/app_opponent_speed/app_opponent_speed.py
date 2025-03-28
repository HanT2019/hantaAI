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

logger = getLogger(__name__)
inference_type = get_inference_type('app_opponent_speed')


def main(accident_id, images_dir, start_no, end_no, ec2_output_dir, s3_output_file, s3_progress_file, additional_args_str):
    progress = 10

    # POSTパラメータ、GETパラメータ作成
    additional_args = json.loads(additional_args_str)
    if not 'fps' in additional_args.keys():
        logger.error('"fps" is not found')
        write_status(inference_type, 500, 'Internal error', '"fps" is not found', progress, ec2_output_dir, s3_progress_file)
        sys.exit()

    car_detection_inference_type = get_inference_type('app_3dbb_detection')
    car_detection_result_path = os.path.join(ec2_output_dir, f'{car_detection_inference_type}_result.json')
    if not os.path.exists(car_detection_result_path):
        logger.error('"inference_type=7" is not executed yet.')
        write_status(inference_type, 400, 'Invalid request', '"inference_type=7" is not executed yet.', progress, ec2_output_dir, s3_progress_file)
        sys.exit()

    keyframes_path = os.path.join(ec2_output_dir, 'keyframes.txt')
    if not os.path.exists(keyframes_path):
        logger.error('start/end frame information could not be read.')
        write_status(inference_type, 500, 'Internal error', 'start/end frame information could not be read.', progress, ec2_output_dir, s3_progress_file)
        sys.exit()

    post_parameters = {
        'accident_dir_path': ec2_output_dir,
        'car_detection_result_path': car_detection_result_path,
        'keyframes_path': keyframes_path,
        'fps': float(additional_args['fps'])
    }

    get_parameters = f'accident_dir_path={ec2_output_dir}'

    # 推論開始 POST
    response = requests.post(
        f'http://{get_inference_url(inference_type)}/',
        data = post_parameters
    )
    if response.status_code != 200:
        logger.error(response.text)
        write_status(inference_type, 500, 'Internal error', 'Inference process failed', progress, ec2_output_dir, s3_progress_file)
        sys.exit()

    # 推論進捗 GET
    while True:
        response = requests.get(f'http://{get_inference_url(inference_type)}/progress/')
        if response.status_code != 200:
            logger.error(response.text)
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
        logger.error(response.text)
        write_status(inference_type, 500, 'Internal error', 'Inference process failed', progress, ec2_output_dir, s3_progress_file)
        sys.exit()

    response_dict = json.loads(response.text)
    response_dict['result']['id'] = accident_id

    write_result(inference_type, response_dict, ec2_output_dir, s3_output_file)
    write_status(inference_type, 200, '', '', 100, ec2_output_dir, s3_progress_file)

if __name__ == '__main__':
    try:
        args = sys.argv
        main(args[1], args[2], int(args[3]), int(args[4]), args[5], args[6], args[7], args[8])
    except:
        logger.critical(traceback.print_exc())
        write_status(inference_type, 500, 'Internal error', 'Inference container not running', 100, args[5], args[7])
