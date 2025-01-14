from src.core.agent import Agent
import matplotlib
matplotlib.use('TkAgg',force=True)
print("Switched to:",matplotlib.get_backend())

if __name__ == '__main__':
    task_json = "tasks/youku_login.json"
    config_path = "configs/config.yaml"
    agent_model = Agent(task_json_file=task_json, config_path=config_path)
    agent_model.run()

