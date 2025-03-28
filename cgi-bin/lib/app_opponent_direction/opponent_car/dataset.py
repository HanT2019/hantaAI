import os
import torch
import torch.utils as utils
from PIL import Image

class InferenceSeqDataset(utils.data.Dataset):
    def __init__(self, images_dir='', transform=None):
        self.transform = transform
        self.img_list = [images_dir]

    def __len__(self):
        return len(self.img_list)

    def __getitem__(self, idx):
        images_dir = self.img_list[idx]

        images = []
        for image_path in sorted(os.listdir(images_dir)):
            image = Image.open(os.path.join(images_dir, image_path))

            if self.transform:
                image = self.transform(image)

            images.append(image)

        images = torch.stack(images)

        return images
