#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys, os
import json
import boto3

sys.path.append('/var/www/cgi-bin/lib')
from inference_manager import get_inference_name

def s3_setup():
    s3 = boto3.resource('s3')
    return s3

BUCKET_NAME = os.environ.get('AWS_S3_BUCKET_NAME')

def bucket_setup_for_download():
    s3 = s3_setup()
    bucket = s3.Bucket(BUCKET_NAME)
    return bucket

def bucket_setup(file_name):
    s3 = s3_setup()
    bucket = s3.Object(BUCKET_NAME, file_name)
    return bucket

def write_status(inference_type, code, message, desc, progress, ec2_output_dir, s3_progress_file):
    result_data = {"code":200, "message": "", "desc": ""}
    result_data["code"] = code
    result_data["message"] = message
    result_data["desc"] = desc
    result_data["progress"] = int(progress)

    return_dict = {}
    return_dict['result'] = result_data

    response = '{0}\n'.format(json.dumps(return_dict))

    bucket = bucket_setup(s3_progress_file)
    bucket.put(Body=response)

    file_path = os.path.join(ec2_output_dir, str(inference_type) + '_status.json')
    with open(file_path, 'w') as fout:
        fout.write(response)

def write_result(inference_type, return_dict, ec2_output_dir, s3_output_file):
    response = '{0}\n'.format(json.dumps(return_dict))

    bucket = bucket_setup(s3_output_file)
    bucket.put(Body=response)

    file_path = os.path.join(ec2_output_dir, str(inference_type) + '_result.json')
    with open(file_path, 'w') as fout:
        fout.write(response)

    bucket = bucket_setup(file_path)
    bucket.put(Body=response)
