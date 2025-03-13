# translator.py
import os
import json
import time
import requests
from typing import Optional
from config import DOCUSAURUS_PATH, DOCS_PATH

# 百度翻译API配置
from file_generator import sanitize_filename

API_KEY = ""
SECRET_KEY = ""

# 支持的语言代码映射
LANGUAGE_CODES = {
    "en": "en",       # 英语
    "ja": "jp",       # 日语
    "ko": "kor",      # 韩语
    "zh-Hans": "zh",  # 简体中文
    "zh-Hant": "cht"  # 繁体中文
}

# Docusaurus语言代码到i18n目录的映射
DOCUSAURUS_LANGUAGE_PATHS = {
    "en": "en",
    "ja": "ja",
    "ko": "ko",
    "zh-Hans": "zh_cn",
    "zh-Hant": "zh_tw"
}

def set_baidu_api_keys(api_key: str, secret_key: str):
    """设置百度翻译API的密钥"""
    global API_KEY, SECRET_KEY
    API_KEY = api_key
    SECRET_KEY = secret_key

def get_access_token() -> Optional[str]:
    """
    获取百度翻译API的access token
    
    Returns:
        str: access token，如果出错则返回None
    """
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": API_KEY,
        "client_secret": SECRET_KEY
    }
    
    try:
        response = requests.post(url, params=params)
        result = response.json()
        return str(result.get("access_token"))
    except Exception as e:
        print(f"获取access token失败: {str(e)}")
        return None

def translate_text(text: str, from_lang: str = "zh", to_lang: str = "en", max_retries: int = 3) -> str:
    """
    使用百度翻译API翻译文本
    
    Args:
        text (str): 要翻译的文本
        from_lang (str): 源语言代码，默认为中文
        to_lang (str): 目标语言代码
        max_retries (int): 最大重试次数
        
    Returns:
        str: 翻译后的文本，如果翻译失败则返回原文本
    """
    if not API_KEY or not SECRET_KEY:
        raise ValueError("百度翻译API的密钥未设置，请在config.py中配置")
    
    # 如果文本为空，直接返回
    if not text or text.strip() == "":
        return ""
    
    # 将Docusaurus语言代码转换为百度翻译API的语言代码
    if to_lang in LANGUAGE_CODES:
        to_lang = LANGUAGE_CODES[to_lang]
    
    # 获取access token
    access_token = get_access_token()
    if not access_token:
        print("无法获取access token，返回原文本")
        return text
    
    # 百度翻译API接口
    url = f"https://aip.baidubce.com/rpc/2.0/mt/texttrans/v1?access_token={access_token}"
    
    # 构建请求数据
    payload = json.dumps({
        "from": from_lang,
        "to": to_lang,
        "q": text
    }, ensure_ascii=False)
    
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    for retry in range(max_retries):
        try:
            # 发送请求
            response = requests.post(
                url,
                headers=headers,
                data=payload.encode("utf-8"),
                timeout=10
            )
            result = response.json()
            
            # 检查是否有错误
            if "error_code" in result:
                error_msg = f"翻译失败，错误码: {result['error_code']}, 错误信息: {result.get('error_msg', '未知错误')}"
                print(error_msg)
                
                if retry < max_retries - 1:
                    print(f"等待后重试 ({retry + 1}/{max_retries})...")
                    time.sleep(2 ** retry)  # 指数退避
                    continue
                return text
            
            # 提取翻译结果
            if "result" in result and "trans_result" in result["result"]:
                translated_text = result["result"]["trans_result"][0]["dst"]
                
                # 为了避免API限制，添加短暂延迟
                time.sleep(0.5)
                
                return translated_text
            
            print(f"翻译返回格式异常: {result}")
            return text
            
        except Exception as e:
            print(f"翻译过程中发生错误: {str(e)}")
            
            if retry < max_retries - 1:
                print(f"等待后重试 ({retry + 1}/{max_retries})...")
                time.sleep(2 ** retry)  # 指数退避
                continue
            return text
    
    return text

class MarkdownSegment:
    """Markdown段落的分段类，用于存储文本和格式信息"""
    def __init__(self, text="", is_format=False, format_type=None):
        self.text = text  # 文本内容
        self.is_format = is_format  # 是否是格式标记
        self.format_type = format_type  # 格式类型：'bold', 'italic', 'code', 'format_prefix'

    def __str__(self):
        return f"MarkdownSegment(text='{self.text}', is_format={self.is_format}, format_type={self.format_type})"

def split_markdown_text(text):
    """
    将Markdown文本分割成纯文本和格式标记的段落
    """
    import re
    segments = []
    
    # 处理特殊格式前缀（如标题、列表项等）
    if is_special_markdown_format(text):
        format_prefix, content = extract_format_and_content(text)
        segments.append(MarkdownSegment(format_prefix, True, 'format_prefix'))
        text = content
    
    # 修改：使用非贪婪匹配来分割粗体、斜体和代码
    # 注意 pattern 中使用了非贪婪匹配 .*?
    pattern = r'(\*\*.*?\*\*|\*.*?\*|`.*?`)'
    
    # 使用 re.split 保留分隔符
    parts = re.split(f'({pattern})', text)
    
    for part in parts:
        if not part:  # 跳过空字符串
            continue
            
        # 检查是否是粗体
        if part.startswith('**') and part.endswith('**'):
            segments.append(MarkdownSegment(part, True, 'bold'))
        
        # 检查是否是斜体
        elif part.startswith('*') and part.endswith('*'):
            segments.append(MarkdownSegment(part, True, 'italic'))
        
        # 检查是否是代码
        elif part.startswith('`') and part.endswith('`'):
            segments.append(MarkdownSegment(part, True, 'code'))
        
        # 普通文本
        else:
            segments.append(MarkdownSegment(part, False))
    
    return segments

def translate_segments(segments, to_lang):
    """
    翻译MarkdownSegment列表中的纯文本段落
    """
    translated_segments = []
    
    for segment in segments:
        if segment.is_format:
            if segment.format_type == 'bold':
                # 提取粗体内容进行翻译
                content = segment.text[2:-2]  # 移除 ** 标记
                translated_content = translate_text(content, to_lang=to_lang)
                translated_segments.append(MarkdownSegment(f"**{translated_content}**", True, 'bold'))
            elif segment.format_type == 'italic':
                # 提取斜体内容进行翻译
                content = segment.text[1:-1]  # 移除 * 标记
                translated_content = translate_text(content, to_lang=to_lang)
                translated_segments.append(MarkdownSegment(f"*{translated_content}*", True, 'italic'))
            else:
                # 其他格式标记直接保留
                translated_segments.append(segment)
        else:
            # 纯文本段落需要翻译
            if segment.text.strip():  # 只翻译非空文本
                translated_text = translate_text(segment.text, to_lang=to_lang)
                translated_segments.append(MarkdownSegment(translated_text, False))
            else:
                # 空文本直接添加
                translated_segments.append(segment)
    
    return translated_segments

def combine_markdown_segments(segments):
    """
    将MarkdownSegment列表组合成Markdown文本
    
    Args:
        segments (list): MarkdownSegment对象列表
        
    Returns:
        str: 组合后的Markdown文本
    """
    return ''.join(segment.text for segment in segments)

def fix_markdown_format_errors(content: str) -> str:
    """
    修复翻译后的Markdown格式错误
    
    Args:
        content (str): 翻译后的Markdown内容
        
    Returns:
        str: 修复后的Markdown内容
    """
    import re
    
    # 修复错误的粗体格式
    # 匹配 "* text****" 这种格式的模式
    pattern = r'\* ([^*\n]+)\*{2,}'
    
    def fix_bold_format(match):
        # 将 "* text****" 转换为 "**text**"
        text = match.group(1).strip()
        return f"**{text}**"
    
    # 应用修复
    content = re.sub(pattern, fix_bold_format, content)
    
    # 修复多余的星号
    # 清理连续的星号（超过2个的）
    content = re.sub(r'\*{3,}', '**', content)
    
    # 修复列表项格式
    # 确保列表项使用单个减号且后面有空格
    content = re.sub(r'^(\s*)-(?!\s)', r'\1- ', content, flags=re.MULTILINE)
    
    # 修复可能的空格问题
    content = re.sub(r'\*\* ', r'**', content)
    content = re.sub(r' \*\*', r'**', content)
    
    # 修复换行问题
    content = re.sub(r'\*\*\n', r'**\n', content)
    
    # 修复粗体标记后缺少冒号的问题
    # 匹配以粗体结尾但后面没有冒号的行
    content = re.sub(r'(\*\*[^:\n]+\*\*)(?!:)([^\n]*)', r'\1:\2', content)
    
    # 修复减号后面的空格
    content = re.sub(r'(?m)^(\s*)-(?!\s)', r'\1- ', content)
    
    # 修复多余的冒号（避免出现双冒号）
    content = re.sub(r':+', r':', content)
    
    # 修复冒号后面的空格
    content = re.sub(r':(?!\s)', r': ', content)
    
    return content

def translate_markdown(markdown_content, to_lang):
    """
    翻译Markdown内容，保持格式和frontmatter不变
    """
    # 分离frontmatter和正文
    frontmatter, content = split_frontmatter(markdown_content)

    
    # 将Markdown内容分割成行
    lines = content.split("\n")
    
    # 翻译每一行
    translated_lines = []
    in_code_block = False
    
    # 标记是否已经处理过标题
    title_processed = False
    
    for line in lines:
        # print(f"line: {line}")
        # 跳过空行
        if not line.strip():
            translated_lines.append("")
            continue
        
        # 检查是否是代码块的开始或结束
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            translated_lines.append(line)
            continue
        
        # 如果在代码块内，不翻译
        if in_code_block:
            translated_lines.append(line)
            continue
        
        # 保存行首的空白字符（缩进）
        leading_spaces = ""
        for char in line:
            if char.isspace():
                leading_spaces += char
            else:
                break
        
        # 去除前导空格后的行
        stripped_line = line.strip()
        
        # 检查是否是列表项
        is_list_item = False
        list_marker = ""
        content_start = 0
        
        # 检查是否是无序列表项
        if stripped_line.startswith(("-", "*", "+")):
            is_list_item = True
            list_marker = stripped_line[0] + " "
            content_start = stripped_line.find(" ") + 1
        
        # 检查是否是有序列表项
        elif stripped_line and stripped_line[0].isdigit() and ". " in stripped_line:
            is_list_item = True
            dot_pos = stripped_line.find(". ")
            list_marker = stripped_line[:dot_pos+2]
            content_start = dot_pos + 2
        
        if is_list_item:
            # 提取列表项内容
            content = stripped_line[content_start:].strip()
            
            # 将内容分割成纯文本和格式标记
            segments = split_markdown_text(content)
            
            # 翻译纯文本段落
            translated_segments = translate_segments(segments, to_lang)
            
            # 重新组合成Markdown文本
            translated_content = combine_markdown_segments(translated_segments)
            
            # 重新组合成完整的列表项
            translated_line = leading_spaces + list_marker + translated_content
        else:
            # 将行分割成纯文本和格式标记
            segments = split_markdown_text(stripped_line)
            
            # 翻译纯文本段落
            translated_segments = translate_segments(segments, to_lang)
            
            # 重新组合成Markdown文本
            translated_content = combine_markdown_segments(translated_segments)
            
            # 添加回前导空格
            translated_line = leading_spaces + translated_content

        # print(f"translated_line: {translated_line}")
        
        translated_lines.append(translated_line)
    
    # 重新组合翻译后的内容，保留原始的行结构
    translated_content = "\n".join(translated_lines)
    
    # 修复格式错误
    translated_content = fix_markdown_format_errors(translated_content)
    
    # 确保frontmatter在最前面，后面跟着内容确保顺序正确：frontmatter -> 标题 -> 内容
    return f"{frontmatter}\n\n{translated_content}"

def split_frontmatter(markdown_content):
    """
    分离Markdown内容中的frontmatter和正文，确保frontmatter完整性
    
    Args:
        markdown_content (str): Markdown内容
        
    Returns:
        tuple: (frontmatter, content)
    """
    # 检查是否以"---"开头
    if not markdown_content.startswith("---"):
        return "", markdown_content
        
    try:
        # 查找第二个"---"
        parts = markdown_content.split("---", 2)
        if len(parts) >= 3:
            # 保留完整的frontmatter，确保格式正确（移除多余空格）
            frontmatter_content = parts[1].strip()
            frontmatter = f"---\n{frontmatter_content}\n---"
            # 提取正文部分并去除开头的空行
            content = parts[2].lstrip()
            return frontmatter, content
    except Exception as e:
        print(f"Warning: Error splitting frontmatter: {str(e)}")
        
    # 如果解析失败，返回空frontmatter和原始内容
    return "", markdown_content

def split_markdown_into_paragraphs(content):
    """
    将Markdown内容分割成段落
    
    Args:
        content (str): Markdown内容
        
    Returns:
        list: 段落列表
    """
    # 使用双换行符分割段落
    paragraphs = content.split("\n\n")
    
    # 过滤空段落
    return [p for p in paragraphs if p.strip()]

def is_code_block(paragraph):
    """
    检查段落是否是代码块
    
    Args:
        paragraph (str): 段落内容
        
    Returns:
        bool: 是否是代码块
    """
    # 检查是否是围栏式代码块（以```开头）
    if paragraph.strip().startswith("```"):
        return True
    
    # 检查是否是缩进式代码块（每行以至少4个空格或1个制表符开头）
    lines = paragraph.split("\n")
    if all(line.startswith("    ") or line.startswith("\t") for line in lines if line.strip()):
        return True
    
    return False

def is_special_markdown_format(paragraph):
    """
    检查段落是否是特殊的Markdown格式（如标题、列表项等）
    
    Args:
        paragraph (str): 段落内容
        
    Returns:
        bool: 是否是特殊格式
    """
    # 检查是否是标题（以#开头）
    if paragraph.strip().startswith("#"):
        return True
    
    # 检查是否是无序列表项（以-、*或+开头）
    if paragraph.strip().startswith(("-", "*", "+")):
        return True
    
    # 检查是否是有序列表项（以数字和点开头）
    if paragraph.strip() and paragraph.strip()[0].isdigit() and ". " in paragraph:
        return True
    
    # 检查是否是引用（以>开头）
    if paragraph.strip().startswith(">"):
        return True
    
    return False

def extract_format_and_content(paragraph):
    """
    从特殊格式的Markdown段落中提取格式标记和文本内容
    
    Args:
        paragraph (str): 段落内容
        
    Returns:
        tuple: (format_prefix, text_content)
    """
    # 标题
    if paragraph.strip().startswith("#"):
        # 计算#的数量
        heading_level = 0
        for char in paragraph:
            if char == "#":
                heading_level += 1
            else:
                break
        
        format_prefix = "#" * heading_level + " "
        text_content = paragraph.strip()[heading_level:].strip()
        return format_prefix, text_content
    
    # 无序列表项
    if paragraph.strip().startswith(("-", "*", "+")):
        marker = paragraph.strip()[0]
        format_prefix = marker + " "
        text_content = paragraph.strip()[2:].strip()
        return format_prefix, text_content
    
    # 有序列表项
    if paragraph.strip() and paragraph.strip()[0].isdigit() and ". " in paragraph:
        index = paragraph.find(". ")
        format_prefix = paragraph[:index+2]
        text_content = paragraph[index+2:].strip()
        return format_prefix, text_content
    
    # 引用
    if paragraph.strip().startswith(">"):
        format_prefix = "> "
        text_content = paragraph.strip()[2:].strip()
        return format_prefix, text_content
    
    # 默认情况
    return "", paragraph

def create_translation_file_structure(document_structure, target_languages=None):
    """
    为目标语言创建翻译文件结构
    
    Args:
        document_structure (dict): 解析后的文档结构
        target_languages (list): 目标语言代码列表，默认为None（使用所有支持的语言）
    """
    if target_languages is None:
        target_languages = list(DOCUSAURUS_LANGUAGE_PATHS.keys())
    
    print(f"开始为以下语言创建翻译文件结构: {', '.join(target_languages)}")
    
    for lang in target_languages:
        # 跳过中文（源语言）
        if lang == "zh-Hans":
            continue
        
        # 获取语言对应的i18n目录路径
        lang_path = DOCUSAURUS_LANGUAGE_PATHS.get(lang)
        if not lang_path:
            print(f"警告: 未找到语言 {lang} 的目录映射，跳过")
            continue
        
        i18n_docs_path = os.path.join(DOCUSAURUS_PATH, "i18n", lang_path, "docusaurus-plugin-content-docs", "current")
        
        # 确保i18n目录存在
        os.makedirs(i18n_docs_path, exist_ok=True)
        
        print(f"为语言 {lang} 创建翻译文件结构")
        
        # 遍历文档结构，为每个一级标题创建目录
        for level1_title, content_dict in document_structure.items():
            # 创建一级标题对应的目录
            category_name = level1_title
            category_path = os.path.join(i18n_docs_path, category_name)
            
            # 确保目录存在
            os.makedirs(category_path, exist_ok=True)
            
            # 创建_category_.json文件
            create_translated_category_json(category_path, category_name, lang)
            
            print(f"  已创建目录: {category_name}")

def create_translated_category_json(category_path, category_name, lang):
    """
    创建翻译后的分类_category_.json文件
    
    Args:
        category_path (str): 分类目录路径
        category_name (str): 分类名称
        lang (str): 目标语言代码
    """
    category_json_path = os.path.join(category_path, "_category_.json")
    
    # 翻译分类名称
    translated_name = translate_text(category_name, to_lang=lang)
    
    category_json_content = {
        "label": translated_name,
        "position": 2  # 可以根据需要调整位置
    }
    
    with open(category_json_path, 'w', encoding='utf-8') as f:
        json.dump(category_json_content, f, ensure_ascii=False, indent=2)

def translate_document_structure(document_structure, target_languages=None, force_translate=False):
    """
    翻译文档结构中的所有内容，包括文件名
    """
    if target_languages is None:
        target_languages = list(DOCUSAURUS_LANGUAGE_PATHS.keys())
    
    print(f"开始翻译文档内容为以下语言: {', '.join(target_languages)}")
    
    # 统计翻译信息
    translation_stats = {
        'total_files': 0,
        'skipped_files': 0,
        'translated_files': 0,
        'failed_files': 0
    }
    
    for lang in target_languages:
        # 跳过中文（源语言）
        if lang == "zh-Hans":
            continue
        
        # 获取语言对应的i18n目录路径
        lang_path = DOCUSAURUS_LANGUAGE_PATHS.get(lang)
        if not lang_path:
            print(f"警告: 未找到语言 {lang} 的目录映射，跳过")
            continue
        
        i18n_docs_path = os.path.join(DOCUSAURUS_PATH, "i18n", lang_path, "docusaurus-plugin-content-docs", "current")
        
        print(f"\n翻译文档内容为语言: {lang}")
        
        # 遍历文档结构，翻译每个文件
        for level1_title, content_dict in document_structure.items():
            # 翻译一级标题（目录名）
            translated_category = translate_text(level1_title, to_lang=lang)
            category_path = os.path.join(i18n_docs_path, sanitize_filename(translated_category))
            
            # 确保目录存在
            os.makedirs(category_path, exist_ok=True)
            
            # 创建翻译后的_category_.json文件
            create_translated_category_json(category_path, translated_category, lang)
            
            print(f"  已创建目录: {translated_category}")
            
            # 为每个内容项创建翻译后的markdown文件
            for title, content in content_dict.items():
                translation_stats['total_files'] += 1
                
                # 翻译文件标题
                translated_title = translate_text(title, to_lang=lang)
                file_name = sanitize_filename(translated_title) + ".md"
                file_path = os.path.join(category_path, file_name)
                
                # 检查文件是否已存在
                if os.path.exists(file_path) and not force_translate:
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            existing_content = f.read().strip()
                        if existing_content:
                            print(f"    - 跳过已存在的文件: {file_name}")
                            translation_stats['skipped_files'] += 1
                            continue
                    except Exception as e:
                        print(f"    - 现有文件 {file_name} 读取失败，将重新翻译: {str(e)}")
                
                try:
                    # 创建markdown文件内容，保留标题结构
                    if title.endswith(f"{level1_title}介绍"):
                        # 对于介绍文件，使用翻译后的一级标题
                        markdown_content = f"### {translated_category}\n\n{content}"
                    else:
                        # 对于其他文件，使用翻译后的标题
                        markdown_content = f"### {translated_title}\n\n{content}"
                    
                    # 翻译markdown内容
                    translated_content = translate_markdown(markdown_content, lang)
                    print(f"translated_content: {translated_content}")
                    # 删除文件前四行
                    translated_content = translated_content.split('\n', 4)[4]
                    print(f"translated_content: {translated_content}")
                    # 写入文件
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(translated_content)
                    
                    print(f"    - 已翻译文件: {file_name}")
                    translation_stats['translated_files'] += 1
                    
                except Exception as e:
                    print(f"    - 翻译文件 {file_name} 失败: {str(e)}")
                    translation_stats['failed_files'] += 1
            
            print(f"  目录 {translated_category} 翻译完成")
        
        print(f"\n语言 {lang} 翻译统计:")
        print(f"  - 总文件数: {translation_stats['total_files']}")
        print(f"  - 跳过文件数: {translation_stats['skipped_files']}")
        print(f"  - 成功翻译数: {translation_stats['translated_files']}")
        print(f"  - 翻译失败数: {translation_stats['failed_files']}")
    
    # 打印总体统计信息
    print("\n总体翻译统计:")
    print(f"总文件数: {translation_stats['total_files']}")
    print(f"跳过文件数: {translation_stats['skipped_files']}")
    print(f"成功翻译数: {translation_stats['translated_files']}")
    print(f"翻译失败数: {translation_stats['failed_files']}")
