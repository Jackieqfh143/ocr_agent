import os
from src.core.icondetector import IconDetector
from src.utils.util import get_uni_name

if __name__ == '__main__':
    save_dir = './results/' + get_uni_name()
    weight_path = './weights/FastSAM-s.pt'
    os.makedirs(save_dir, exist_ok=True)

    source_img = './imgs/demo.jpg'
    icon_img = './imgs/icon.png'

    detector = IconDetector(device='cpu', weight_path=weight_path, metric_model='vgg19'
                            ,save_dir=save_dir, target_height= 224, target_width=224)

    detector.det(source_img, icon_img)


