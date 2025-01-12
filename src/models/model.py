import torch
from .wavemlp import WaveMLP_S, WaveMLP_M, OrderedDict
from .vggNet import VGG


def load_pretrained_model(weight_path, modelName = "WaveMLP_S", device = "cpu"):
    if modelName == "WaveMLP_S":
        model = WaveMLP_S()
    elif modelName == "WaveMLP_M":
        model = WaveMLP_M()
    elif modelName == "VGG":
        model = VGG()
    else:
        raise Exception("No Matching Model Error")
    state_dict = model.state_dict()
    weight_dict = torch.load(weight_path, map_location=device)
    new_state_dict = OrderedDict()
    for k, v in weight_dict.items():
        if k in state_dict.keys():
            new_state_dict[k] = v

    model.load_state_dict(new_state_dict)
    model.eval().to(device)

    return model