import sys
import numpy as np
import cv2 as cv
import json
import traceback

sys.path.append('/var/www/cgi-bin/lib')
from file_output import write_status, write_result
from inference_manager import get_inference_type
from reshape_return_dict import Method, reshape
from mylogger import getLogger

logger = getLogger(__name__)
inference_type = get_inference_type('app_self_direction')

def main(accident_id, images_dir, start_no, end_no, ec2_output_dir, s3_output_file, s3_progress_file):
    return_dict = {}
    result_data = {'id': accident_id, 'frames': []}

    def xywh2xyxy(data, W, H):
        x, y, w, h = data
        x0 = x - w / 2
        y0 = y - h / 2
        x1 = x + w / 2
        y1 = y + h / 2
        return [x0, y0, x1, y1]

    def loadmask(path):
        ret=[[] for _ in range(start_no, end_no + 1)]

        with open(path) as f:
            data=json.load(f)

        for idx_f ,data in enumerate(data['result']['frames']):
            if idx_f in range(start_no, end_no + 1):
                for d in data['cars']:
                    ret[idx_f - start_no].append(xywh2xyxy((d['bbox']['x'],d['bbox']['y'],d['bbox']['w'],d['bbox']['h']),W,H))

        return ret

    def opticalflow(img1, img2, mask1, mask2, mask=True):
        def mask_in(p, mask):
            x, y = p
            mx0, my0, mx1, my1 = mask
            return (mx0 < x < mx1) and (my0 < y < my1)

        def norm(p0, p1):
            return np.sqrt((((p0 - p1) ** 2).sum()))

        thresh = 0
        # params for ShiTomasi corner detection
        feature_params = dict(maxCorners=1000,
                              qualityLevel=0.2,
                              minDistance=3,
                              blockSize=7)
        # Parameters for lucas kanade optical flow
        lk_params = dict(winSize=(5, 5),
                         maxLevel=5,
                         criteria=(cv.TERM_CRITERIA_EPS | cv.TERM_CRITERIA_COUNT, 10, 0.03))
        old_frame = img1[50:, :, :]
        old_gray = cv.cvtColor(old_frame, cv.COLOR_BGR2GRAY)
        p0 = cv.goodFeaturesToTrack(old_gray, mask=None, **feature_params)
        # Create a mask image for drawing purposes
        frame = img2[50:, :, :]
        frame_gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)
        # calculate optical flow
        p1, st, err = cv.calcOpticalFlowPyrLK(old_gray, frame_gray, p0, None, **lk_params)
        # Select good points
        good_old = p0[st == 1]
        good_new = p1[st == 1]
        if mask:
            # print("mask",mask1,mask2)
            ret_old = []
            ret_new = []
            if mask1 != [] and mask2 != []:
                for old, new in zip(good_old, good_new):
                    for m1, m2 in zip(mask1, mask2):
                        if not mask_in(old.ravel(), m1) and not mask_in(new.ravel(), m2):
                            if norm(p0, p1) > thresh:
                                ret_old += [old]
                                ret_new += [new]
                return ret_old, ret_new
            else:
                return good_old, good_new

    def opticalflow_mc(item, ret_arr, masks, W):
        def angle(p0, p1):
            return np.arctan2((p1[1] - p0[1]), (p1[0] - p0[0]))

        img1, img2, i = item
        mask1 = masks[i]
        mask2 = masks[i + 1]
        p0, p1 = opticalflow(img1, img2, mask1, mask2)
        theta = [angle(*p) for p in zip(p0, p1)]
        pos = [int(p[0] // (W / 3)) for p in p0]
        mi = -np.pi
        ma = np.pi
        bin = 8
        ret = np.zeros((3, bin))
        for t, p in zip(theta, pos):
            if -np.pi < t < np.pi:
                ret[p, int((t - mi) / (ma - mi) * bin)] += 1
        flag = (ret.sum(axis=-1) != 0)
        ret = np.argmax(ret, axis=-1)

        ret_arr[i, 0] = (flag & (ret == 0) | (ret == 7)).all()
        ret_arr[i, 1] = ((ret == 3) | (ret == 4)).all()
        #print(i, (flag & (ret == 0) | (ret == 7)).all(), ((ret == 3) | (ret == 4)).all())

    conv = 5
    conv2 = 15
    addlast = 10
    imgps = [f'{images_dir}/{i:04d}.jpg' for i in range(start_no, end_no)]
    #masks = [loadtxt(imgp.replace('jpg', 'txt')) for imgp in imgps]
    ret_arr = np.zeros((end_no - start_no + 1, 2)) + 2

    preimg = cv.imread(imgps[0])
    H, W, C = preimg.shape

    masks=loadmask(f'{ec2_output_dir}/1_result.json')
    for idx, imgp in enumerate(imgps[1:]):
        img = cv.imread(imgp)
        opticalflow_mc((preimg, img, idx), ret_arr, masks, W)
        preimg = img

    #print('all process finish')
    ret_arr = np.array(
        [np.convolve(ret_arr[:, i], np.ones(conv) / conv, mode='same') > 0.8 for i in range(2)]).transpose()
    ret_arr = np.array(
        [np.convolve(ret_arr[:, i], np.ones(conv2) / conv2, mode='same') > 0.99 for i in range(2)]).transpose()
    ret_arr = np.array(
        [np.convolve(ret_arr[:, i], np.ones(conv2) / conv2, mode='same') > 0.05 for i in range(2)]).transpose()
    roll_arr = np.roll(ret_arr, addlast, axis=0)
    roll_arr[:, addlast:] = 0
    ret_arr = ret_arr | roll_arr

    # ret_arr = np.concatenate([np.arange(len(ret_arr)).reshape(-1, 1), ret_arr], axis=-1)

    # return f_dick
    ret_id_mapping=[['05','02'],['01']]
    for idx,(r,l) in enumerate(ret_arr,start_no):
        result_data['frames'].append({'no':idx,'self_direction_code':ret_id_mapping[r][l]})

    return_dict['result'] = result_data
    return_dict = reshape(return_dict, method=Method.CENTRAL)

    write_result(inference_type, return_dict, ec2_output_dir, s3_output_file)
    write_status(inference_type, 200, '', '', 100, ec2_output_dir, s3_progress_file)

if __name__ == '__main__':
    try:
        args = sys.argv
        main(args[1], args[2], int(args[3]), int(args[4]), args[5], args[6], args[7])
    except:
        logger.critical(traceback.print_exc())
        write_status(inference_type, 500, 'Internal error', 'Internal error', 100, args[5], args[7])
