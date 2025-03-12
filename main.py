# main.py
import sys
import traceback
from feishu_api import get_document_content, debug_api_response
from document_parser import parse_document_content, extract_document_structure
from file_generator import generate_files, update_sidebar, backup_sidebar, push_to_github

def main():
    """
    主程序入口
    """
    try:
        print("开始从飞书获取《命理Tips》文档...")
        
        # 1. 获取文档内容
        doc_content = get_document_content()
        print("成功获取文档内容")
        
        # 调试输出API返回的JSON结构
        print("API返回的JSON结构如下:")
        debug_api_response(doc_content)
        
        # 2. 尝试使用两种方式解析文档内容
        try:
            # 首先尝试使用parse_document_content解析
            document_structure = parse_document_content(doc_content)
            print(f"成功解析文档结构，共有{len(document_structure)}个一级标题")
        except Exception as e:
            print(f"使用parse_document_content解析失败: {str(e)}")
            print("尝试使用extract_document_structure解析...")
            
            # 如果失败，尝试使用extract_document_structure解析
            markdown_content = extract_document_structure(doc_content)
            print("成功提取文档内容，但需要手动解析结构")
            
            # 将提取的markdown内容保存到文件，以便手动处理
            with open("extracted_content.md", "w", encoding="utf-8") as f:
                f.write(markdown_content)
            
            print("已将提取的内容保存到extracted_content.md文件，请手动处理")
            sys.exit(1)
        
        # 3. 备份sidebars.ts文件
        backup_sidebar()
        
        # 4. 生成目录和文件
        generate_files(document_structure)
        print("成功生成目录和文件")
        
        # # 5. 更新Docusaurus配置
        # update_sidebar(document_structure)
        # print("成功更新Docusaurus配置")
        
        # # 6. 推送到Github
        # if push_to_github():
        #     print("整个过程已成功完成，更改已推送到Github")
        # else:
        #     print("整个过程已完成，但推送到Github失败，请手动推送")
        
    except Exception as e:
        print(f"程序执行过程中发生错误: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
