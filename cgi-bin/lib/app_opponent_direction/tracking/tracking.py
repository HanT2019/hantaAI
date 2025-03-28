#! /usr/bin/env python
import colorsys
import imghdr
import os
import sys
import random
import json
import math
import cv2
import datetime

import numpy as np

from .color_histogram import ColorHistogram

sys.path.append('/var/www/cgi-bin/lib')
from file_output import write_status
from inference_manager import get_inference_type

def initialize_frames(keyframes_path):
    key_frames =[]

    with open(keyframes_path, 'r') as keyframes_txt:
        for keyframe in keyframes_txt:
            no, cx, cy, w, h = tuple([int(v) for v in keyframe.strip().split(' ')])
            x, y, w, h = xywh_from_cxcywh(cx, cy, w, h)
            key_frames.append((no, x, y, w, h))

    track_frames = linear_prediction(key_frames)

    return track_frames, key_frames

def load_yolo_results(car_detection_result_path):
    yolo_results = []

    with open(car_detection_result_path) as f:
        data = json.load(f)

        for frame_data in data['result']['frames']:
            frame_result = []

            for car in frame_data['cars']:
                x, y, w, h = xywh_from_cxcywh(int(car['x']), int(car['y']), int(car['w']), int(car['h']))
                frame_result.append((x, y, w, h))

            yolo_results.append(frame_result)

    return yolo_results

def linear_prediction(key_frames=[]):
    prev_no  = -1
    prev_frame = None
    track_frames = []

    for key in sorted(key_frames):
        if prev_no >= 0:
            diff_no = key[0] - prev_no

            if diff_no > 1:
                delta_x = (key[1] - prev_frame[1]) / float(diff_no)
                delta_y = (key[2] - prev_frame[2]) / float(diff_no)
                delta_w = (key[3] - prev_frame[3]) / float(diff_no)
                delta_h = (key[4] - prev_frame[4]) / float(diff_no)

                for i in range(diff_no - 1):
                    no = prev_no + i + 1
                    x = prev_frame[1] + delta_x * (i+1)
                    y = prev_frame[2] + delta_y * (i+1)
                    w = prev_frame[3] + delta_w * (i+1)
                    h = prev_frame[4] + delta_h * (i+1)
                    track_frames.append((no, x, y, w, h))

        track_frames.append(key)
        prev_no = key[0]
        prev_frame = key

    return track_frames

def rectangle_corners(x, y, w, h):
    left = x
    top = y
    right = x + w
    bottom = y + h
    return left, top, right, bottom

def xywh_from_corners(left, top, right, bottom):
    x = left
    y = top
    w = right - left
    h = bottom - top
    return x, y, w, h

def xywh_from_cxcywh(cx, cy, w, h):
    x = cx - int(w/2)
    y = cy - int(h/2)
    return x, y, w, h

def iou(top1, bottom1, left1, right1, top2, bottom2, left2, right2):
    return intersection(top1, bottom1, left1, right1, top2, bottom2, left2, right2) / union(top1, bottom1, left1, right1, top2, bottom2, left2, right2)

def intersection(top1, bottom1, left1, right1, top2, bottom2, left2, right2):
    w = overlap(left1, right1, left2, right2)
    h = overlap(top1, bottom1, top2, bottom2)
    if w < 0:
        return 0
    if h < 0:
        return 0

    area = w * h;
    return area;

def union(top1, bottom1, left1, right1, top2, bottom2, left2, right2):
    i = intersection(top1, bottom1, left1, right1, top2, bottom2, left2, right2)
    u = (bottom1 - top1) * (right1 - left1) + (bottom2 - top2) * (right2 - left2) - i;
    return u;

def overlap(left1, right1, left2, right2):
    left = left1
    right = right1

    if left1 < left2:
        left = left2

    if right1 > right2:
        right = right2

    return right - left;

def smooth_track_frames(track_frames):
    # Averaging Bounding Boxes
    no_list = []
    x_list = []
    y_list = []
    w_list = []
    h_list = []

    for no, x, y, w, h in track_frames:
        no_list.append(no)
        x_list.append(x)
        y_list.append(y)
        w_list.append(w)
        h_list.append(h)

    x_list = moving_average(x_list, N=5)
    y_list = moving_average(y_list, N=5)
    w_list = moving_average(w_list, N=5)
    h_list = moving_average(h_list, N=5)

    return_list = [track_frames[0]]
    for i in range(len(track_frames) - 1):
        if i > 0:
            return_list.append((no_list[i], x_list[i], y_list[i], w_list[i], h_list[i]))
    return_list.append(track_frames[-1])

    return return_list

def moving_average(f, N=5):
    b=np.ones(N)/N
    offset = int(N/2)

    tmp_f = [f[0] for _ in range(N)]
    tmp_f.extend(f)
    tmp_f.extend([f[-1] for _ in range(N)])

    ave = np.convolve(tmp_f, b, mode='same')
    return ave[N:-N]

def save_cropped_cars(images_list, track_frames, output_dir):
    for frame in track_frames:
        img_path = images_list[frame[0] - 1]

        left = int(frame[1])
        top = int(frame[2])
        right = left + int(frame[3])
        bottom = top + int(frame[4])

        output_img_path = os.path.join(output_dir, os.path.basename(img_path))

        img = cv2.imread(img_path)
        cropped_img = img[top:bottom, left:right, :]
        resized_img = cv2.resize(cropped_img, (224, 224))
        cv2.imwrite(output_img_path, resized_img)

def track_cars(input_img_dir, output_img_dir, car_detection_result_path, keyframes_path, ec2_output_dir, s3_output_file, s3_progress_file):
    inference_type = get_inference_type('app_opponent_direction')

    if not os.path.exists(input_img_dir):
        write_status(inference_type, 500, 'Internal error', 'Images could not be read.', 10, ec2_output_dir, s3_progress_file)
        sys.exit()

    if not os.path.exists(output_img_dir):
        os.mkdir(output_img_dir)

    if not os.path.exists(car_detection_result_path):
        write_status(inference_type, 400, 'Invalid request', '"inference_type=1" is not executed yet.', 10, ec2_output_dir, s3_progress_file)
        sys.exit()

    if not os.path.exists(keyframes_path):
        write_status(inference_type, 500, 'Internal error', 'start/end frame information could not be read.', 10, ec2_output_dir, s3_progress_file)
        sys.exit()

    track_frames, key_frames = initialize_frames(keyframes_path)
    yolo_results = load_yolo_results(car_detection_result_path)

    # Preparing ColorHistogram class
    colorHistogram = ColorHistogram()
    frame_image_list = [os.path.join(input_img_dir, img_name) for img_name in sorted(os.listdir(input_img_dir))]

    diff_list_length = key_frames[1][0] - len(frame_image_list) # end_frame_no - num_existing_images
    if diff_list_length > 0:
        frame_image_list_prefix = [frame_image_list[0] for _ in range(diff_list_length)]
        frame_image_list_prefix.extend(frame_image_list)
        frame_image_list = frame_image_list_prefix

    for keyframe in key_frames:
        colorHistogram.add_keyframe(keyframe, frame_image_list[keyframe[0] - 1])

    # Tracking cars with linear prediction
    key_frames_length = len(key_frames)
    for i in range(len(track_frames)):
        for frame in track_frames:
            # Skip if keyframe
            if frame in key_frames:
                continue

            no, x, y, w, h = frame[0], frame[1], frame[2], frame[3], frame[4]
            left, top, right, bottom = rectangle_corners(x, y, w, h)

            predicted_boxes = [rectangle_corners(_x, _y, _w, _h) for _x, _y, _w, _h in yolo_results[no - 1]]

            # Update key frames with IoU
            for predicted_box in predicted_boxes:
                predicted_left, predicted_top, predicted_right, predicted_bottom = predicted_box

                iou_value = iou(predicted_top, predicted_bottom, predicted_left, predicted_right, top, bottom, left, right)

                if iou_value > 0.3 and iou_value <= 0.99: # default: 0.5 < IoU <= 0.99
                    if no != 1 and no != len(track_frames):
                        predicted_x, predicted_y, predicted_w, predicted_h = xywh_from_corners(predicted_left, predicted_top, predicted_right, predicted_bottom)
                        keyframe_candidate = (no, predicted_x, predicted_y, predicted_w, predicted_h)

                        if colorHistogram.check_histogram_for_frame(keyframe_candidate, frame_image_list[no - 1]):
                            colorHistogram.add_keyframe(keyframe_candidate, frame_image_list[no - 1])
                            key_frames.append(keyframe_candidate)
                            break

        if len(key_frames) == key_frames_length:
            break

        # Progress report
        progress = 0.1 + 0.6*(float(i + 1)/float(len(track_frames)))
        if progress>0.69:
            progress = 0.69
        write_status(inference_type, 200, "","", int(progress*100), ec2_output_dir, s3_progress_file)

    track_frames = smooth_track_frames(track_frames)

    save_cropped_cars(frame_image_list, track_frames, output_img_dir)
    write_status(inference_type, 200, '', '', 70, ec2_output_dir, s3_progress_file)

    return float(len(key_frames))/float(len(track_frames))
