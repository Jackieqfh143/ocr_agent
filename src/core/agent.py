import os.path
import time
from src.utils.util import *
from functools import wraps
from .icondetector import IconDetector
from .textdetector import OCR, find_nearest_bbox, find_bbox_by_text
from src.core.adbcontroller import ADBController
from tqdm import  tqdm

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
        self.text_detector = OCR(**self.configs["text_detector"])
        self.controller = ADBController(adb_path=self.configs["adb_path"], save_dir=self.configs["save_dir"])
        self.save_dir = self.configs["save_dir"]
        self.icon_sim_threshold = float(self.configs["icon_sim_threshold"])
        self.text_score_threshold = float(self.configs["text_detector"]["text_threshold"])
        self.before_check_actions = []

    def sanity_check(self, action_name):
        supported_tasks = get_decorated_methods(self, api)
        if action_name not in supported_tasks:
            raise Exception("UnSupported Task Error")

    def run(self):
        self.controller.init_task()
        self.before_check_actions = [item.get("action_list") for item in self.tasks["actions"] if item.get("action") == "before_check"]
        self.on_error_actions = [item.get("action_list") for item in self.tasks["actions"] if item.get("action") == "on_error"]
        for action in self.tasks["actions"]:
            if len(self.before_check_actions) > 0:
                self.before_check(self.before_check_actions[0])

            action_name = action.get("action")
            if action_name != "before_check" or action_name != "on_error":
                try:
                    if self._perform_task(action):
                        continue
                except Exception as e:
                    print(e)
                    if len(self.on_error_actions) > 0:
                        self.on_error(self.on_error_actions[0], self._perform_task, action)



        print("All Task have finished")
        icon_path = os.path.join(self.save_dir, 'tmp_icon.png')
        if os.path.exists(icon_path):
            os.remove(icon_path)


    @api
    def startActivity(self, activity_name, **kwargs):
        self.controller.start_activity(activity_name)

    @api
    def stopActivity(self, activity_name, **kwargs):
        self.controller.stop_activity(activity_name)

    @api
    def openAppByIcon(self, icon, text = '', **kwargs):
        text = text.strip()
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
                if text != '':
                    if self._check_nearby_text(img_cur, bbox, text):
                        break
                else:
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
    def click_icon(self, icon, text ='', **kwargs):
        img_cur = self.controller.get_screenshot(scale_ratio=1)
        status,bbox,score = self._find_bbox_by_icon(img_cur, icon)
        if status and self._check_nearby_text(img_cur, bbox, text):
            print("bbox: ", bbox)
            print("score: ", score)
            x, y = calculate_center(bbox)
            print("center_x, center_y: ", (x, y))
            self.controller.tap(x, y)
            return True

        return False

    @api
    def long_press_icon(self, icon, text = '', duration = 1000,  **kwargs):
        img_cur = self.controller.get_screenshot(scale_ratio=1)
        status, bbox, score = self._find_bbox_by_icon(img_cur, icon)
        if status and self._check_nearby_text(img_cur, bbox, text):
            print("bbox: ", bbox)
            print("score: ", score)
            x, y = calculate_center(bbox)
            print("center_x, center_y: ", (x, y))
            self.controller.long_press(x, y, duration)
            return True

        return False

    @api
    def swipe(self, direction, distance, duration,  **kwargs):
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
    def sleep(self, duration,  **kwargs):
        time.sleep(int(duration))
        return True

    @api
    def click_text(self, text, **kwargs):
        status,bbox, score = self._find_bbox_by_text(text)
        if status:
            print("bbox: ", bbox)
            x, y = calculate_center(bbox)
            print("center_x, center_y: ", (x, y))
            self.controller.tap(x, y)
            return True

        return False

    @api
    def long_press_text(self, text, duration, **kwargs):
        status, bbox, score = self._find_bbox_by_text(text)
        if status:
            print("bbox: ", bbox)
            x, y = calculate_center(bbox)
            print("center_x, center_y: ", (x, y))
            self.controller.long_press(x, y, duration)
            return True

        return False

    @api
    def input_text(self, text):
        self.controller.type(text)
        return True

    @api
    def exist_icon(self, icon, score = None, true_action = {}, false_action = {}):
        if not score:
            score = self.icon_sim_threshold
        status, bbox, pred_score = self._find_bbox_by_icon(icon)
        if status and pred_score >= score:
            print(f"Icon {icon} is exist")
            print("Perform True Action")
            return self._perform_task(true_action)
        else:
            print(f"Icon {icon} does not exist")
            print("Perform False Action")
            return self._perform_task(false_action)

    @api
    def exist_text(self, text, score = None, true_action = {}, false_action = {}):
        if not score:
            score = self.text_score_threshold
        status, bbox, pred_score = self._find_bbox_by_text(text)
        if status and pred_score >= score:
            print(f"Text {text} is exist")
            print("Perform True Action")
            return self._perform_task(true_action)
        else:
            print(f"Text {text} does not exist")
            print("Perform False Action")
            return self._perform_task(false_action)

    @api
    def on_error(self, action_list, callback, callback_params):
        print("Running on_error tasks")
        for i, action in enumerate(action_list):
            self._perform_task(action)
            print("Running callback function...")
            try:
                callback(callback_params)
            except Exception as e:
                if i == len(action_list) - 1:
                    raise e
                else:
                    pass
            else:
                break

        print("All on_error tasks have been finished")

    @api
    def before_check(self, action_list):
        print("Running before tasks")
        for action in action_list:
            self._perform_task(action)
        print("All before tasks have been finished")

    @api
    def back_home(self, **kwargs):
        self.controller.home_btn()
        return True

    @api
    def back(self, **kwargs):
        self.controller.back()
        return True

    @api
    def repeat_actions(self, action_list, repeat_times):
        for i in tqdm(range(repeat_times)):
            print(f"Running the NO {i} repeat_actions")
            for action in action_list:
                self._perform_task(action)
            print(f"The NO {i} repeat_actions have been finished")

    def _check_nearby_text(self, img_cur, bbox, text):
        if text != '':
            text_det_res = self.text_detector.det(img_cur)
            _, target_text, target_score = find_nearest_bbox(bbox, *text_det_res)
            print(f"input text: {text}, nearest text: {target_text}, text_det_score: {target_score}")
            if target_text == text and target_score >= self.text_score_threshold:
                return True
            else:
                return False
        else:
            return True

    def _find_bbox_by_icon(self, img_cur, icon):
        icon_path = os.path.join(self.save_dir, 'tmp_icon.png')
        if os.path.exists(icon_path):
            os.remove(icon_path)
        load_image(icon).save(icon_path)
        det_res = self.icon_detector.det(img_cur, icon_path)
        if len(det_res) > 0 and float(det_res[0][0]) >= self.icon_sim_threshold :
            bbox = det_res[0][1]
            return True, bbox, float(det_res[0][0])
        else:
            return False, None, None

    def _find_bbox_by_text(self, text):
        img_cur = self.controller.get_screenshot(scale_ratio=1)
        text_det_res = self.text_detector.det(img_cur)
        bbox, score = find_bbox_by_text(text, *text_det_res)
        print(f"_find_bbox_by_text bbox:{bbox} score:{score}")
        if bbox:
            return True, bbox, score
        else:
            return False, None, None

    def _perform_task(self, action):
        if not action or len(action) == 0:
            print("Skip Empty Task")
            return True

        print("input action ", action)
        method_name = action.get("action")
        args = {k:v for k,v in action.items() if k != "action"}
        print("**************************")
        print(f"Running Task {method_name}: {args} ...")
        start_time = time.time()
        method = getattr(self, method_name)
        status = method(**args)
        if time.time() - start_time >= self.max_op_time:
            raise Exception("Exceed the Maximum Time Error")

        if status:
            print(f"Task {method_name}: {args} finished in success.")
            return True
        elif args.get("skipable"):
            print(f"Task {method_name}: {args} has been skipped.")
            return True
        else:
            raise Exception(f"Task {method_name}: {args} Failed Error")







