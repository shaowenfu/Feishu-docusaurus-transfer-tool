# 飞书文档迁移到Docusaurus工具

这个工具用于将飞书文档内容迁移到Docusaurus网站，并支持多语言自动翻译

## 功能概述

1. 通过飞书API获取文档全部块内容
2. 解析文档结构，提取标题和正文
3. 将中文内容同步到i18n/zh-hans目录（而非docs目录）
4. 更新Docusaurus配置
5. 自动翻译文档内容为多种语言
   - 支持百度翻译API（适合一般内容）
   - 支持GPT-4o大模型翻译（适合专业内容，如命理学术语）
6. 将英文翻译同时放置在docs和i18n/en目录下，作为默认语言
7. 可选择推送到Github
8. 支持检查和修正文档排序
   - 自动处理docs和i18n目录下的文档排序
   - 确保intro.md始终位于第一位
   - 保持目录和文件的排序与文档结构一致

## 目录结构

```
feishu-docusaurus/
├── config.py          # 配置文件，存储API密钥等信息
├── feishu_api.py      # 飞书API相关函数
├── document_parser.py # 文档解析相关函数
├── file_generator.py  # 文件生成相关函数（更新：支持i18n目录结构）
├── translator.py      # 翻译相关函数（更新：支持英文作为默认语言）
├── llm_translator.py  # 大模型翻译相关函数（更新：支持英文作为默认语言）
├── main.py            # 主程序入口（更新：支持新的工作流程）
├── README.md          # 本文档
├── 多语言自动翻译指南.md  # 翻译功能使用指南
└── 飞书文档同步与多语言翻译指导.md # 完整使用指南
```

## 使用方法

### 1. 配置环境

确保已安装Python 3.6+和必要的依赖：

```bash
pip install requests lark_oapi argparse
```

### 2. 配置参数

编辑`config.py`文件，设置以下参数：

```python
# 飞书应用信息
APP_ID = "你的飞书应用ID"
APP_SECRET = "你的飞书应用密钥"

# 文档信息
DOC_TOKEN = "文档的obj_token"  # 《命理Tips》文档的obj_token

# Docusaurus项目路径
DOCUSAURUS_PATH = "Docusaurus项目路径"
DOCS_PATH = f"{DOCUSAURUS_PATH}/docs"
SIDEBAR_PATH = f"{DOCUSAURUS_PATH}/sidebars.ts"

# 百度翻译API配置（新增）
BAIDU_APP_ID = "你的百度翻译APP ID"
BAIDU_SECRET_KEY = "你的百度翻译密钥"

# 翻译配置（新增）
TARGET_LANGUAGES = ["en", "ja", "ko", "zh-Hant"]  # 支持的目标语言
```

### 3. 运行脚本

#### 基本命令

```bash
# 基本用法 - 执行所有步骤(同步文档并翻译)
python main.py

# 只同步文档，不执行翻译
python main.py --no-translate

# 只执行翻译，不从飞书获取文档
python main.py --only-translate

# 从现有的Docusaurus项目生成文档结构
python main.py --generate-structure

# 从现有项目生成文档结构但不执行翻译
python main.py --generate-structure --no-translate
```

#### 翻译相关命令

```bash
# 指定要翻译的目标语言
python main.py --languages en,ja,ko

# 使用百度翻译API
python main.py --baidu-app-id YOUR_APP_ID --baidu-secret-key YOUR_SECRET_KEY

# 使用GPT-4o大模型翻译
python main.py --use-llm --azure-endpoint YOUR_ENDPOINT --azure-api-key YOUR_API_KEY

# 组合使用：指定语言和翻译方法
python main.py --languages en,ja --use-llm --azure-endpoint YOUR_ENDPOINT --azure-api-key YOUR_API_KEY

# 只翻译特定语言的现有文档
python main.py --only-translate --languages en,ja

# 使用大模型翻译并指定部署名称（默认为gpt-4o）
python main.py --use-llm --azure-endpoint YOUR_ENDPOINT --azure-api-key YOUR_API_KEY --azure-deployment YOUR_DEPLOYMENT_NAME

# 检查并修正文档排序
python main.py --fix-order
```

#### 命令参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `--no-translate` | 跳过翻译步骤 | `python main.py --no-translate` |
| `--only-translate` | 只执行翻译，不同步文档 | `python main.py --only-translate` |
| `--generate-structure` | 从现有Docusaurus项目生成文档结构 | `python main.py --generate-structure` |
| `--fix-order` | 检查并修正文档排序（包括docs和i18n目录） | `python main.py --fix-order` |
| `--languages` | 指定目标翻译语言，用逗号分隔 | `python main.py --languages en,ja,ko` |
| `--force-translate` | 强制重新翻译所有文件，包括已存在的文件 | `python main.py --force-translate` |
| **百度翻译API参数** | | |
| `--baidu-app-id` | 设置百度翻译API的APP ID | `python main.py --baidu-app-id YOUR_APP_ID` |
| `--baidu-secret-key` | 设置百度翻译API的密钥 | `python main.py --baidu-secret-key YOUR_KEY` |
| **GPT-4o大模型翻译参数** | | |
| `--use-llm` | 使用大模型翻译而不是百度翻译API | `python main.py --use-llm` |
| `--azure-endpoint` | Azure OpenAI API的端点URL | `python main.py --azure-endpoint YOUR_ENDPOINT` |
| `--azure-api-key` | Azure OpenAI API的密钥 | `python main.py --azure-api-key YOUR_API_KEY` |
| `--azure-deployment` | Azure OpenAI API的部署名称，默认为gpt-4o | `python main.py --azure-deployment YOUR_DEPLOYMENT` |

## 文档结构解析规则

脚本会按照以下规则解析飞书文档结构：

1. **根节点**：文档的最顶层，通常是整个文档的标题（如"命理Tips"）
2. **一级标题**（block_type = 4，heading2）：在根节点下直接嵌套的标题，表示文档的主要部分（如"天干"）
3. **二级标题**（block_type = 5，heading3）：在根节点下直接嵌套的标题，表示文档的子部分（如"甲"）
4. **段落**（block_type = 14，code 或 block_type = 2，text）：在根节点下直接嵌套的内容块，表示具体的文本内容

## 文件生成规则

1. 为每个一级标题创建一个目录（如`i18n/zh-hans/docusaurus-plugin-content-docs/current/天干/`）
2. 为每个二级标题创建一个Markdown文件（如`i18n/zh-hans/docusaurus-plugin-content-docs/current/天干/甲.md`）
3. 如果一级标题下有直接段落，则创建一个介绍文件（如`i18n/zh-hans/docusaurus-plugin-content-docs/current/天干/天干介绍.md`）
4. 英文翻译会同时放置在`docs/天干/`和`i18n/en/docusaurus-plugin-content-docs/current/天干/`目录下

## 常见问题

### 1. 获取飞书API访问令牌失败

- 检查APP_ID和APP_SECRET是否正确
- 确认飞书应用是否有足够的权限

### 2. 解析文档内容失败

- 检查DOC_TOKEN是否正确
- 确认文档的访问权限设置

### 3. 创建目录和文件失败

- 检查DOCUSAURUS_PATH是否正确
- 确认有足够的文件系统权限

## 代码说明

### feishu_api.py

负责与飞书API交互，获取文档内容。主要函数：

- `get_tenant_access_token()`: 获取飞书API的tenant_access_token
- `get_token()`: 获取有效的token，处理token过期问题
- `get_document_content()`: 获取文档内容

### document_parser.py

负责解析飞书文档内容，提取标题和正文。主要函数：

- `parse_document_content()`: 解析文档内容，构建文档结构
- `get_text_content()`: 从Text对象中提取文本内容
- `clean_markdown_content()`: 清理markdown内容，处理特殊字符和格式

### file_generator.py

负责创建目录和文件，更新Docusaurus配置。主要函数：

- `get_zh_hans_docs_path()`: 获取简体中文文档路径
- `generate_files()`: 根据文档结构生成目录和文件（更新为使用i18n/zh-hans目录）
- `create_category_json()`: 创建分类的_category_.json文件
- `update_sidebar()`: 更新Docusaurus的sidebars.ts文件
- `generate_document_structure_from_docs()`: 从现有项目生成文档结构（更新为支持i18n目录结构）
- `copy_english_to_docs()`: 将英文翻译从i18n/en目录复制到docs目录
- `push_to_github()`: 将更改推送到Github

### translator.py

负责使用百度翻译API翻译文档内容，保留Markdown格式。主要函数：

- `translate_text()`: 使用百度翻译API翻译文本
- `translate_markdown()`: 翻译Markdown内容，保留格式
- `create_translation_file_structure()`: 创建翻译文件结构
- `translate_document_structure()`: 翻译文档结构中的所有内容（更新为支持英文作为默认语言）

### llm_translator.py

负责使用Azure OpenAI API (GPT-4o)翻译文档内容，专门针对命理学术语进行优化。主要函数：

- `set_azure_openai_config()`: 设置Azure OpenAI API配置
- `generate_translation_prompt()`: 生成针对命理学内容的翻译提示词
- `translate_with_llm()`: 使用大模型翻译单个文件内容
- `extract_markdown_from_response()`: 从大模型响应中提取Markdown内容
- `translate_document_with_llm()`: 翻译整个文档结构中的所有内容（更新为支持英文作为默认语言）

### main.py

主程序入口，协调各个模块的工作。主要函数：

- `main()`: 主程序入口，按顺序执行各个步骤，支持命令行参数（更新为支持新的工作流程）

## 贡献指南

欢迎提交Issue和Pull Request来改进这个工具。在提交PR之前，请确保：

1. 代码符合PEP 8风格指南
2. 添加了必要的注释和文档
3. 通过了所有测试

## 许可证

MIT
