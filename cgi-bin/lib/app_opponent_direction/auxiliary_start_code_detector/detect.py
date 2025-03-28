import os
import cv2
import json

CLASSES = [
    {'name': 'center_left', 'position': '06', 'direction': '02'},
    {'name': 'center_right', 'position': '06', 'direction': '01'},
    {'name': 'center_straight', 'position': '06', 'direction': '05'},
    {'name': 'left_left', 'position': '03', 'direction': '02'},
    {'name': 'left_right', 'position': '03', 'direction': '01'},
    {'name': 'left_straight', 'position': '03', 'direction': '05'},
    {'name': 'right_left', 'position': '01', 'direction': '02'},
    {'name': 'right_right', 'position': '01', 'direction': '01'},
    {'name': 'right_straight', 'position': '01', 'direction': '05'},
    {'name': 'rear_end', 'position': '05', 'direction': '05'},
]

def get_image_width(images_dir):
    frame_image_list = [os.path.join(images_dir, img_name) for img_name in sorted(os.listdir(images_dir))]

    if len(frame_image_list) > 0:
        img = cv2.imread(frame_image_list[0])
        height, width, _ = img.shape
        return width

    return 1280

def load_keyframes(keyframes_path):
    keyframes = []

    with open(keyframes_path, 'r') as keyframes_txt:
        for keyframe in keyframes_txt:
            no, cx, cy, w, h = tuple([int(v) for v in keyframe.strip().split(' ')])
            keyframes.append((no, cx, cy, w, h))

    return keyframes

def detect(images_dir, keyframes_path, position, direction):
    classes_list = list(
        filter(
            lambda class_item: class_item['position']==position and class_item['direction']==direction, CLASSES
        )
    )

    if len(classes_list) == 0:
        return position, direction

    if 'left_' in classes_list[0]['name'] or 'right_' in classes_list[0]['name']:
        keyframes = load_keyframes(keyframes_path)
        _, cx, cy, w, h = keyframes[0]
        width = get_image_width(images_dir)

        if cx < int(width/2):
            return '03', direction
        else:
            return '01', direction

    return position, direction
