"""
配置文件
包含API密钥、系统设置等配置信息
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# Mathpix API 配置
# 注意：请在这里填入您的API密钥
MATHPIX_APP_ID = os.getenv("MATHPIX_APP_ID", "ai_t_b2282a_f499d0")
MATHPIX_APP_KEY = os.getenv("MATHPIX_APP_KEY", "55e4fb5039548002f5f1d8a5b81f7c3b86ad06b4c9e480f0e3d658adc52abc48")
MATHPIX_API_URL = "https://api.mathpix.com/v3/text"

# 文件路径配置
UPLOAD_DIR = PROJECT_ROOT / "uploads"
RESULTS_DIR = PROJECT_ROOT / "results"
TEMPLATES_DIR = PROJECT_ROOT / "templates"

# 图像处理配置
MAX_IMAGE_SIZE = (2048, 2048)  # 最大图像尺寸
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.pdf'}

# OCR配置
OCR_CONFIDENCE_THRESHOLD = 0.7  # 置信度阈值
MAX_RETRIES = 3  # 最大重试次数
TIMEOUT = 30  # 请求超时时间（秒）

# 日志配置
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# 确保目录存在
UPLOAD_DIR.mkdir(exist_ok=True)
RESULTS_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)

