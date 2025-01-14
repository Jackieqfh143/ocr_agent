from paddlex import create_pipeline
import math
import os
from src.utils.util import get_uni_name, is_same_img

def calculate_bbox_center(bbox):
    min_x, min_y, max_x, max_y = bbox
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2
    return (center_x, center_y)


def calculate_distance(bbox1, bbox2):
    center1 = calculate_bbox_center(bbox1)
    center2 = calculate_bbox_center(bbox2)

    distance = math.sqrt((center2[0] - center1[0]) ** 2 + (center2[1] - center1[1]) ** 2)
    return distance


def filter_by_score(bbox_list, text_list, score_list, score_threshold = 0.9):
    # 使用列表推导式筛选
    filtered_bboxes = [bbox for bbox, score in zip(bbox_list, score_list) if score >= score_threshold]
    filtered_texts = [text for text, score in zip(text_list, score_list) if score >= score_threshold]
    filtered_scores = [score for score in score_list if score >= score_threshold]

    return filtered_bboxes, filtered_texts, filtered_scores

def bbox_to_corners(bbox):
    # 提取 x 和 y 坐标
    x_coords = [point[0] for point in bbox]
    y_coords = [point[1] for point in bbox]

    # 计算最小和最大坐标
    min_x = min(x_coords)
    max_x = max(x_coords)
    min_y = min(y_coords)
    max_y = max(y_coords)

    # 返回左上角和右下角的坐标
    return [min_x, min_y,max_x, max_y]


def find_nearest_bbox(target_bbox, bbox_list, text_list, score_list):
    nearest_distance = float('inf')
    nearest_index = -1

    for i, bbox in enumerate(bbox_list):
        distance = calculate_distance(target_bbox, bbox)

        if distance < nearest_distance:
            nearest_distance = distance
            nearest_index = i

    if nearest_index != -1:
        return bbox_list[nearest_index], text_list[nearest_index], score_list[nearest_index]
    else:
        return None, None, None

def find_bbox_by_text(target_text, bbox_list, text_list, score_list):
    index = -1
    for i, text in enumerate(text_list):
        if target_text in text:
            index = i
            break
        else:
            continue

    if index != -1:
        return bbox_list[index], score_list[index]
    else:
        return None,None

class OCR:
    def __init__(self, save_dir = './results', device = "cpu", text_threshold = 0.85):
        self.save_dir = os.path.join(save_dir, get_uni_name())
        self.pipeline = create_pipeline(pipeline="OCR", device=device)
        self.text_threshold = text_threshold
        os.makedirs(self.save_dir, exist_ok=True)

        self.box_list = []
        self.text_list = []
        self.score_list = []
        self.cache_img_path = ""

    def should_use_cache(self, img):
        if img == self.cache_img_path:
            if self.cache_img_path != "":
                return is_same_img(self.cache_img_path, img)
            else:
                return True
        else:
            return False


    def det(self, img_path):
        if not self.should_use_cache(img_path):
            self.cache_img_path = img_path
            output = self.pipeline.predict(img_path)
            bbox_list = []
            text_list = []
            score_list = []

            for res in output:
                res.save_to_img(self.save_dir)
                res.save_to_json(self.save_dir)
                bbox_list += res["dt_polys"]
                text_list += res["rec_text"]
                score_list += res["rec_score"]

            bbox_list, text_list, self.score_list = filter_by_score(bbox_list, text_list, score_list, self.text_threshold)
            self.bbox_list = [bbox_to_corners(bbox) for bbox in bbox_list]
            self.text_list = [text.strip() for text in text_list]
        else:
            print("Use cache text detect result")

        return self.bbox_list, self.text_list, self.score_list



if __name__ == '__main__':
    save_dir = "./"
    img_path = "/home/codeoops/code/ocr_agent/results/screenshot/20250114_160102_3620ac70-42b9-4655-908e-1e04bc9a34ea/20250114_160107_b6c7edc0-6731-47ae-8ba5-2b51aaee0ef8.jpg"
    text_detector = OCR(save_dir=save_dir)
    res = text_detector.run(img_path)
    bbox_list, text_list, score_list = res
    print("bbox_list: ", bbox_list)
    print("text_list: ", text_list)
    print("score_list: ", score_list)

    # 设定阈值
    score_threshold = 0.85

    # 筛选数据
    filtered_bboxes, filtered_texts, filtered_scores = filter_by_score(bbox_list, text_list, score_list,
                                                                       score_threshold)

    print("过滤后的 BBoxes:", filtered_bboxes)
    print("过滤后的文本:", filtered_texts)
    print("过滤后的分数:", filtered_scores)

