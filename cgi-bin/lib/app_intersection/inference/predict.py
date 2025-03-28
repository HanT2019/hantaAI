import sys
sys.path.append('/var/www/cgi-bin/lib')
import os
import torch
import torchvision.transforms as transforms

from file_output import write_status
from inference_manager import get_inference_type
from .dataset import InferenceDataset
from .resnet import ResNet

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
CLASSES = [
    {'name': '+', 'id': '03'},
    {'name': '-|', 'id': '06'},
    {'name': 'T', 'id': '05'},
    {'name': '|-', 'id': '07'},
    {'name': 'others', 'id': '00'},
    {'name': '|', 'id': '04'},
]

def predict_for_frames(images_dir, start_no, end_no, ec2_output_dir, s3_output_file, s3_progress_file):
    result_list = []

    transform = getTransforms()
    dataset = InferenceDataset(
        images_dir = images_dir,
        start_no = start_no,
        end_no = end_no,
        transform = transform
    )
    dataloader = torch.utils.data.DataLoader(
        dataset,
        batch_size = 1,
        shuffle = False,
        num_workers = 0
    )

    model = ResNet(
        num_layers = 18,
        num_classes = len(CLASSES),
        pretrained = False
    ).to(DEVICE)
    checkpoint = torch.load('/var/www/cgi-bin/lib/app_intersection/inference/model_data/app_intersection.pth')
    if 'state_dict' in checkpoint.keys():
        checkpoint = checkpoint['state_dict']
    model.load_state_dict(
        checkpoint,
        strict = False
    )
    model.eval()

    file_sum = len(dataloader)
    file_counter = 0
    inference_type = get_inference_type('app_intersection')

    with torch.no_grad():
        for image, no in dataloader:
            file_counter += 1

            output = model(image.to(DEVICE))
            _, predicted = torch.max(output.data, 1)
            predicted = predicted.to('cpu')[0].item()

            frame_dict = {}
            frame_dict['no'] = int(no)
            frame_dict['intersection_type_code'] = CLASSES[int(predicted)]['id']
            result_list.append(frame_dict)

            # Progress report
            progress = 0.1 + 0.9*(float(file_counter)/float(file_sum))
            if progress>0.99:
                progress = 0.99
            write_status(inference_type, 200, "","", int(progress*100), ec2_output_dir, s3_progress_file)

    return result_list

def getTransforms():
    return transforms.Compose(
        [
            # transforms.Resize((720, 1280)),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        ]
    )
