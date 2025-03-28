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
logger = getLogger(__file__)

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

data = sys.stdin.read()

import socket
import datetime
total, used, free = shutil.disk_usage('/')
logger.info(f'Server Address: {socket.gethostbyname(socket.gethostname())}')
logger.info(f'Request Date: {datetime.datetime.now()}, Body: {data}, To: {__file__}')
logger.info(f'Disk Usage: Used: {used / (2**30)}GiB, Free: {free / (2**30)}GiB')
if free / (2**30) < 0.5:
    logger.warning('Low disk space.')

if "inference_process" in (p.name() for p in psutil.process_iter()):
    logger.warning('Process is busy.')
    return_response(1400, "Process is busy.", "Process is busy.")
    sys.exit()

try:
    request_json = json.loads(data)
except:
    logger.error('The JSON format of the request is invalid.')
    return_response(999, "Invalid json_format", "The JSON format of the request is invalid.")
    sys.exit()

try:
    param_name="id"
    accident_id = request_json["id"]
except:
    logger.error(f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    return_response(999, "Invalid parameter", f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    sys.exit()

try:
    param_name="inference_type"
    inference_type = request_json["inference_type"]
except:
    logger.error(f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    return_response(999, "Invalid parameter", f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    sys.exit()

try:
    param_name="input_dir"
    s3_input_dir = request_json["input_dir"]
except:
    logger.error(f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    return_response(999, "Invalid parameter", f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    sys.exit()

try:
    param_name="input_file_last_no"
    s3_input_length = request_json["input_file_last_no"]
except:
    logger.error(f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    return_response(999, "Invalid parameter", f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    sys.exit()

try:
    param_name="output_file"
    s3_output_file = request_json["output_file"]
except:
    logger.error(f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    return_response(999, "Invalid parameter", f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    sys.exit()

try:
    param_name="progress_file"
    s3_progress_file = request_json["progress_file"]
except:
    logger.error(f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    return_response(999, "Invalid parameter", f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    sys.exit()

try:
    param_name="vertical_angle"
    vertical_angle = request_json["vertical_angle"]
except:
    logger.error(f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    return_response(999, "Invalid parameter", f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    sys.exit()

try:
    param_name="horizontal_angle"
    horizontal_angle = request_json["horizontal_angle"]
except:
    logger.error(f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    return_response(999, "Invalid parameter", f'"{param_name}" not found. Please include the correct "{param_name}" in the request JSON.')
    sys.exit()

if len(bytes(accident_id, encoding='utf-8')) != len(accident_id):
    logger.error('id should be Half-width alphanumeric characters.')
    return_response(1000, "Invalid id", "id should be Half-width alphanumeric characters.")
    sys.exit()

if type(inference_type) is not int:
    logger.error('inference_type should be integer.')
    return_response(1001, 'Invalid inference_type', 'inference_type should be integer.')
    sys.exit()

if type(s3_input_length) is not int:
    logger.error('input_file_last_no should be integer.')
    return_response(1002, 'Invalid input_file_last_no', 'input_file_last_no should be integer.')
    sys.exit()

if type(s3_input_dir) is not str:
    logger.error('input_dir should be string.')
    return_response(999, "Invalid parameter", "input_dir should be string.")
    sys.exit()

if len(bytes(s3_input_dir, encoding='utf-8')) != len(s3_input_dir):
    logger.error('input_dir should be encoded in utf-8.')
    return_response(999, "Invalid parameter", "input_dir should be encoded in utf-8.")
    sys.exit()

if type(s3_output_file) is not str:
    logger.error('output_file should be string.')
    return_response(999, "Invalid parameter", "output_file should be string.")
    sys.exit()

if len(bytes(s3_output_file, encoding='utf-8')) != len(s3_output_file):
    logger.error('output_file should be encoded in utf-8.')
    return_response(999, "Invalid parameter", "output_file should be encoded in utf-8.")
    sys.exit()

if type(s3_progress_file) is not str:
    logger.error('progress_file should be string.')
    return_response(999, "Invalid parameter", "progress_file should be string.")
    sys.exit()

if len(bytes(s3_progress_file, encoding='utf-8')) != len(s3_progress_file):
    logger.error('progress_file should be encoded in utf-8.')
    return_response(999, "Invalid parameter", "progress_file should be encoded in utf-8.")
    sys.exit()

if not type(vertical_angle) in [int, float]:
    logger.error('vertical_angle should be float number.')
    return_response(1004, 'Invalid vertical_angle', 'vertical_angle should be float number.')
    sys.exit()

if not type(horizontal_angle) in [int, float]:
    logger.error('horizontal_angle should be float number.')
    return_response(1004, 'Invalid horizontal_angle', 'horizontal_angle should be float number.')
    sys.exit()

additional_args = {
    'vertical_angle': vertical_angle,
    'horizontal_angle': horizontal_angle
}

valid_flag = check_inference(inference_type)

if valid_flag == 0 or inference_type not in [1, 7]:
    logger.error('inference_type should be 1 or 7.')
    return_response(1003, 'Invalid inference_type: (Invalid number)', 'inference_type should be 1 or 7.')
    sys.exit()

data_dir = '/tmp'

try:
    accident_dir_path = os.path.join(data_dir, accident_id) # /tmp/<id>
except:
    logger.error('id should be Half-width alphanumeric characters.')
    return_response(1000, "Invalid id", "id should be Half-width alphanumeric characters.")
    sys.exit()

images_dir_path = os.path.join(accident_dir_path, "images") # /tmp/<id>/images

pid = os.fork()
if pid == 0:
    setproctitle("inference_process")
    if not os.path.exists(accident_dir_path):
        os.mkdir(accident_dir_path)
        os.chmod(accident_dir_path, 0o777)
    if not os.path.exists(images_dir_path):
        os.mkdir(images_dir_path)
    else:
        # force delete images
        shutil.rmtree(images_dir_path)
        os.mkdir(images_dir_path)

    progress = 0
    write_status(inference_type, 200, "Images downloading","Images downloading", progress, accident_dir_path, s3_progress_file)

    try:
        bucket = bucket_setup_for_download()
        for i in range(1, s3_input_length+1):
            save_as = images_dir_path + '/' + '{:0=4}.jpg'.format(i)
            s3_file_path = os.path.join(s3_input_dir, '{:0=4}.jpg'.format(i))
            bucket.download_file(s3_file_path, save_as)
        progress = 10
        write_status(inference_type, 200, "Images downloaded","Images downloaded", progress, accident_dir_path, s3_progress_file)
    except:
        logger.critical(f'Image "{s3_file_path}" could not be downloaded.')
        write_status(inference_type, 1100, "Image download error", "Image could not be downloaded.", progress, accident_dir_path, s3_progress_file)
        sys.exit()

    path = "/var/www/cgi-bin/"
    src_name = "process.py"

    subprocess.call(["python3", path + src_name, str(inference_type), accident_id, "1", str(s3_input_length), accident_dir_path, s3_output_file, s3_progress_file, json.dumps(additional_args)])
    sys.exit()
else:
    os.waitpid(pid,0)

return_response(200, '', '')
sys.exit()
