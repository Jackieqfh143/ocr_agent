import cv2
from skimage.metrics import structural_similarity as ssim
import numpy as np
from glob import  glob
from PIL import Image
import matplotlib.pyplot as plt


def ssimFun(img1, img2):
    grayA = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    grayB = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    similarity_index, _ = ssim(grayA, grayB, full=True)
    print(f"SSIM 相似度: {similarity_index}")
    return similarity_index

def mse(imageA, imageB):
    # 计算均方误差
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])
    print(f"mse误差: {err}")
    return err

def siftFun(img1, img2):
    try:
        # 使用 SIFT 特征检测器
        sift = cv2.SIFT_create()
        keypointsA, descriptorsA = sift.detectAndCompute(img1, None)
        keypointsB, descriptorsB = sift.detectAndCompute(img2, None)

        # 创建 BFMatcher 进行匹配
        bf = cv2.BFMatcher(cv2.NORM_L2, crossCheck=True)
        matches = bf.match(descriptorsA, descriptorsB)

        # 计算匹配的总数
        similarity = len(matches)
        print(f"特征点匹配数量: {similarity}")
        return similarity
    except Exception as e:
        print(e)
        return 0

import os
from src.core.icondetector import IconDetector
from src.utils.util import get_uni_name, load_yaml_file

if __name__ == '__main__':
    img_dir = "results/icon_detector/20250119_193051_0fe261ed-a56a-4f60-96b8-e51874c88427/segments/"
    configs = load_yaml_file("configs/config.yaml")
    weight_path = './weights/FastSAM-s.pt'
    source_img = './imgs/demo.jpg'
    icon_img = 'imgs/tiktok/tiktok_comments.png'
    icon_img = np.array(Image.open(icon_img).resize((224, 224)))
    img_list = glob(f"{img_dir}*.png")
    img_list = [np.array(Image.open(img).resize((224, 224))) for img in img_list]
    print()
    # detector = IconDetector(**configs["icon_detector"])
    # detector.det(source_img, icon_img)

    pred_list = []
    for img in img_list:
        res = siftFun(icon_img, img)
        pred_list.append((res, img))

    # 按照 SSIM 分数排序
    pred_list = sorted(pred_list, key=lambda x: x[0], reverse=True)

    # 创建 Matplotlib 图形，设置为 len(pred_list) 行和 1 列
    fig, axes = plt.subplots(len(pred_list), 1, figsize=(10, 80))

    # 绘制每张图像
    for i in range(len(pred_list)):
        axes[i].imshow(cv2.cvtColor(pred_list[i][1], cv2.COLOR_BGR2RGB))
        axes[i].axis('off')  # 关闭坐标轴
        axes[i].text(0, 0, s=f'sift: {pred_list[i][0]:.2f}', fontsize=8, color='white', backgroundcolor='black')

    # 设置标题
    plt.suptitle('Image Similarity Comparison', fontsize=16)
    plt.tight_layout(rect=[0, 0, 1, 0.95])

    # 保存结果图像
    plt.savefig('comparison_result.png', bbox_inches='tight')
    plt.show()