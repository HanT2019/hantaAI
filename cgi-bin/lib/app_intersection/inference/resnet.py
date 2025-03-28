import torch.nn as nn
import torchvision.models as models

class ResNet(nn.Module):
    def __init__(self, num_layers=18, num_classes=10, pretrained=True):
        super().__init__()

        if num_layers == 18:
            self.resnet = models.resnet18(pretrained=pretrained)
        elif num_layers == 34:
            self.resnet = models.resnet34(pretrained=pretrained)
        elif num_layers == 50:
            self.resnet = models.resnet50(pretrained=pretrained)
        elif num_layers == 101:
            self.resnet = models.resnet101(pretrained=pretrained)
        elif num_layers == 152:
            self.resnet = models.resnet152(pretrained=pretrained)
        else:
            # print('ResNet: num_layers should be the one of [18, 34, 50, 101, 152]')
            exit(1)

        self.resnet.fc = nn.Linear(self.resnet.fc.in_features, num_classes)
        self.softmax = nn.Softmax(dim=1)

    def forward(self, x):
        x = self.resnet(x)
        x = self.softmax(x)
        return x
