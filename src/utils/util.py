import base64
import hashlib
import json
import os
from io import BytesIO
import yaml
import cv2
from datetime import datetime
import uuid
import requests
from PIL import Image, ImageDraw
from PIL import ImageFont
import numpy as np

def get_uni_name():
    now = datetime.now()
    time_str = now.strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())
    unique_name = f"{time_str}_{unique_id}"
    return unique_name

def draw_bbox(img, bbox, color = (0, 0, 255)):
    cv2.rectangle(img, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
    return img


def draw_text(img, bbox, text, text_color = (0, 0, 255), font_path = "resources/fonts/zhouzisongti.otf"):
    x1, y1 = bbox[0],bbox[1]
    x2, y2 = bbox[2],bbox[3]
    width = x2 - x1
    height = y2 - y1

    color = text_color
    thickness = 1
    font_scale = 1

    try:
        font_size = 20
        font = ImageFont.truetype(font_path, font_size)
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(pil_img)
        # 计算文本的边界框
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        # 计算文本位置
        text_x = x1 + (width - text_width) // 2
        text_y = y1 + (height - text_height) // 2
        # 绘制文本
        draw.text((text_x, text_y), text, fill=text_color, font=font)

        # 转换回 OpenCV 格式
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    except Exception as e:
        print("加载字体文件失败")
        print(e)
        font = cv2.FONT_HERSHEY_SIMPLEX
        (text_width, text_height), baseline = cv2.getTextSize(text, font, font_scale, thickness)

        text_x = x1 + (width - text_width) // 2
        text_y = y1 + (height + text_height) // 2

        cv2.putText(img, text, (text_x, text_y), font, font_scale, color, thickness, cv2.LINE_AA)

    return img


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def decode_image(encoded_image, output_path):
    with open(output_path, "wb") as image_file:
        image_file.write(base64.b64decode(encoded_image))


def load_image(image_input):
    # 检查是否是本地文件路径
    if isinstance(image_input, str) and os.path.isfile(image_input):
        return load_image_from_file(image_input)

    # 检查是否是有效的 URL
    elif image_input.startswith(('http://', 'https://')):
        return load_image_from_url(image_input)

    # 检查是否是 Base64 字符串
    elif image_input.startswith('data:image/'):
        return load_image_from_base64(image_input)

    else:
        raise ValueError("Unsupported image input format.")


def load_image_from_file(file_path):
    """从本地文件加载图像"""
    return Image.open(file_path).convert('RGB')


def load_image_from_url(url):
    # 发送请求获取图像
    response = requests.get(url)

    # 检查请求是否成功
    if response.status_code == 200:
        # 使用 BytesIO 将字节数据转换为文件对象
        image = Image.open(BytesIO(response.content))
        return image
    else:
        print(f"Failed to retrieve image. Status code: {response.status_code}")
        return None


def load_image_from_base64(base64_string):
    # 解码 Base64 字符串
    image_data = base64.b64decode(base64_string)

    # 使用 BytesIO 将字节数据转换为文件对象
    image = Image.open(BytesIO(image_data))

    return image

def load_json_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
        return data

def save2json_file(file_name, data):
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)

def py2json(json_string):
    return json.loads(json_string)

def json2py(json_data)   :
    return json.dumps(json_data, ensure_ascii=False, indent=4)

def load_yaml_file(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

def is_same_img(img1, img2):
    img1 = load_image(img1)
    img2 = load_image(img2)
    def image_hash(image):
        # 将图像转换为灰度图并缩小
        img_w, img_h = img1.size
        image = image.convert('L').resize((img_w // 4, img_h // 4), Image.Resampling.LANCZOS)
        # 获取像素数据
        pixels = list(image.getdata())
        # 计算哈希值
        return hashlib.md5(bytes(pixels)).hexdigest()
    hash1 = image_hash(img1)
    hash2 = image_hash(img2)
    print("image hash1 ", hash1)
    print("image hash2 ", hash2)
    return hash1 == hash2


def calculate_center(bbox):
    """
    计算边界框的中心点

    :param bbox: 边界框，格式为 (x_min, y_min, x_max, y_max)
    :return: 中心点 (center_x, center_y)
    """
    x_min, y_min, x_max, y_max = bbox
    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    return center_x, center_y