from pathlib import Path
import yaml

current_dir= Path(__file__).parent
config_path=current_dir.parent/'config.yaml'
def load_config():
    with open(config_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return config



