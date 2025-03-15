import json
import os
import re
from pathlib import Path
import frontmatter

def load_json(file_path):
    """读取原始 JSON 文件"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"文件 {file_path} 未找到！")
        return None
    except json.JSONDecodeError:
        print(f"文件 {file_path} 不是有效的 JSON 格式！")
        return None

def simplify_structure(data):
    """递归删除 JSON 数据中的所有值，只保留目录结构"""
    if isinstance(data, dict):
        return {key: simplify_structure(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [simplify_structure(item) for item in data]
    else:
        return {} if isinstance(data, dict) else []

def normalize_path_name(name):
    """将JSON中的名称转换为实际文件系统中的名称"""
    # 替换中文括号
    name = name.replace('（', '_').replace('）', '_')
    # 替换英文括号
    name = name.replace('(', '_').replace(')', '_')
    # 替换空格
    name = name.replace(' ', '_')
    # 处理连续的下划线
    name = re.sub(r'_+', '_', name)
    # 移除首尾的下划线
    name = name.strip('_')
    return name

def ensure_category_json(dir_path, dir_name, position):
    """确保目录下有正确的_category_.json文件"""
    normalized_dir_name = normalize_path_name(dir_name)
    dir_full_path = os.path.join(dir_path, normalized_dir_name)
    
    # 只处理已存在的目录
    if not os.path.isdir(dir_full_path):
        # print(f"跳过不存在的目录: {dir_full_path}")
        return
        
    category_file = os.path.join(dir_full_path, '_category_.json')
    category_data = {
        "label": dir_name,  # 使用原始名称作为显示标签
        "position": position
    }
    
    # 检查是否存在_category_.json
    if os.path.exists(category_file):
        with open(category_file, 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
            if existing_data.get('position') != position:
                print(f"更新目录 {dir_name} 的位置: {existing_data.get('position')} -> {position}")
                existing_data['position'] = position
                with open(category_file, 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, ensure_ascii=False, indent=2)
            # else:
            #     print(f"目录 {dir_name} 的位置无需更新: {position}")
    else:
        print(f"创建目录 {dir_name} 的 _category_.json, 位置: {position}")
        with open(category_file, 'w', encoding='utf-8') as f:
            json.dump(category_data, f, ensure_ascii=False, indent=2)

def update_markdown_frontmatter(file_path, position):
    """更新markdown文件的frontmatter"""
    if not os.path.exists(file_path):
        # print(f"跳过不存在的文件: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析frontmatter
    post = frontmatter.loads(content)
    
    # 更新sidebar_position
    current_position = post.get('sidebar_position')
    if current_position != position:
        print(f"更新文件 {os.path.basename(file_path)} 的位置: {current_position} -> {position}")
        post['sidebar_position'] = position
        
        # 写回文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
    # else:
    #     print(f"文件 {os.path.basename(file_path)} 的位置无需更新: {position}")

def process_structure(structure, docs_path, parent_dir='', start_position=1):
    """处理目录结构"""
    print(f"\n处理目录: {docs_path}")
    for position, (name, content) in enumerate(structure.items(), start_position):
        normalized_name = normalize_path_name(name)
        
        # 判断是目录还是文件
        is_directory = isinstance(content, dict) and bool(content)  # 非空字典为目录
        
        if is_directory:
            # 处理目录
            current_dir = os.path.join(docs_path, normalized_name)
            if os.path.isdir(current_dir):
                print(f"\n--- 处理目录 {name} (位置 {position}) ---")
                # 创建或更新category.json
                ensure_category_json(docs_path, name, position)
                # 递归处理子目录
                process_structure(content, current_dir, start_position=1)
            # else:
            #     print(f"跳过不存在的目录: {current_dir}")
        else:
            # 处理文件（空字典或空列表的情况）
            md_file = os.path.join(docs_path, f"{normalized_name}.md")
            print(f"  处理文件: {name}.md (位置 {position})")
            update_markdown_frontmatter(md_file, position)

def check_and_fix_document_order(docusaurus_path):
    """检查并修正文档排序"""
    # 加载目录结构
    structure_file = "E:/Obsidian_space/HomeOfSherwen/Home_file/CanTianAI/feishu-docusaurus/document_structure.json"
    if not os.path.exists(structure_file):
        print(f"错误: 未找到文档结构文件 {structure_file}")
        return False

    original_data = load_json(structure_file)
    if original_data is None:
        return False
        
    # 简化数据结构
    simplified_structure = simplify_structure(original_data)
    
    # 处理主文档目录 (docs)
    docs_path = os.path.join(docusaurus_path, "docs")
    print("\n=== 处理主文档目录 (docs) ===")
    process_structure(simplified_structure, docs_path, start_position=2)  # intro.md 占据位置1
    
    # 处理翻译目录 (i18n)
    i18n_base = os.path.join(docusaurus_path, "i18n")
    if os.path.exists(i18n_base):
        languages = ['en', 'ja', 'ko', 'zh-Hans', 'zh-Hant']
        for lang in languages:
            lang_docs_path = os.path.join(i18n_base, lang, "docusaurus-plugin-content-docs", "current")
            if os.path.exists(lang_docs_path):
                print(f"\n=== 处理 {lang} 翻译目录 ===")
                process_structure(simplified_structure, lang_docs_path, start_position=2)  # intro.md 占据位置1
            # else:
                # print(f"跳过不存在的语言目录: {lang}")
    
    return True

def main():
    # 配置路径
    input_file = "document_structure.json"  # 原始JSON文件路径
    docs_path = 'E:/Obsidian_space/HomeOfSherwen/Home_file/CanTianAI/cantian-ai-wiki/docs'  # 实际的docs目录路径
    
    print(f"开始处理目录结构...")
    print(f"JSON文件: {input_file}")
    print(f"文档目录: {docs_path}\n")
    
    # 加载并简化目录结构
    original_data = load_json(input_file)
    if original_data is None:
        print("无法加载原始 JSON 数据，程序退出。")
        return
        
    # 简化数据结构
    simplified_structure = simplify_structure(original_data)
    
    # 处理目录结构
    process_structure(simplified_structure, docs_path)
    
    print("\n处理完成!")

if __name__ == "__main__":
    main()
