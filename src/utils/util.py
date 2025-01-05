import cv2
from datetime import datetime
import uuid

def get_uni_name():
    now = datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M")
    unique_id = str(uuid.uuid4())
    unique_name = f"{time_str}_{unique_id}"
    return unique_name

def draw_bbox(img, bbox, color = (0, 0, 255)):
    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
    return img


def draw_text(img, bbox, text, text_color = (0, 0, 255)):
    x1, y1 = bbox[0],bbox[1]
    x2, y2 = bbox[2],bbox[3]
    width = x2 - x1
    height = y2 - y1

    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    color = text_color
    thickness = 1

    (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

    text_x = x1 + (width - text_width) // 2
    text_y = y1 + (height + text_height) // 2

    cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)

    return img