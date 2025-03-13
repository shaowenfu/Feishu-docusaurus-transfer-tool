# main.py
import sys
import traceback
import argparse
from feishu_api import get_document_content, debug_api_response
from document_parser import parse_document_content, extract_document_structure
from file_generator import generate_files, update_sidebar, backup_sidebar, push_to_github, generate_document_structure_from_docs
from translator import set_baidu_api_keys, create_translation_file_structure, translate_document_structure
from config import BAIDU_APP_ID, BAIDU_SECRET_KEY, TARGET_LANGUAGES

def main():
    """
    主程序入口
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='飞书文档迁移到Docusaurus工具')
    parser.add_argument('--no-translate', action='store_true', help='不执行翻译步骤')
    parser.add_argument('--only-translate', action='store_true', help='只执行翻译步骤，不从飞书获取文档')
    parser.add_argument('--generate-structure', action='store_true', help='从现有的Docusaurus项目中生成文档结构')
    parser.add_argument('--force-translate', action='store_true', help='强制重新翻译所有文件，包括已存在的文件')
    parser.add_argument('--baidu-app-id', help='百度翻译API的APP ID')
    parser.add_argument('--baidu-secret-key', help='百度翻译API的密钥')
    parser.add_argument('--languages', help='要翻译的目标语言，用逗号分隔，例如：en,ja,ko')
    args = parser.parse_args()
    
    # 设置百度翻译API密钥
    baidu_app_id = args.baidu_app_id or BAIDU_APP_ID
    baidu_secret_key = args.baidu_secret_key or BAIDU_SECRET_KEY
    
    # 设置目标语言
    target_languages = TARGET_LANGUAGES
    if args.languages:
        target_languages = args.languages.split(',')
    
    # 如果提供了百度翻译API密钥，设置它们
    if baidu_app_id != "YOUR_BAIDU_APP_ID" and baidu_secret_key != "YOUR_BAIDU_SECRET_KEY":
        set_baidu_api_keys(baidu_app_id, baidu_secret_key)
    
    try:
        # 如果需要从现有的Docusaurus项目中生成文档结构
        if args.generate_structure:
            print("从现有的Docusaurus项目中生成文档结构...")
            
            # 生成文档结构
            document_structure = generate_document_structure_from_docs()
            
            # 保存文档结构到本地文件
            import json
            with open("document_structure.json", "w", encoding="utf-8") as f:
                json.dump(document_structure, f, ensure_ascii=False, indent=2)
            print(f"成功从现有的Docusaurus项目中生成文档结构，共有{len(document_structure)}个一级标题")
            print("已将文档结构保存到document_structure.json文件")
            
            # 如果只是生成文档结构，不执行翻译步骤，则退出
            if args.no_translate:
                print("已完成文档结构生成，跳过翻译步骤")
                sys.exit(0)
        
        # 如果只执行翻译步骤
        if args.only_translate or args.generate_structure:
            if not args.generate_structure:
                print("只执行翻译步骤，跳过从飞书获取文档...")
            
            # 从本地文件加载文档结构
            try:
                import json
                with open("document_structure.json", "r", encoding="utf-8") as f:
                    document_structure = json.load(f)
                print(f"成功从本地文件加载文档结构，共有{len(document_structure)}个一级标题")
            except Exception as e:
                print(f"从本地文件加载文档结构失败: {str(e)}")
                print("请先运行程序获取文档内容并生成文件，或使用--generate-structure选项从现有的Docusaurus项目中生成文档结构")
                sys.exit(1)
            
            # 执行翻译步骤
            if not args.no_translate:
                # 检查百度翻译API密钥是否已设置
                if baidu_app_id == "YOUR_BAIDU_APP_ID" or baidu_secret_key == "YOUR_BAIDU_SECRET_KEY":
                    print("警告: 百度翻译API密钥未设置，无法执行翻译步骤")
                    print("请在config.py中设置BAIDU_APP_ID和BAIDU_SECRET_KEY，或使用--baidu-app-id和--baidu-secret-key参数")
                    sys.exit(1)
                
                
                # 翻译文档内容
                translate_document_structure(document_structure, target_languages, force_translate=args.force_translate)
                print("成功翻译文档内容")
            
            print("翻译步骤已完成")
            return
        
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
            
            # 保存文档结构到本地文件，以便后续使用
            import json
            with open("document_structure.json", "w", encoding="utf-8") as f:
                json.dump(document_structure, f, ensure_ascii=False, indent=2)
            print("已将文档结构保存到document_structure.json文件")
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
        
        # 5. 更新Docusaurus配置
        update_sidebar(document_structure)
        print("成功更新Docusaurus配置")
        
        # 6. 执行翻译步骤
        if not args.no_translate:
            # 检查百度翻译API密钥是否已设置
            if baidu_app_id == "YOUR_BAIDU_APP_ID" or baidu_secret_key == "YOUR_BAIDU_SECRET_KEY":
                print("警告: 百度翻译API密钥未设置，跳过翻译步骤")
                print("请在config.py中设置BAIDU_APP_ID和BAIDU_SECRET_KEY，或使用--baidu-app-id和--baidu-secret-key参数")
            else:
                # 创建翻译文件结构
                create_translation_file_structure(document_structure, target_languages)
                print("成功创建翻译文件结构")
                
                # 翻译文档内容
                translate_document_structure(document_structure, target_languages, force_translate=args.force_translate)
                print("成功翻译文档内容")
        
        # # 7. 推送到Github
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
