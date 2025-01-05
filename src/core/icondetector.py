import os.path
import time
import cv2
import torch
from src.models.vggNet import VGG
from src.core.segmenter import Segmenter
from src.core.metrics import Metrics
from PIL import Image
import numpy as np
from tqdm import tqdm
from src.utils.util import draw_bbox, draw_text,get_uni_name

class IconDetector():
    def __init__(self, device = 'cpu', weight_path = './weights', metric_model = 'vgg19', save_dir = './results', target_height = 224, target_width = 224):
        self.device = device
        self.metric_model = VGG(device, modelName=metric_model)
        self.seg_model = Segmenter(weight_path, save_dir= save_dir)
        self.metrics = Metrics(device)
        self.target_height = target_height
        self.target_width = target_width
        self.save_dir = save_dir


    def det(self, source_img, icon_img, batch_size = 8):
        start_time = time.time()
        input_img = np.array(Image.open(source_img))
        seg_res = self.seg_model.run(source_img, self.device)
        scores = []
        max_score = 0
        res_bbox = None
        temp_list = []
        temp_bbox_list = []
        for i, (img, bbox) in tqdm(enumerate(seg_res)):
            img1_t = self.load_img(img)
            temp_list.append(img1_t)
            temp_bbox_list.append(bbox)
            if len(temp_list) % batch_size != 0 and i < len(seg_res) - 1:
                continue

            img2_t = self.load_img(icon_img)
            pred1  = self.metric_model.forward(torch.concat(temp_list, dim=0))
            pred2 = self.metric_model.forward(img2_t)
            score_list_tmp = self.metrics.cos_metric(pred1, pred2)
            for j, score in enumerate(score_list_tmp):
                score = str(format(score.cpu().numpy(), '.2f'))
                print("\n score is " , score)
                scores.append(score)
                if float(score) > max_score:
                    input_img = draw_text(draw_bbox(input_img, bbox), bbox, score)
                    res_bbox = temp_bbox_list[j]
                    max_score = float(score)

            temp_list.clear()
            temp_bbox_list.clear()

        print(f"Task finish in {time.time() - start_time} s")
        print("max score is: " + max(scores))
        print("min score is: " + min(scores))
        input_img = draw_text(draw_bbox(input_img, res_bbox, color=(255, 0, 0)), res_bbox, str(max_score), text_color=(255, 0, 0))
        Image.fromarray(input_img).save(os.path.join(self.save_dir, get_uni_name() + "_pred_result.png"))

        return res_bbox



    def img_preprocess(self, img):
        if isinstance(img, str):
            img_pil = Image.open(img).convert('L')
        elif isinstance(img, np.ndarray):
            img_pil = Image.fromarray(img).convert('L')
        else:
            img_pil = img.convert('L')

        w,h = img_pil.size
        if (h != self.target_height or w != self.target_width):
            img_pil = img_pil.resize((self.target_width, self.target_height))
            img_pil = Image.fromarray(cv2.medianBlur(np.array(img_pil), 5))
            img_pil.save(os.path.join(self.save_dir, get_uni_name() + "_gray.png"))

        return img_pil


    def load_img(self, path, preprocess = True):
        if preprocess:
            img_pil = self.img_preprocess(path)
        else:
            img_pil = Image.open(path).convert('L')

        img_np = np.array(img_pil)
        img_np = np.expand_dims(img_np, axis=-1)
        img_t = self.cv2tensor(img_np, True)
        return img_t


    def cv2tensor(self, img, normalize = False):
        img_t = torch.from_numpy(img.transpose(2,0,1)).float().div(255.)
        img_t = torch.concat([img_t, img_t, img_t], dim = 0)
        img_t = torch.unsqueeze(img_t, dim = 0)
        if normalize:
            img_t = img_t * 2 - 1
        return img_t.to(self.device)