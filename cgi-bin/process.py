import os
import sys
import subprocess
from lib.inference_manager import get_inference_name

from lib.mylogger import getLogger
logger = getLogger(__file__)

def check_inference(infer_type):
    if infer_type < 1 or 7 < infer_type:
        return 0
    else:
        return 1

def main(inference_type, accident_id, start_no, end_no, accident_dir_path, s3_output_file, s3_progress_file, additional_args):
    infer_dir = "/var/www/cgi-bin/lib/"
    images_dir = os.path.join(accident_dir_path, 'images')

    inference_name = get_inference_name(inference_type)

    if len(inference_name) > 0:
        src_dir = inference_name
        src_name = "/" + inference_name + ".py"

        pyenv_path = os.environ.get('PYENV_ROOT')

        import datetime
        start_time = datetime.datetime.now()
        logger.info(f'{inference_name} had been started at {start_time}.')

        subprocess.call([pyenv_path + "python3", infer_dir + src_dir + src_name, accident_id, images_dir, str(start_no), str(end_no), accident_dir_path, s3_output_file, s3_progress_file, additional_args])

        finish_time = datetime.datetime.now()
        logger.info(f'{inference_name} had been finished at {finish_time}, spent {finish_time - start_time}.')

        sys.exit()

if __name__ == '__main__':
    args = sys.argv
    logger.info(f'Subprocess Args: {args}, At: {__file__}')
    main(int(args[1]), args[2], int(args[3]), int(args[4]), args[5], args[6], args[7], args[8])
