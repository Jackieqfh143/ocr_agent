from libs.fastsam import FastSAM, FastSAMPrompt
from src.utils.util import get_uni_name
import numpy as np
from PIL import Image
import os
import cv2
from tqdm import tqdm

class Segmenter():
    def __init__(self, weight_path = './weights/FastSAM-s.pt', save_dir = './results'):
        self.model = FastSAM(weight_path)
        self.save_dir = save_dir

    def run(self, img_path, device = 'cpu'):
        img = np.array(Image.open(img_path))
        everything_results = self.model(img_path, device=device, retina_masks=True, imgsz=1024, conf=0.4, iou=0.9, )
        prompt_process = FastSAMPrompt(img_path, everything_results, device=device)
        res = prompt_process._format_results(everything_results[0])
        seg_res = self.extract_all_seg_imgs(res, img, self.save_dir)
        return seg_res

    def anti_aliasing(self, mask):
        kernel = np.ones((5, 5), np.uint8)
        eroded_image = cv2.erode(mask, kernel, iterations=5)
        # dilated_image = cv2.dilate(eroded_image, kernel, iterations=1)
        return eroded_image

    def connect_edge(self, mask):
        # 创建结构元素
        kernel = np.ones((5, 5), np.uint8)
        # 闭运算
        closing = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # opening = cv2.morphologyEx(closing, cv2.MORPH_OPEN, kernel)
        return closing

    def contour_refine(self, img):
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # 使用大津法进行二值化
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        edges = cv2.Canny(binary, 100, 200)

        contours, hierarchy = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        contours = list(c.astype(np.int32) for c in contours)

        mask = np.zeros_like(img)

        cv2.drawContours(mask, contours, -1, (255, 255, 255), thickness=cv2.FILLED)

        mask = self.connect_edge(mask)

        mask = self.anti_aliasing(mask)

        # cv2.fillPoly(mask, pts=contours, color=(255, 255, 255))

        # mask = anti_aliasing(mask)

        result = cv2.bitwise_and(img, mask)

        return result

    def extract_all_seg_imgs(self, masks_list, source_img, save_dir):
        seg_imgs = []

        img_copy = source_img.copy()
        for item in tqdm(masks_list):
            bbox = item.get("bbox").cpu().numpy()[:4]
            bbox = bbox.astype(np.int32)
            seg_map = item.get('segmentation')
            seg_mask = seg_map.astype(np.uint8)
            seg_mask = np.expand_dims(seg_mask, axis=-1)
            seg_img = cv2.bitwise_and(source_img, source_img, mask=seg_mask)
            contours, _ = cv2.findContours(seg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(largest_contour)
                seg_img = seg_img[y:y + h, x:x + w]
                seg_mask = seg_mask[y:y + h, x:x + w]
            b, g, r = cv2.split(seg_img)
            alpha_channel = np.ones(b.shape, dtype=b.dtype) * 255
            alpha_channel = np.expand_dims(alpha_channel, axis=-1)
            alpha_channel[seg_mask == 0] = 0
            rgba_image = cv2.merge((b, g, r, alpha_channel))
            Image.fromarray(rgba_image).save(os.path.join(save_dir, get_uni_name() + ".png"))
            seg_imgs.append((seg_img, bbox))
            cv2.rectangle(img_copy, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
            print()

        return seg_imgs

if __name__ == '__main__':
    save_dir = "./seg_results"
    os.makedirs(save_dir, exist_ok=True)
    model = FastSAM('./weights/FastSAM-s.pt')
    IMAGE_PATH = './imgs/demo.jpg'
    img = np.array(Image.open(IMAGE_PATH))
    DEVICE = 'cpu'
    everything_results = model(IMAGE_PATH, device=DEVICE, retina_masks=True, imgsz=1024, conf=0.4, iou=0.9, )
    prompt_process = FastSAMPrompt(IMAGE_PATH, everything_results, device=DEVICE)

    # everything prompt
    ann = prompt_process.everything_prompt()

    res = prompt_process._format_results(everything_results[0])

    extract_all_seg_imgs(res, img, save_dir)

    prompt_process.plot(annotations=ann, output_path='./output/demo.jpg', )
