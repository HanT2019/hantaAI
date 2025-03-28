#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
import urllib.request
import sys, json
import os
import subprocess
import psutil
import shutil
from boto3 import resource
from setproctitle import setproctitle
from process import check_inference
from lib.file_output import bucket_setup_for_download, s3_setup, write_status
from lib.inference_manager import get_inference_name

from lib.mylogger import getLogger
logger = getLogger(__name__)

def return_response(code, message, desc):
    return_dict = {}
    result_data = {"code":200, "message": "", "desc": ""}
    result_data["code"] = code
    result_data["message"] = message
    result_data["desc"] = desc
    return_dict['result'] = result_data
    response = '{0}\n'.format(json.dumps(return_dict))

    print("Status: 200 OK")
    print('Content-Type:application/json')
    print("Content-Length: %d" % len(response))
    print("")
    print(response)

def check_frame_info(frame_info):
    for key in ['frame_no', 'x', 'y', 'w', 'h']:
        if type(frame_info[key]) is not int:
            return_response(1006, 'Invalid {0}: ({0} isn\'t int)'.format(key), 'Invalid {0}: ({0} isn\'t int)'.format(key))
            sys.exit()

data = sys.stdin.read()

import socket
import datetime
total, used, free = shutil.disk_usage('/')
logger.info(f'Server Address: {socket.gethostbyname(socket.gethostname())}')
logger.info(f'Request Date: {datetime.datetime.now()}, Body: {data}, To: {__file__}')
logger.info(f'Disk Usage: Used: {used / (2**30)}GiB, Free: {free / (2**30)}GiB')
if free / (2**30) < 0.5:
    logger.warning('Low disk capacity')

if "inference_process" in (p.name() for p in psutil.process_iter()):
    logger.warning('Process is busy')
    return_response(1400, "Process is busy.", "Please wait a minute.")
    sys.exit()

try:
    request_json = json.loads(data)
except:
    logger.error('Invalid json_format')
    return_response(999, "Invalid json_format", "Invalid json_format")
    sys.exit()

try:
    param_name="id"
    accident_id = request_json["id"]
except:
    logger.error(f'Invalid parameter {param_name}')
    return_response(999, "Invalid parameter", "Invalid parameter: "+param_name)
    sys.exit()

try:
    param_name="inference_type"
    inference_type = request_json["inference_type"]
except:
    logger.error(f'Invalid parameter {param_name}')
    return_response(999, "Invalid parameter", "Invalid parameter: "+param_name)
    sys.exit()

try:
    param_name="input_dir"
    s3_input_dir = request_json["input_dir"]
except:
    logger.error(f'Invalid parameter {param_name}')
    return_response(999, "Invalid parameter", "Invalid parameter: "+param_name)
    sys.exit()

try:
    param_name="output_file"
    s3_output_file = request_json["output_file"]
except:
    logger.error(f'Invalid parameter {param_name}')
    return_response(999, "Invalid parameter", "Invalid parameter: "+param_name)
    sys.exit()

try:
    param_name="progress_file"
    s3_progress_file = request_json["progress_file"]
except:
    logger.error(f'Invalid parameter {param_name}')
    return_response(999, "Invalid parameter", "Invalid parameter: "+param_name)
    sys.exit()

try:
    param_name="start_frame"
    start_frame = request_json["start_frame"]
except:
    logger.error(f'Invalid parameter {param_name}')
    return_response(999, "Invalid parameter", "Invalid parameter: "+param_name)
    sys.exit()

try:
    param_name="end_frame"
    end_frame = request_json["end_frame"]
except:
    logger.error(f'Invalid parameter {param_name}')
    return_response(999, "Invalid parameter", "Invalid parameter: "+param_name)
    sys.exit()

if len(bytes(accident_id, encoding='utf-8')) != len(accident_id):
    logger.error('id should be Half-width alphanumeric characters.')
    return_response(1000, "Invalid id", "id should be Half-width alphanumeric characters.")
    sys.exit()

if type(inference_type) is not int:
    logger.error('inference_type should be integer.')
    return_response(1001, 'Invalid inference_type', 'inference_type should be integer.')
    sys.exit()

if type(s3_input_dir) is not str:
    logger.error('input_dir should be string.')
    return_response(999, "Invalid parameter", "Invalid parameter: input_dir")
    sys.exit()

if len(bytes(s3_input_dir, encoding='utf-8')) != len(s3_input_dir):
    logger.error('input_dir should be encoded in utf-8.')
    return_response(999, "Invalid parameter", "Invalid parameter: input_dir")
    sys.exit()

if type(s3_output_file) is not str:
    logger.error('output_file should be string.')
    return_response(999, "Invalid parameter", "Invalid parameter: output_file")
    sys.exit()

if len(bytes(s3_output_file, encoding='utf-8')) != len(s3_output_file):
    logger.error('output_file should be encoded in utf-8.')
    return_response(999, "Invalid parameter", "Invalid parameter: output_file")
    sys.exit()

if type(s3_progress_file) is not str:
    logger.error('progress_file should be string.')
    return_response(999, "Invalid parameter", "Invalid parameter: progress_file")
    sys.exit()

if len(bytes(s3_progress_file, encoding='utf-8')) != len(s3_progress_file):
    logger.error('progress_file should be encoded in utf-8.')
    return_response(999, "Invalid parameter", "Invalid parameter: progress_file")
    sys.exit()

valid_flag = check_inference(inference_type)

if valid_flag == 0 or inference_type == 1:
    logger.error('inference_type should be in the range between 2 to 5.')
    return_response(1003, 'Invalid inference_id: (Invalid number)', 'Invalid inference_id: (Invalid number)')
    sys.exit()

check_frame_info(start_frame)
check_frame_info(end_frame)

if start_frame["frame_no"] <= 0:
    logger.error('start-frame_no must be greater than 0.')
    return_response(1004, 'Invalid start-frame_no: (Invalid number)', 'start-frame_no must be greater than 0.')
    sys.exit()

if start_frame["frame_no"] >= end_frame["frame_no"]:
    logger.error('end-frame_no must be greater than start-frame_no.')
    return_response(1005, 'Invalid end-frame_no: (Invalid number)', 'end-frame_no must be greater than start-frame_no.')
    sys.exit()

data_dir = '/tmp'

try:
    accident_dir_path = os.path.join(data_dir, accident_id) # /tmp/<id>
except:
    logger.error('id should be string.')
    return_response(1000, "Invalid id", "id should be text-format")
    sys.exit()

images_dir_path = os.path.join(accident_dir_path, "images") # /tmp/<id>/images

pid = os.fork()
if pid == 0:
    setproctitle("inference_process")
    if not os.path.exists(accident_dir_path):
        os.mkdir(accident_dir_path)
    if not os.path.exists(images_dir_path):
        os.mkdir(images_dir_path)

    progress = 0
    write_status(inference_type, 200, "Images downloading","Images downloading", progress, accident_dir_path, s3_progress_file)

    try:
        bucket = bucket_setup_for_download()
        for i in range(start_frame["frame_no"], end_frame["frame_no"]+1):
            save_as = images_dir_path + '/' + '{:0=4}.jpg'.format(i)
            if not os.path.exists(save_as):
                s3_file_path = os.path.join(s3_input_dir, '{:0=4}.jpg'.format(i))
                bucket.download_file(s3_file_path, save_as)
        progress = 10
        write_status(inference_type, 200, "Images downloaded","Images downloaded", progress, accident_dir_path, s3_progress_file)
    except:
        write_status(inference_type, 1100, "Image download error", "Image could not be downloaded.", progress, accident_dir_path, s3_progress_file)
        sys.exit()

    # /tmp/<id>/keyframes.txt
    with open(os.path.join(accident_dir_path, 'keyframes.txt'), 'w') as f:
        f.write(f'{start_frame["frame_no"]} {start_frame["x"]} {start_frame["y"]} {start_frame["w"]} {start_frame["h"]}\n')
        f.write(f'{end_frame["frame_no"]} {end_frame["x"]} {end_frame["y"]} {end_frame["w"]} {end_frame["h"]}\n')

    # load result of app_car_detection
    try:
        bucket = bucket_setup_for_download()
        cars_result_path = os.path.join(accident_dir_path, '1_result.json')

        if not os.path.exists(cars_result_path):
            bucket.download_file(cars_result_path, cars_result_path)
    except:
        logger.critical('Image could not be downloaded.')
        write_status(inference_type, 400, 'Invalid request', '"inference_type=1" is not executed yet.', progress, accident_dir_path, s3_progress_file)
        sys.exit()

    path = "/var/www/cgi-bin/"
    src_name = "process.py"

    subprocess.call(["python3", path + src_name, str(inference_type), accident_id, str(start_frame["frame_no"]), str(end_frame["frame_no"]), accident_dir_path, s3_output_file, s3_progress_file])
    sys.exit()

return_response(200, '', '')
sys.exit()
