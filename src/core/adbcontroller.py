import os.path
import threading
import time
import subprocess
from PIL import Image
from src.utils.util import get_uni_name


class ADBController:
    """
    ADB（Android Debug Bridge）控制器，用于与 Android 设备进行交互。
    提供屏幕截图、滑动操作、按键事件等功能。
    """

    def __init__(self, adb_path, save_dir):
        """
        初始化 ADBController 类。

        :param adb_path: ADB 可执行文件的路径
        :param save_dir: 保存截图和录屏的目录
        """
        self.adb_path = adb_path
        self.screen_width, self.screen_height, self.screen_center = self.get_screen_size()
        self.save_dir = os.path.join(save_dir, "screenshot", get_uni_name())
        os.makedirs(self.save_dir, exist_ok=True)

        if self.is_screen_off() or self.is_screen_locked():
            self.unlock_phone()

    def get_screen_size(self):
        """
        获取设备屏幕尺寸并计算中心点。

        :return: 屏幕宽度, 屏幕高度, 屏幕中心点 (x, y)
        :raises Exception: 如果获取屏幕尺寸失败
        """
        command = f"{self.adb_path} shell wm size"
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        if result.returncode == 0:
            output = result.stdout.strip()
            size = output.split(": ")[1]
            width, height = map(int, size.split('x'))
            center_x = width // 2
            center_y = height // 2
            return width, height, (center_x, center_y)
        else:
            raise Exception(f"Error executing command: {result.stderr}")

    def swipe(self, start_x, start_y, end_x, end_y, duration):
        """
        执行滑动操作。

        :param start_x: 起始点 x 坐标
        :param start_y: 起始点 y 坐标
        :param end_x: 结束点 x 坐标
        :param end_y: 结束点 y 坐标
        :param duration: 滑动持续时间（毫秒）
        """
        command = self.adb_path + f" shell input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
        res = subprocess.run(command, capture_output=True, text=True, shell=True)
        print(f"从点 ({start_x},{start_y}) 滑动到 ({end_x},{end_y})")
        print(res)

    def swipe_up(self, distance, duration, offset=300):
        """
        向上滑动指定距离。

        :param distance: 滑动距离（像素）
        :param duration: 滑动持续时间（毫秒）
        :param offset: 从距离中心点的偏移量
        """
        print(f"向上滑动 {distance} pixels ")
        start_x, start_y = self.screen_center
        start_y = start_y + offset
        end_x, end_y = (start_x, start_y - distance)  # 向上滑动，y 坐标减小
        self.swipe(start_x, start_y, end_x, end_y, duration)

    def swipe_down(self, distance, duration, offset=300):
        """
        向下滑动指定距离。

        :param distance: 滑动距离（像素）
        :param duration: 滑动持续时间（毫秒）
        :param offset: 从距离中心点的偏移量
        """
        print(f"向下滑动 {distance} pixels ")
        start_x, start_y = self.screen_center
        start_y = start_y - offset
        end_x, end_y = (start_x, start_y + distance)  # 向下滑动，y 坐标增加
        self.swipe(start_x, start_y, end_x, end_y, duration)

    def swipe_left(self, distance, duration, offset=500):
        print("swipe_left")
        """
        向左滑动指定距离。

        :param distance: 滑动距离（像素）
        :param duration: 滑动持续时间（毫秒）
        :param offset: 从距离中心点的偏移量
        """
        print(f"向左滑动 {distance} pixels ")
        start_x, start_y = self.screen_center
        start_x = start_x + offset
        end_x, end_y = (start_x - distance, start_y)  # 向左滑动，x 坐标减小
        self.swipe(start_x, start_y, end_x, end_y, duration)

    def swipe_right(self, distance, duration, offset=500):
        print("swipe_right")
        """
        向右滑动指定距离。

        :param distance: 滑动距离（像素）
        :param duration: 滑动持续时间（毫秒）
        :param offset: 从距离中心点的偏移量
        """
        print(f"向右滑动 {distance} pixels ")
        start_x, start_y = self.screen_center
        start_x = start_x - offset
        end_x, end_y = (start_x + distance, start_y)  # 向右滑动，x 坐标增加
        self.swipe(start_x, start_y, end_x, end_y, duration)

    def power_btn(self):
        """
        模拟按下电源按钮。
        """
        print("模拟按下电源按钮")
        command = self.adb_path + f" shell input keyevent 26"
        subprocess.run(command, capture_output=True, text=True, shell=True)

    def get_screenshot(self, scale_ratio=0.5):
        """
        获取屏幕截图并保存到指定目录。

        :param scale_ratio: 缩放比例（0-1之间的值）
        :return: 保存的截图路径
        """
        command = self.adb_path + " shell rm /sdcard/screenshot.png"
        subprocess.run(command, capture_output=True, text=True, shell=True)
        time.sleep(0.5)
        command = self.adb_path + " shell screencap -p /sdcard/screenshot.png"
        subprocess.run(command, capture_output=True, text=True, shell=True)
        time.sleep(0.5)
        command = self.adb_path + f" pull /sdcard/screenshot.png {self.save_dir}"
        subprocess.run(command, capture_output=True, text=True, shell=True)

        image_path = f"{self.save_dir}/screenshot.png"
        save_path = f"{self.save_dir}/{get_uni_name()}.jpg"
        print(f" 获取屏幕截图并保存到指定目录 {save_path}")

        image = Image.open(image_path)
        original_width, original_height = image.size
        new_width = int(original_width * scale_ratio)
        new_height = int(original_height * scale_ratio)
        resized_image = image.resize((new_width, new_height))
        resized_image.convert("RGB").save(save_path, "JPEG")
        os.remove(image_path)
        return save_path

    def record_screen(self, save_name, duration=180):
        """
        录制屏幕并保存视频文件。

        :param save_name: 录制视频的保存名称
        :param duration: 录制持续时间（秒）
        """
        print(f" 录制屏幕并保存视频文件到 {save_name}")
        command = self.adb_path + " shell rm /sdcard/screen_record.mp4"
        subprocess.run(command, capture_output=True, text=True, shell=True)
        time.sleep(0.5)
        command = self.adb_path + f" shell screenrecord --time-limit {duration} /sdcard/screen_record.mp4"
        subprocess.run(command, capture_output=True, text=True, shell=True)

        def delay_task():
            command = self.adb_path + f" pull /sdcard/screen_record.mp4 {self.save_dir}/{save_name}"
            subprocess.run(command, capture_output=True, text=True, shell=True)

        timer = threading.Timer(duration, delay_task)
        timer.start()

    def tap(self, x, y):
        """
        模拟在指定坐标位置的点击操作。

        :param x: 点击的 x 坐标
        :param y: 点击的 y 坐标
        """
        print(f" 模拟在坐标 ({x},{y}) 位置的点击操作")
        command = self.adb_path + f" shell input tap {x} {y}"
        subprocess.run(command, capture_output=True, text=True, shell=True)

    def long_press(self, x, y, duration):
        """
        模拟在指定坐标位置的长按操作。

        :param x: 长按的 x 坐标
        :param y: 长按的 y 坐标
        :param duration: 长按持续时间（毫秒）
        """
        print(f" 模拟在坐标 ({x},{y}) 位置的长按操作")
        self.swipe(x, y, x, y, duration)

    def type(self, text):
        """
        在设备上输入文本。

        :param text: 要输入的文本
        """
        print(f"在设备上输入文本 {text}")
        text = text.replace("\\n", "_").replace("\n", "_")
        for char in text:
            if char == ' ':
                command = self.adb_path + f" shell input text %s"
                subprocess.run(command, capture_output=True, text=True, shell=True)
            elif char == '_':
                command = self.adb_path + f" shell input keyevent 66"
                subprocess.run(command, capture_output=True, text=True, shell=True)
            elif 'a' <= char <= 'z' or 'A' <= char <= 'Z' or char.isdigit():
                command = self.adb_path + f" shell input text {char}"
                subprocess.run(command, capture_output=True, text=True, shell=True)
            elif char in '-.,!?@\'°/:;()':
                command = self.adb_path + f" shell input text \"{char}\""
                subprocess.run(command, capture_output=True, text=True, shell=True)
            else:
                command = self.adb_path + f" shell am broadcast -a ADB_INPUT_TEXT --es msg \"{char}\""
                subprocess.run(command, capture_output=True, text=True, shell=True)

    def back(self):
        """
        模拟按下返回按钮。
        """
        print( "模拟按下返回按钮")
        command = self.adb_path + f" shell input keyevent 4"
        subprocess.run(command, capture_output=True, text=True, shell=True)

    def home_btn(self):
        """
        返回设备主屏幕。
        """
        print("返回设备主屏幕")
        command = self.adb_path + f" shell am start -a android.intent.action.MAIN -c android.intent.category.HOME"
        subprocess.run(command, capture_output=True, text=True, shell=True)

    def start_activity(self, activity_name):
        print(f"启动活动 {activity_name}")
        command = self.adb_path + f" shell am start -n {activity_name}"
        subprocess.run(command, capture_output=True, text=True, shell=True)

    def stop_activity(self, activity_name):
        print(f"停止活动 {activity_name}")
        command = self.adb_path + f" shell am force-stop {activity_name}"
        subprocess.run(command, capture_output=True, text=True, shell=True)

    def unlock_phone(self):
        if self.is_screen_off():
            self.power_btn()
            time.sleep(0.5)

        if self.is_screen_locked():
            time.sleep(0.5)
            print("尝试自动解锁手机")
            self.swipe(self.screen_center[0], self.screen_center[1] + 1000, self.screen_center[0], self.screen_center[1] - 200, 500)

    def is_screen_off(self):
        command = self.adb_path + f" shell dumpsys power"
        result = subprocess.run(command, capture_output=True, text=True, shell=True)

        for line in result.stdout.splitlines():
            if "Display Power" in line:
                if "state=OFF" in line:
                    print("屏幕处于熄屏状态")
                    return True
                elif "state=ON" in line:
                    print("屏幕处于亮屏状态")
                    return False

        return None

    def is_screen_locked(self):
        command = self.adb_path + f" shell dumpsys window policy"
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        lines = result.stdout.splitlines()
        loc_flag = 0
        for i in range(len(lines)):
            if 'KeyguardServiceDelegate'.strip() in lines[i]:
                loc_flag = i + 1

        print(lines[loc_flag])
        if 'showing=true' in lines[loc_flag] and loc_flag != 0:
            print("屏幕处于锁定状态")
            return True
        else:
            print("屏幕处于解锁状态")
            return False

        return None
