import os.path
import time
from src.utils.util import *
from functools import wraps
from .icondetector import IconDetector
from src.core.adbcontroller import ADBController

def api(func):
    @wraps(func)  # 保留原始函数的元数据
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    wrapper.is_decorated = True  # 添加一个标记
    return wrapper

def get_decorated_methods(cls, decorator):
    decorated_methods = []
    for name in dir(cls):
        method = getattr(cls, name)
        # 检查方法是否可调用并且装饰器是否在方法的 __wrapped__ 属性中
        if callable(method) and getattr(method, 'is_decorated', False):
            decorated_methods.append(name)
    return decorated_methods

class Agent():
    def __init__(self, task_json_file, config_path):
        self.tasks = load_json_file(task_json_file)
        self.configs = load_yaml_file(config_path)
        self.max_op_time = self.configs["max_op_time"]
        self.icon_detector = IconDetector(**self.configs["icon_detector"])
        self.controller = ADBController(adb_path=self.configs["adb_path"], save_dir=self.configs["save_dir"])
        self.save_dir = self.configs["save_dir"]

    def sanity_check(self, action_name):
        supported_tasks = get_decorated_methods(self, api)
        if action_name not in supported_tasks:
            raise Exception("UnSupported Task Error")

    def run(self):
        for action in self.tasks["actions"]:
            print("input action ", action)
            if action.get("action"):
                k = action.get("action")
                action.pop("action")
                v = ",".join([str(item) for item in action.values()])
                print("**************************")
                print(f"Running Task {k}:{v} ...")
                start_time = time.time()
                method = getattr(self, k)
                if k == "swipe":
                    args = v.split(",")
                    status = method(*args)
                else:
                    status = method(v)
                if time.time() - start_time >= self.max_op_time:
                    raise Exception("Exceed the Maximum Time Error")

                if status:
                    print(f"Task {k}:{v} finished in success.")
                    continue
                else:
                    raise Exception(f"Task {k}: {v} Failed Error")

        print("All Task have finished")
        icon_path = os.path.join(self.save_dir, 'tmp_icon.png')
        if os.path.exists(icon_path):
            os.remove(icon_path)


    @api
    def startActivity(self, activity_name):
        pass

    @api
    def stopActivity(self, activity_name):
        pass

    @api
    def openAppByIcon(self, icon):
        icon_path = os.path.join(self.save_dir, 'tmp_icon.png')
        if os.path.exists(icon_path):
            os.remove(icon_path)
        load_image(icon).save(icon_path)
        self.controller.home_btn()
        time.sleep(0.5)
        swipe_direction = 0
        count = 0
        bbox = None
        while True:
            img_cur = self.controller.get_screenshot(scale_ratio=1)
            det_res = self.icon_detector.det(img_cur, icon_path)
            print(det_res)
            if len(det_res) > 0 and float(det_res[0][0]) >= float(self.configs["icon_sim_threshold"]):
                bbox = det_res[0][1]
                break

            direction = 'left' if swipe_direction == 0 else "right"
            self.swipe(direction, 500, 300)
            time.sleep(0.5)
            img = self.controller.get_screenshot(scale_ratio=1)
            if is_same_img(img, img_cur):
                swipe_direction = 1 - swipe_direction
                count += 1

            if count >= 2:
                raise Exception("Failed to find APP Icon Error")

        print("bbox: ", bbox)
        x,y = calculate_center(bbox)
        print("center_x, center_y: ", (x, y))
        self.controller.tap(x, y)
        return True

    @api
    def click_icon(self, icon):
        icon_path = os.path.join(self.save_dir, 'tmp_icon.png')
        if os.path.exists(icon_path):
            os.remove(icon_path)
        load_image(icon).save(icon_path)
        img_cur = self.controller.get_screenshot(scale_ratio=1)
        det_res = self.icon_detector.det(img_cur, icon_path)
        if len(det_res) > 0 and float(det_res[0][0]) >= float(self.configs["icon_sim_threshold"]):
            bbox = det_res[0][1]
            print("bbox: ", bbox)
            x, y = calculate_center(bbox)
            print("center_x, center_y: ", (x, y))
            self.controller.tap(x, y)
            return True
        else:
            raise Exception("Failed to Click Icon Error")

        return False

    @api
    def long_press_icon(self, icon):
        pass

    @api
    def swipe(self, direction, distance, duration):
        distance = int(distance)
        duration = int(duration)
        if direction == 'left':
            self.controller.swipe_left(distance, duration)
        elif direction == 'right':
            self.controller.swipe_right(distance, duration)
        elif direction == 'up':
            self.controller.swipe_up(distance, duration)
        else:
            self.controller.swipe_down(distance, duration)

        self.sleep(duration / 1000)
        return True

    @api
    def sleep(self, seconds):
        time.sleep(int(seconds))
        return True

