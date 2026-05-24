import os
from pathlib import Path
from dotenv import load_dotenv
import pytest

# 强制定位到根目录的 .env 文件并加载
root_dir = Path(__file__).parent.parent
env_path = root_dir / ".env"

if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    # 怕路径数错了，做个保险：直接在当前目录往上找
    load_dotenv(find_dotenv=True, override=True)