# document_parser.py
import json
import re


def parse_document_content(doc_content):
    """
    解析飞书文档内容，提取标题和正文
    
    Args:
        doc_content (dict): 飞书API返回的文档内容
        
    Returns:
        dict: 解析后的文档结构，格式为：
        {
            "二级标题1": {
                "三级标题1": "内容1",
                "三级标题2": "内容2",
                ...
            },
            "二级标题2": {
                ...
            },
            ...
        }
    """
    # 获取文档内容
    # 从API返回的JSON中提取content字段
    content = doc_content.get("data", {}).get("content", "")
    # 将content直接保存为markdown文件

    if not content:
        raise ValueError("文档内容为空")
    
    print(f"成功获取文档内容，长度为{len(content)}字符")
    
    # 解析文档结构
    document_structure = {}
    current_level2_title = None
    current_level3_title = None
    current_content = []
    
    # 将内容按行分割
    lines = content.split("\n")
    
    for line in lines:
        # 检查是否为二级标题
        if line.startswith("## "):
            # 如果已经有内容，保存之前的内容
            if current_level2_title and current_level3_title and current_content:
                if current_level2_title not in document_structure:
                    document_structure[current_level2_title] = {}
                document_structure[current_level2_title][current_level3_title] = "\n".join(current_content)
                current_content = []
            
            # 设置新的二级标题
            current_level2_title = line[3:].strip()
            current_level3_title = None
            print(f"发现二级标题: {current_level2_title}")
            
        # 检查是否为三级标题
        elif line.startswith("### "):
            # 如果已经有内容，保存之前的内容
            if current_level2_title and current_level3_title and current_content:
                if current_level2_title not in document_structure:
                    document_structure[current_level2_title] = {}
                document_structure[current_level2_title][current_level3_title] = "\n".join(current_content)
                current_content = []
            
            # 设置新的三级标题
            current_level3_title = line[4:].strip()
            print(f"  发现三级标题: {current_level3_title}")
            
        # 如果不是标题，则为内容
        elif current_level2_title and current_level3_title:
            current_content.append(line)
    
    # 保存最后一部分内容
    if current_level2_title and current_level3_title and current_content:
        if current_level2_title not in document_structure:
            document_structure[current_level2_title] = {}
        document_structure[current_level2_title][current_level3_title] = "\n".join(current_content)
    
    print(f"文档解析完成，共有{len(document_structure)}个二级标题")
    for level2_title, level3_dict in document_structure.items():
        print(f"- {level2_title}: {len(level3_dict)}个三级标题")
    
    return document_structure

def clean_markdown_content(content):
    """
    清理markdown内容，处理特殊字符和格式
    
    Args:
        content (str): 原始markdown内容
        
    Returns:
        str: 清理后的markdown内容
    """
    # 处理可能的HTML实体
    content = content.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
    
    # 处理可能的多余空行
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    return content

def extract_document_structure(doc_content):
    """
    从飞书文档API返回的JSON中提取文档结构
    
    这个函数处理飞书文档API的特定JSON结构，提取出文档的标题和内容
    
    Args:
        doc_content (dict): 飞书API返回的文档内容
        
    Returns:
        str: 提取出的markdown格式文档内容
    """
    try:
        # 这里需要根据实际的飞书API返回结构进行调整
        # 以下是一个示例，实际结构可能不同
        content = doc_content.get("data", {}).get("content", "")
        if isinstance(content, dict):
            # 如果content是一个复杂的JSON对象，需要进一步解析
            # 这里需要根据实际返回的结构编写解析逻辑
            # 以下是一个简化的示例
            if "blocks" in content:
                blocks = content["blocks"]
                markdown_content = ""
                for block in blocks:
                    if block.get("type") == "heading" and block.get("heading", {}).get("level") == 2:
                        markdown_content += f"## {block['heading']['content']}\n\n"
                    elif block.get("type") == "heading" and block.get("heading", {}).get("level") == 3:
                        markdown_content += f"### {block['heading']['content']}\n\n"
                    elif block.get("type") == "text":
                        markdown_content += f"{block['text']['content']}\n\n"
                return markdown_content
            else:
                # 如果没有blocks字段，可能是其他结构
                return json.dumps(content, ensure_ascii=False, indent=2)
        else:
            # 如果content是字符串，直接返回
            return content
    except Exception as e:
        print(f"解析文档结构时发生错误: {str(e)}")
        # 如果解析失败，返回原始JSON字符串
        return json.dumps(doc_content, ensure_ascii=False, indent=2)
