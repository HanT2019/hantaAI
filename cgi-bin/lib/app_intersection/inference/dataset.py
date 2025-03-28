import os
import torch.utils as utils
from PIL import Image

class InferenceDataset(utils.data.Dataset):
    def __init__(self, images_dir='', start_no=0, end_no=0, transform=None):
        self.images_dir = images_dir
        self.start_no = start_no
        self.end_no = end_no
        self.transform = transform

        self.img_list = []
        for no in range(start_no, end_no + 1):
            self.img_list.append(
                (
                    os.path.join(images_dir, '{:0=4}.jpg'.format(no)),
                    no
                )
            )

    def __len__(self):
        return len(self.img_list)

    def __getitem__(self, idx):
        image_file, no = self.img_list[idx]

        image = Image.open(image_file)
        if self.transform:
            image = self.transform(image)

        return image, no
