import lpips
import torch
import torch.nn as nn

class Metrics():
    def __init__(self, device):
        self.cos_metric = nn.CosineSimilarity(dim=1, eps=1e-8)
        self.lpips_model = None
        self.device = device


    def metric_l1_loss(self, f1, f2):
        return torch.mean(torch.abs(f1 - f2))

    def metric_lpips_loss(self, f1, f2):
        if self.lpips_model == None:
            self.lpips_model = lpips.LPIPS(pretrained=True, net='alex')
            self.lpips_model.to(self.device)
        return self.lpips_model.forward(f1, f2, normalize=True)

    def metric_cos_similarity(self, f1, f2):
        return self.cos_metric(f1, f2)


