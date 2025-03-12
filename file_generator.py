# file_generator.py
import os
import re
import json
import subprocess
from config import DOCS_PATH, SIDEBAR_PATH, DOCUSAURUS_PATH

def sanitize_filename(name):
    """
    清理文件名，移除不合法字符
    
    Args:
        name (str): 原始文件名
        
    Returns:
        str: 清理后的文件名
    """
    # 移除不合法字符，只保留字母、数字、下划线、连字符和点
    name = re.sub(r'[^\w\-\.]', '_', name)
    return name

def create_category_json(category_path, category_name):
    """
    创建分类的_category_.json文件
    
    Args:
        category_path (str): 分类目录路径
        category_name (str): 分类名称
    """
    category_json_path = os.path.join(category_path, "_category_.json")
    
    category_json_content = {
        "label": category_name,
        "position": 2  # 可以根据需要调整位置
    }
    
    with open(category_json_path, 'w', encoding='utf-8') as f:
        json.dump(category_json_content, f, ensure_ascii=False, indent=2)

def generate_files(document_structure):
    """
    根据文档结构生成目录和文件
    
    Args:
        document_structure (dict): 解析后的文档结构，格式为：
        {
            "一级标题1": {
                "介绍": "一级标题下的段落内容",
                "二级标题1": "二级标题下的段落内容",
                "二级标题2": "二级标题下的段落内容",
                ...
            },
            "一级标题2": {
                ...
            },
            ...
        }
    """
    print(f"开始生成目录和文件，文档结构包含 {len(document_structure)} 个一级标题")
    
    for level1_title, content_dict in document_structure.items():
        # 创建一级标题对应的目录
        category_name = level1_title
        category_path = os.path.join(DOCS_PATH, sanitize_filename(category_name))
        
        # 确保目录存在
        os.makedirs(category_path, exist_ok=True)
        
        # 创建_category_.json文件
        create_category_json(category_path, category_name)
        
        print(f"已创建目录: {category_name}")
        
        # 为每个内容项创建markdown文件
        for title, content in content_dict.items():
            # 如果标题是"XX介绍"格式，表示是一级标题下的直接段落
            is_intro = title.endswith(f"{level1_title}介绍")
            
            # 创建文件名
            file_name = sanitize_filename(title) + ".md"
            file_path = os.path.join(category_path, file_name)
            
            # 创建markdown文件内容
            if is_intro:
                # 对于介绍文件，使用一级标题作为标题
                markdown_content = f"# {level1_title}\n\n{content}"
            else:
                # 对于二级标题文件，使用二级标题作为标题
                markdown_content = f"# {title}\n\n{content}"
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"  - 已创建文件: {file_name}")
        
        print(f"目录 {category_name} 下共创建了 {len(content_dict)} 个文件")

def update_sidebar(document_structure):
    """
    更新Docusaurus的sidebars.ts文件
    
    Args:
        document_structure (dict): 解析后的文档结构
    """
    try:
        # 读取现有的sidebars.ts文件
        with open(SIDEBAR_PATH, 'r', encoding='utf-8') as f:
            sidebar_content = f.read()
        
        # 构建新的侧边栏项
        new_sidebar_items = []
        
        for level2_title in document_structure.keys():
            category_name = sanitize_filename(level2_title)
            new_sidebar_items.append(f"    '{category_name}',")
        
        # 将新项添加到sidebars.ts文件中
        # 查找tutorialSidebar数组的结束位置
        match = re.search(r'tutorialSidebar:\s*\[([\s\S]*?)\]', sidebar_content)
        
        if match:
            # 获取现有的侧边栏项
            existing_items = match.group(1).strip()
            
            # 检查新项是否已经存在
            new_items_to_add = []
            for item in new_sidebar_items:
                item_name = item.strip().strip(',').strip("'")
                if item_name not in existing_items:
                    new_items_to_add.append(item)
            
            # 如果有新项要添加
            if new_items_to_add:
                # 构建新的侧边栏内容
                if existing_items:
                    # 如果已有项，在最后一项后添加新项
                    new_sidebar_content = sidebar_content.replace(
                        match.group(0),
                        f"tutorialSidebar: [{existing_items},\n{''.join(new_items_to_add)}\n  ]"
                    )
                else:
                    # 如果没有现有项，直接添加新项
                    new_sidebar_content = sidebar_content.replace(
                        match.group(0),
                        f"tutorialSidebar: [\n{''.join(new_items_to_add)}\n  ]"
                    )
                
                # 写入更新后的内容
                with open(SIDEBAR_PATH, 'w', encoding='utf-8') as f:
                    f.write(new_sidebar_content)
                
                print(f"已更新sidebars.ts文件，添加了{len(new_items_to_add)}个新分类")
            else:
                print("所有分类已存在于sidebars.ts文件中，无需更新")
        else:
            print("无法在sidebars.ts文件中找到tutorialSidebar数组，请手动更新")
    except Exception as e:
        print(f"更新sidebars.ts文件时发生错误: {str(e)}")
        print("请手动更新sidebars.ts文件")

def backup_sidebar():
    """
    备份sidebars.ts文件
    """
    import shutil
    backup_path = SIDEBAR_PATH + ".bak"
    shutil.copy2(SIDEBAR_PATH, backup_path)
    print(f"已备份sidebars.ts文件到 {backup_path}")

def push_to_github():
    """
    将更改推送到Github
    
    Returns:
        bool: 是否成功推送
    """
    try:
        # 切换到Docusaurus项目目录
        os.chdir(DOCUSAURUS_PATH)
        
        # 先拉取最新代码
        subprocess.run(["git", "pull"], check=True)
        
        # 添加所有更改
        subprocess.run(["git", "add", "."], check=True)
        
        # 提交更改
        commit_message = "Add 命理Tips documents from Feishu"
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        
        # 推送到Github
        subprocess.run(["git", "push"], check=True)
        
        print("已成功推送更改到Github")
        return True
    except subprocess.CalledProcessError as e:
        print(f"推送到Github时发生错误: {str(e)}")
        print("请按以下步骤手动推送:")
        print("1. 打开命令行，进入项目目录")
        print(f"2. 执行: cd {DOCUSAURUS_PATH}")
        print("3. 执行: git add .")
        print("4. 执行: git commit -m \"Add 命理Tips documents from Feishu\"")
        print("5. 执行: git push")
        return False
    except Exception as e:
        print(f"推送到Github时发生未知错误: {str(e)}")
        return False
