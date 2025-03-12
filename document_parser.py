# document_parser.py
import json
import re
import traceback

def save_to_markdown_file(markdown_content, filename="output.md"):
    """
    将 Markdown 内容保存到文件
    """
    with open(filename, "w", encoding="utf-8") as file:
        file.write(markdown_content)
    print(f"Markdown 文件已保存为：{filename}")


def get_text_content(text_obj):
    """
    从Text对象中提取文本内容
    
    Args:
        text_obj: 可能是Text对象或者包含Text对象的字典
        
    Returns:
        str: 提取的文本内容
    """
    if text_obj is None:
        return ""
    
    # 如果是Text对象
    if hasattr(text_obj, 'elements'):
        elements = text_obj.elements
        if elements:
            content = ""
            for elem in elements:
                if hasattr(elem, 'text_run') and elem.text_run:
                    if hasattr(elem.text_run, 'content'):
                        content += elem.text_run.content
            return content
    
    # 如果是字典
    if isinstance(text_obj, dict):
        if 'elements' in text_obj:
            elements = text_obj['elements']
            if elements:
                content = ""
                for elem in elements:
                    if 'text_run' in elem and elem['text_run']:
                        if 'content' in elem['text_run']:
                            content += elem['text_run']['content']
                return content
    
    # 如果是字符串
    if isinstance(text_obj, str):
        return text_obj
    
    # 其他情况
    return str(text_obj)


def parse_document_content(doc_content):
    """
    解析飞书文档内容，提取标题和正文
    
    Args:
        doc_content (dict): 飞书API返回的文档内容
        
    Returns:
        dict: 解析后的文档结构，格式为：
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
    try:
        # 获取文档块列表
        if isinstance(doc_content, dict) and 'items' in doc_content:
            blocks = doc_content['items']
        elif hasattr(doc_content, 'items'):
            blocks = doc_content.items
        else:
            raise ValueError("无法获取文档块列表")
        
        # 打印前几个块的信息，用于调试
        print(f"文档共有 {len(blocks)} 个块")
        
        # 构建块ID到块的映射
        block_map = {}
        root_block = None
        
        for block in blocks:
            # 获取block_id
            block_id = None
            if isinstance(block, dict) and 'block_id' in block:
                block_id = block['block_id']
            elif hasattr(block, 'block_id'):
                block_id = block.block_id
            
            if not block_id:
                continue
                
            # 添加到block_map
            block_map[block_id] = block
            
            # 获取parent_id
            parent_id = None
            if isinstance(block, dict) and 'parent_id' in block:
                parent_id = block['parent_id']
            elif hasattr(block, 'parent_id'):
                parent_id = block.parent_id
            
            # 如果是根节点
            if parent_id == '':
                root_block = block
        
        if not root_block:
            raise ValueError("找不到文档根节点")
        
        # 获取根节点ID
        root_id = None
        if isinstance(root_block, dict) and 'block_id' in root_block:
            root_id = root_block['block_id']
        elif hasattr(root_block, 'block_id'):
            root_id = root_block.block_id
        
        if not root_id:
            raise ValueError("根节点没有block_id")
        
        # 获取根节点标题
        root_title = "命理Tips"  # 默认标题
        
        # 解析文档结构
        document_structure = {}
        
        # 收集所有一级标题（block_type=4）
        level1_titles = {}
        # 收集所有二级标题（block_type=5）
        level2_titles = {}
        # 收集所有代码块（block_type=14）
        code_blocks = {}
        
        # 第一遍遍历：收集所有标题和代码块
        for block in blocks:
            # 跳过根节点
            if isinstance(block, dict) and block.get('block_id') == root_id:
                continue
            elif hasattr(block, 'block_id') and block.block_id == root_id:
                continue
            
            # 获取block_type
            block_type = None
            if isinstance(block, dict) and 'block_type' in block:
                block_type = block['block_type']
            elif hasattr(block, 'block_type'):
                block_type = block.block_type
            
            # 获取parent_id
            parent_id = None
            if isinstance(block, dict) and 'parent_id' in block:
                parent_id = block['parent_id']
            elif hasattr(block, 'parent_id'):
                parent_id = block.parent_id
            
            # 只处理直接挂在根节点下的块
            if parent_id != root_id:
                continue
            
            # 获取block_id
            block_id = None
            if isinstance(block, dict) and 'block_id' in block:
                block_id = block['block_id']
            elif hasattr(block, 'block_id'):
                block_id = block.block_id
            
            # 一级标题（block_type=4）
            if block_type == 4:
                title_text = ""
                if isinstance(block, dict) and 'heading2' in block:
                    if isinstance(block['heading2'], dict) and 'elements' in block['heading2']:
                        for elem in block['heading2']['elements']:
                            if 'text_run' in elem and 'content' in elem['text_run']:
                                title_text += elem['text_run']['content']
                    else:
                        title_text = get_text_content(block['heading2'])
                elif hasattr(block, 'heading2'):
                    if hasattr(block.heading2, 'elements'):
                        for elem in block.heading2.elements:
                            if hasattr(elem, 'text_run') and hasattr(elem.text_run, 'content'):
                                title_text += elem.text_run.content
                    else:
                        title_text = get_text_content(block.heading2)
                
                if title_text:
                    level1_titles[block_id] = title_text
                    print(f"找到一级标题: {title_text}")
                    # 初始化一级标题的内容字典
                    document_structure[title_text] = {}
            
            # 二级标题（block_type=5）
            elif block_type == 5:
                title_text = ""
                if isinstance(block, dict) and 'heading3' in block:
                    if isinstance(block['heading3'], dict) and 'elements' in block['heading3']:
                        for elem in block['heading3']['elements']:
                            if 'text_run' in elem and 'content' in elem['text_run']:
                                title_text += elem['text_run']['content']
                    else:
                        title_text = get_text_content(block['heading3'])
                elif hasattr(block, 'heading3'):
                    if hasattr(block.heading3, 'elements'):
                        for elem in block.heading3.elements:
                            if hasattr(elem, 'text_run') and hasattr(elem.text_run, 'content'):
                                title_text += elem.text_run.content
                    else:
                        title_text = get_text_content(block.heading3)
                
                if title_text:
                    level2_titles[block_id] = title_text
                    print(f"  找到二级标题: {title_text}")
            
            # 代码块（block_type=14）
            elif block_type == 14:
                code_text = ""
                if isinstance(block, dict) and 'code' in block:
                    if isinstance(block['code'], dict) and 'elements' in block['code']:
                        for elem in block['code']['elements']:
                            if 'text_run' in elem and 'content' in elem['text_run']:
                                code_text += elem['text_run']['content']
                    else:
                        code_text = get_text_content(block['code'])
                elif hasattr(block, 'code'):
                    if hasattr(block.code, 'elements'):
                        for elem in block.code.elements:
                            if hasattr(elem, 'text_run') and hasattr(elem.text_run, 'content'):
                                code_text += elem.text_run.content
                    else:
                        code_text = get_text_content(block.code)
                
                if code_text:
                    code_blocks[block_id] = code_text
        
        # 第二遍遍历：将二级标题和代码块关联到一级标题
        # 根据块的顺序来确定关联关系
        current_level1_title = None
        current_level2_title = None
        
        for block in blocks:
            # 跳过根节点
            if isinstance(block, dict) and block.get('block_id') == root_id:
                continue
            elif hasattr(block, 'block_id') and block.block_id == root_id:
                continue
            
            # 获取block_id
            block_id = None
            if isinstance(block, dict) and 'block_id' in block:
                block_id = block['block_id']
            elif hasattr(block, 'block_id'):
                block_id = block.block_id
            
            # 获取parent_id
            parent_id = None
            if isinstance(block, dict) and 'parent_id' in block:
                parent_id = block['parent_id']
            elif hasattr(block, 'parent_id'):
                parent_id = block.parent_id
            
            # 只处理直接挂在根节点下的块
            if parent_id != root_id:
                continue
            
            # 获取block_type
            block_type = None
            if isinstance(block, dict) and 'block_type' in block:
                block_type = block['block_type']
            elif hasattr(block, 'block_type'):
                block_type = block.block_type
            
            # 一级标题（block_type=4）
            if block_type == 4 and block_id in level1_titles:
                current_level1_title = level1_titles[block_id]
                current_level2_title = None
            
            # 二级标题（block_type=5）
            elif block_type == 5 and block_id in level2_titles:
                current_level2_title = level2_titles[block_id]
                
                # 如果有当前一级标题，将二级标题添加到一级标题下
                if current_level1_title:
                    document_structure[current_level1_title][current_level2_title] = ""
            
            # 代码块（block_type=14）
            elif block_type == 14 and block_id in code_blocks:
                code_text = code_blocks[block_id]
                
                # 如果有当前二级标题，将代码块添加到二级标题下
                if current_level1_title and current_level2_title:
                    if document_structure[current_level1_title][current_level2_title]:
                        document_structure[current_level1_title][current_level2_title] += f"\n\n{code_text}"
                    else:
                        document_structure[current_level1_title][current_level2_title] = code_text
                # 如果只有一级标题，将代码块添加到一级标题的"介绍"下
                elif current_level1_title:
                    intro_key = f"{current_level1_title}介绍"
                    if intro_key not in document_structure[current_level1_title]:
                        document_structure[current_level1_title][intro_key] = code_text
                    else:
                        document_structure[current_level1_title][intro_key] += f"\n\n{code_text}"
            
            # 文本段落（block_type=2）
            elif block_type == 2:
                para_text = ""
                if isinstance(block, dict) and 'text' in block:
                    if isinstance(block['text'], dict) and 'elements' in block['text']:
                        for elem in block['text']['elements']:
                            if 'text_run' in elem and 'content' in elem['text_run']:
                                para_text += elem['text_run']['content']
                    else:
                        para_text = get_text_content(block['text'])
                elif hasattr(block, 'text'):
                    if hasattr(block.text, 'elements'):
                        for elem in block.text.elements:
                            if hasattr(elem, 'text_run') and hasattr(elem.text_run, 'content'):
                                para_text += elem.text_run.content
                    else:
                        para_text = get_text_content(block.text)
                
                if para_text and current_level1_title:
                    # 如果有当前二级标题，将段落添加到二级标题下
                    if current_level2_title:
                        if document_structure[current_level1_title][current_level2_title]:
                            document_structure[current_level1_title][current_level2_title] += f"\n\n{para_text}"
                        else:
                            document_structure[current_level1_title][current_level2_title] = para_text
                    # 如果只有一级标题，将段落添加到一级标题的"介绍"下
                    else:
                        intro_key = f"{current_level1_title}介绍"
                        if intro_key not in document_structure[current_level1_title]:
                            document_structure[current_level1_title][intro_key] = para_text
                        else:
                            document_structure[current_level1_title][intro_key] += f"\n\n{para_text}"
        
        return document_structure
        
    except Exception as e:
        print(f"解析文档内容时发生错误: {str(e)}")
        traceback.print_exc()
        raise


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
    提取文档结构为简单的文本格式，用于调试
    """
    try:
        # 创建一个简单的文本表示
        result = []
        
        # 获取文档块列表
        if isinstance(doc_content, dict) and 'items' in doc_content:
            blocks = doc_content['items']
        elif hasattr(doc_content, 'items'):
            blocks = doc_content.items
        else:
            return "无法获取文档块列表"
        
        result.append(f"文档共有 {len(blocks)} 个块")
        
        # 只处理前10个块，避免输出过多
        for i, block in enumerate(blocks[:10]):
            result.append(f"\n--- 块 {i+1} ---")
            
            # 获取block_id
            if isinstance(block, dict) and 'block_id' in block:
                result.append(f"block_id: {block['block_id']}")
            elif hasattr(block, 'block_id'):
                result.append(f"block_id: {block.block_id}")
            
            # 获取block_type
            if isinstance(block, dict) and 'block_type' in block:
                result.append(f"block_type: {block['block_type']}")
            elif hasattr(block, 'block_type'):
                result.append(f"block_type: {block.block_type}")
            
            # 获取parent_id
            if isinstance(block, dict) and 'parent_id' in block:
                result.append(f"parent_id: {block['parent_id']}")
            elif hasattr(block, 'parent_id'):
                result.append(f"parent_id: {block.parent_id}")
            
            # 尝试获取内容
            content = None
            
            # 检查是否为页面
            if isinstance(block, dict) and 'page' in block and block['page']:
                content = get_text_content(block['page'])
            elif hasattr(block, 'page') and block.page:
                content = get_text_content(block.page)
            
            # 检查是否为二级标题
            elif isinstance(block, dict) and 'heading2' in block and block['heading2']:
                content = get_text_content(block['heading2'])
            elif hasattr(block, 'heading2') and block.heading2:
                content = get_text_content(block.heading2)
            
            # 检查是否为三级标题
            elif isinstance(block, dict) and 'heading3' in block and block['heading3']:
                content = get_text_content(block['heading3'])
            elif hasattr(block, 'heading3') and block.heading3:
                content = get_text_content(block.heading3)
            
            # 检查是否为文本段落
            elif isinstance(block, dict) and 'text' in block and block['text']:
                content = get_text_content(block['text'])
            elif hasattr(block, 'text') and block.text:
                content = get_text_content(block.text)
            
            # 检查是否为代码块
            elif isinstance(block, dict) and 'code' in block and block['code']:
                content = get_text_content(block['code'])
            elif hasattr(block, 'code') and block.code:
                content = get_text_content(block.code)
            
            if content:
                # 截断过长的内容
                if len(content) > 100:
                    content = content[:100] + "..."
                result.append(f"内容: {content}")
        
        if len(blocks) > 10:
            result.append(f"\n... 还有 {len(blocks) - 10} 个块未显示 ...")
        
        return "\n".join(result)
        
    except Exception as e:
        print(f"提取文档结构时发生错误: {str(e)}")
        traceback.print_exc()
        return f"提取文档结构时发生错误: {str(e)}"
