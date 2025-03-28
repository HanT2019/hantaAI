#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys, os

inference_names = {1:"app_car_detection", 2:"app_intersection", 3:"app_self_direction", 4:"app_opponent_direction", 5:"app_signal_detection"}

def get_inference_name(inference_type):
    inference_name = ''

    if int(inference_type) in inference_names:
        inference_name = inference_names[int(inference_type)]

    return inference_name

def get_inference_type(inference_name):
    inference_type = -1

    if inference_name in inference_names.values():
        inference_type = [k for k, v in inference_names.items() if v == inference_name][0]

    return inference_type
