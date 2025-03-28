import sys
import os
import traceback
sys.path.append('/var/www/cgi-bin/lib')
from file_output import write_status, write_result
from inference_manager import get_inference_type
from tracking.tracking import track_cars
from opponent_car.predict import predict_for_frames
from auxiliary_start_code_detector.detect import detect
from mylogger import getLogger

logger = getLogger(__file__)
inference_type = get_inference_type('app_opponent_direction')

def main(accident_id, images_dir, start_no, end_no, ec2_output_dir, s3_output_file, s3_progress_file):
    return_dict = {}
    result_data = {'id': accident_id}
    judgement_data = {'opponent_start_code': '00', 'opponent_direction_code': '00'}

    car_detection_inference_type = get_inference_type('app_car_detection')
    car_detection_result_path = os.path.join(ec2_output_dir, f'{car_detection_inference_type}_result.json')
    if not os.path.exists(car_detection_result_path):
        write_status(inference_type, 400, 'Invalid request', '"inference_type=1" is not executed yet.', 10, ec2_output_dir, s3_progress_file)
        sys.exit()

    keyframes_path = os.path.join(ec2_output_dir, 'keyframes.txt')
    if not os.path.exists(keyframes_path):
        write_status(inference_type, 500, 'Internal error', 'start/end frame information could not be read.', 10, ec2_output_dir, s3_progress_file)
        sys.exit()

    # tracking
    cropped_images_dir = os.path.join(ec2_output_dir, 'cropped_cars')
    confidence_level = track_cars(
        images_dir,
        cropped_images_dir,
        car_detection_result_path,
        keyframes_path,
        ec2_output_dir,
        s3_output_file,
        s3_progress_file
    )

    if confidence_level > 0.5:
        # predicting opponent car direction
        position, direction = predict_for_frames(cropped_images_dir, ec2_output_dir, s3_output_file, s3_progress_file)
        position, direction = detect(images_dir, keyframes_path, position, direction)
        judgement_data['opponent_start_code'] = position
        judgement_data['opponent_direction_code'] = direction

    result_data['judgements'] = judgement_data
    return_dict['result'] = result_data

    write_result(inference_type, return_dict, ec2_output_dir, s3_output_file)
    write_status(inference_type, 200, '', '', 100, ec2_output_dir, s3_progress_file)

if __name__ == '__main__':
    try:
        args = sys.argv
        main(args[1], args[2], int(args[3]), int(args[4]), args[5], args[6], args[7])
    except:
        write_status(inference_type, 500, 'Internal error', 'Internal error', 100, args[5], args[7])
