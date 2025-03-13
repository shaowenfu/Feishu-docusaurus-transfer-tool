# config.py
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 飞书应用信息
APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")

# 文档信息
DOC_TOKEN = os.getenv("FEISHU_DOC_TOKEN")  # 《命理Tips》文档的obj_token

# Docusaurus项目路径
DOCUSAURUS_PATH = "e:/Obsidian_space/HomeOfSherwen/Home_file/CanTianAI/cantian-ai-wiki"
DOCS_PATH = f"{DOCUSAURUS_PATH}/docs"
SIDEBAR_PATH = f"{DOCUSAURUS_PATH}/sidebars.ts"

# API URLs
AUTH_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
DOC_URL = "https://open.feishu.cn/open-apis/doc/v2/{}/content"

# 百度翻译API配置
BAIDU_APP_ID = os.getenv("BAIDU_APP_ID")
BAIDU_SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")

# 翻译配置
# 支持的目标语言列表
TARGET_LANGUAGES = ["en", "ja", "ko", "zh-Hant"]  # 不包含zh-Hans（源语言）
