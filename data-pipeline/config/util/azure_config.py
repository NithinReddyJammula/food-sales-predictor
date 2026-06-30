import os
import re
from pathlib import Path
import yaml

def load_env_file(env_path):
    if not env_path.exists():
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip("'\"")
                if k and k not in os.environ:
                    os.environ[k] = v

# Load environment files manually if we're executing locally/outside docker-compose
try:
    current_file_path = Path(__file__).resolve()
    project_root = current_file_path.parent.parent.parent.parent
    load_env_file(project_root / '.env')
    load_env_file(project_root / 'data-pipeline' / '.env')
except Exception:
    pass

def interpolate_value(val):
    if not isinstance(val, str):
        return val
    pattern = re.compile(r'\$\{(\w+)(?::-([^}]*))?\}')
    def replace(match):
        var_name = match.group(1)
        default_val = match.group(2)
        env_val = os.environ.get(var_name)
        if env_val is not None:
            return env_val
        elif default_val is not None:
            return default_val
        else:
            return ''
    return pattern.sub(replace, val)

def interpolate_dict(d):
    if isinstance(d, dict):
        return {k: interpolate_dict(v) for k, v in d.items()}
    elif isinstance(d, list):
        return [interpolate_dict(v) for v in d]
    else:
        return interpolate_value(d)

current_dir = Path(__file__).parent
config_path = current_dir.parent / 'config.yaml'

def load_config(path=None):
    target_path = Path(path) if path else config_path
    with open(target_path, 'r') as config_file:
        config = yaml.safe_load(config_file)
    return interpolate_dict(config)



