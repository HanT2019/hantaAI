import sys
sys.path.append('/var/www/cgi-bin/lib')
import os
import torch
import torchvision.transforms as transforms

from file_output import write_status
from inference_manager import get_inference_type
from .dataset import InferenceSeqDataset
from .image_lstm import ImageLSTM

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
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

def predict_for_frames(images_dir, ec2_output_dir, s3_output_file, s3_progress_file):
    result_list = []

    transform = getTransforms()
    dataset = InferenceSeqDataset(
        images_dir = images_dir,
        transform = transform
    )
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size = 1,
        shuffle = False,
        num_workers = 0
    )

    model = ImageLSTM(512, 2, 0, len(CLASSES)).to(DEVICE)
    checkpoint = torch.load('/var/www/cgi-bin/lib/app_opponent_direction/opponent_car/model_data/app_opponent_direction.pth')
    if 'state_dict' in checkpoint.keys():
        checkpoint = checkpoint['state_dict']
    model.load_state_dict(
        checkpoint,
        strict = False
    )
    model.eval()

    file_sum = len(dataloader)
    file_counter = 0
    inference_type = get_inference_type('app_opponent_direction')
    position = '00'
    direction = '00'

    with torch.no_grad():
        for data in dataloader:
            file_counter += 1

            output = model(data.to(DEVICE))
            _, predicted = torch.max(output.data, 1)
            predicted = predicted.to('cpu')[0].item()

            position = CLASSES[int(predicted)]['position']
            direction = CLASSES[int(predicted)]['direction']

            # Progress report
            progress = 0.7 + 0.3*(float(file_counter)/float(file_sum))
            if progress>0.99:
                progress = 0.99
            write_status(inference_type, 200, "","", int(progress*100), ec2_output_dir, s3_progress_file)

    return position, direction

def getTransforms():
    return transforms.Compose(
        [
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ]
    )
