import os.path
import time
import cv2
import torch
from src.core.segmenter import Segmenter
from src.core.metrics import Metrics
from src.models.model import load_pretrained_model
from PIL import Image
import numpy as np
from tqdm import tqdm
from src.utils.util import draw_bbox, draw_text,get_uni_name,load_image, is_same_img

class IconDetector():
    def __init__(self, device = 'cpu', segment_weight_path = "./weights", metric_weight_path = './weights', metric_model = 'vgg19', save_dir = './results', target_height = 224, target_width = 224, batch_size = 32, topK = 1):
        self.device = device
        self.save_dir = os.path.join(save_dir, get_uni_name())
        os.makedirs(self.save_dir, exist_ok=True)
        self.metric_model = load_pretrained_model(weight_path=metric_weight_path, modelName=metric_model, device=device)
        self.seg_model = Segmenter(weight_path=segment_weight_path, save_dir=  self.save_dir)
        self.metrics = Metrics(device)
        self.target_height = target_height
        self.target_width = target_width
        self.batch_size = batch_size
        self.topK = topK
        self.cache_source_img = ""
        self.det_res = None

    def should_use_cache(self, img):
        if img == self.cache_source_img:
            if self.cache_source_img != "":
                return is_same_img(self.cache_source_img, img)
            else:
                return True
        else:
            return False

    @torch.no_grad()
    def det(self, source_img, icon_img):
        if not self.should_use_cache(source_img):
            self.cache_source_img = source_img
            batch_size = self.batch_size
            topK = self.topK
            start_time = time.time()
            input_img = np.array(load_image(source_img))
            seg_res = self.seg_model.run(source_img, self.device)
            scores = []
            temp_list = []
            temp_bbox_list = []
            det_res = []
            img2_t = self.load_img(icon_img)
            pred2 = self.metric_model.forward(img2_t)
            for i, (img, bbox) in tqdm(enumerate(seg_res)):
                img1_t = self.load_img(img)
                temp_list.append(img1_t)
                temp_bbox_list.append(bbox)
                if len(temp_list) % batch_size != 0 and i < len(seg_res) - 1:
                    continue

                pred1  = self.metric_model.forward(torch.concat(temp_list, dim=0))
                score_list_tmp = self.metrics.cos_metric(pred1, pred2)
                for j, score in enumerate(score_list_tmp):
                    score = str(format(score.cpu().numpy(), '.2f'))
                    # print("\n score is " , float(score))
                    scores.append(score)
                    det_res.append((score, temp_bbox_list[j]))

                temp_list.clear()
                temp_bbox_list.clear()

            print(f"Task finish in {time.time() - start_time} s")
            # print("max score is: " + max(scores))
            # print("min score is: " + min(scores))
            det_res = sorted(det_res, key=lambda x: x[0], reverse=True)
            top_k = det_res[:topK]
            for i, (score, bbox) in enumerate(top_k):
                if i == 0:
                    color = (255, 0, 0)
                else:
                    color = (0, 0, 255)

                input_img = draw_text(draw_bbox(input_img, bbox, color=color), bbox, str(score), text_color=color)


            print("det_res: " , det_res)
            Image.fromarray(input_img).save(os.path.join(self.save_dir, get_uni_name() + "_pred_result.png"))

            if len(det_res) > 0 and len(det_res) >= topK:
                self.det_res =  det_res[:topK]
            else:
                self.det_res =  det_res

        else:
            print("Use cache icon detect result")

        return self.det_res


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
            # img_pil = Image.fromarray(cv2.medianBlur(np.array(img_pil), 5))
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