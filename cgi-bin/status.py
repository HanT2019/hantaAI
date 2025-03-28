#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import urllib.request
import sys, json
import os
import subprocess
import psutil
from setproctitle import setproctitle
from process import check_inference
from lib.inference_manager import get_inference_name

def http_json_output(response):
    print("Status: 200 OK")
    print('Content-Type:application/json')
    print("Content-Length: %d" % len(response))
    print("")
    print(response)

def return_response(code, message, desc, progress):
    return_dict = {}
    result_data = {"code":200, "message": "", "desc": "", "progress":0}
    result_data["code"] = code
    result_data["message"] = message
    result_data["desc"] = desc
    result_data["progress"] = progress

    return_dict['result'] = result_data
    response = '{0}\n'.format(json.dumps(return_dict))
    http_json_output(response)

data = sys.stdin.read()

try:
    request_json = json.loads(data)
except:
    return_response(999, "Invalid json_format", "Invalid json_format", 0)
    sys.exit()

try:
    accident_id = request_json["id"]
    inference_type = request_json["inference_type"]
except:
    return_response(999, "Invalid parameter", "Invalid parameter", 0)
    sys.exit()

if type(inference_type) is not int:
    return_response(1001, 'Invalid inference_type: (must be int)', 'Invalid inference_type: (must be int)', 0)
    sys.exit()

valid_flag = check_inference(inference_type)
if valid_flag == 0:
    return_response(1003, 'Invalid inference_type: (Invalid number)', 'Invalid inference_type: (Invalid number)', 0)
    sys.exit()

data_dir = '/tmp'
try:
    accident_dir_path = os.path.join(data_dir, accident_id) # /tmp/<id>
except:
    return_response(1000, "Invalid id", "id should be text-format", 0)
    sys.exit()

if not os.path.exists(accident_dir_path):
    return_response(2000, "Path error", "Data dir not found for id:" + accident_id, 0)
    sys.exit()

status_file_path = os.path.join(accident_dir_path, str(inference_type) + '_status.json')

if not os.path.exists(status_file_path):
    return_response(2000, "Path error", "Status file not found for id:" + accident_id, 0)
    sys.exit()

with open(status_file_path) as f:
    data = f.read()
    try:
        status_json = json.loads(data)
    except:
        return_response(2100, "Invalid status json format for id", "Invalid status json format for id " + accident_id, 0)
        sys.exit()

    http_json_output(data)
