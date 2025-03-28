import torch.nn as nn
import torchvision.models as models

class ImageLSTM(nn.Module):
    def __init__(self, hidden_size, n_layers, dropt, N_classes):
        super().__init__()

        self.hidden_size=hidden_size
        self.num_layers=n_layers

        dim_feats = 4096

        self.cnn=models.alexnet(pretrained=False)
        self.cnn.classifier[-1]=Identity()

        self.rnn = nn.LSTM(
            input_size=dim_feats,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=dropt,
            bidirectional=False)

        self.n_cl=N_classes
        self.last_linear = nn.Sequential(
            nn.Linear(self.hidden_size, self.n_cl),
            nn.Softmax(dim=1)
        )

    def forward(self, x):
        batch_size, timesteps, C, H, W = x.size()

        c_in = x.view(batch_size * timesteps, C, H, W)
        c_out = self.cnn(c_in)

        r_in = c_out.view(-1, batch_size, c_out.shape[-1],)
        r_out, (h_n, h_c) = self.rnn(r_in, None)

        logits = self.last_linear(r_out[-1])

        return logits

class Identity(nn.Module):
    def __init__(self):
        super(Identity, self).__init__()

    def forward(self, x):
        return x
