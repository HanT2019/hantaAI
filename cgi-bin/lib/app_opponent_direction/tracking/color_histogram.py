import cv2
import numpy as np

THRESHOLD = 0.3

class ColorHistogram:
    def __init__(self):
        self.keyframe_histograms = {}

    def add_keyframe(self, keyframe, image_path):
        if not int(keyframe[0]) in self.keyframe_histograms.keys():
            self.keyframe_histograms[int(keyframe[0])] = calc_histograms(keyframe, image_path)

    def check_histogram_for_frame(self, frame, image_path):
        if len(self.keyframe_histograms) == 0:
            return False

        histograms = calc_histograms(frame, image_path)
        nearest_histograms = get_nearest_frame_histograms(self.keyframe_histograms, int(frame[0]))

        blue_distance  = cv2.compareHist(histograms['B'], nearest_histograms['B'], cv2.HISTCMP_BHATTACHARYYA)
        green_distance = cv2.compareHist(histograms['G'], nearest_histograms['G'], cv2.HISTCMP_BHATTACHARYYA)
        red_distance   = cv2.compareHist(histograms['R'], nearest_histograms['R'], cv2.HISTCMP_BHATTACHARYYA)
        average_distance = (blue_distance + green_distance + red_distance) / 3

        if average_distance < THRESHOLD:
            return True

        return False

def calc_histograms(frame, image_path):
    _, x, y, w, h = frame

    img = cv2.imread(image_path)
    mask = np.zeros(img.shape[:2], np.uint8)
    mask[y:y+h, x:x+w] = 255

    blue_hist  = cv2.calcHist([img], [0], mask, [256], [0,256])
    green_hist = cv2.calcHist([img], [1], mask, [256], [0,256])
    red_hist   = cv2.calcHist([img], [2], mask, [256], [0,256])

    return {'B': blue_hist, 'G': green_hist, 'R': red_hist}

def get_nearest_frame_histograms(source_dict, frame_no):
    registered_frames = list(source_dict.keys())
    idx = np.abs(np.array(registered_frames) - frame_no).argmin()
    target_frame_no = registered_frames[idx]
    return source_dict[target_frame_no]
