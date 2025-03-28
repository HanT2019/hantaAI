import sys
import traceback
sys.path.append('/var/www/cgi-bin/lib')
from file_output import write_status, write_result
from inference_manager import get_inference_type
from reshape_return_dict import Method, reshape
from inference.predict import predict_for_frames
from mylogger import getLogger

logger = getLogger(__name__)

def main(accident_id, images_dir, start_no, end_no, ec2_output_dir, s3_output_file, s3_progress_file):
    return_dict = {}
    result_data = {'id': accident_id, 'frames': []}
    result_data['frames'] = predict_for_frames(images_dir, start_no, end_no, ec2_output_dir, s3_output_file, s3_progress_file)

    return_dict['result'] = result_data
    return_dict = reshape(return_dict, method=Method.ONE_SEC_MODE)

    inference_type = get_inference_type('app_intersection')
    write_result(inference_type, return_dict, ec2_output_dir, s3_output_file)
    write_status(inference_type, 200, '', '', 100, ec2_output_dir, s3_progress_file)

if __name__ == '__main__':
    try:
        args = sys.argv
        main(args[1], args[2], int(args[3]), int(args[4]), args[5], args[6], args[7])
    except:
        logger.critical(traceback.print_exc())
