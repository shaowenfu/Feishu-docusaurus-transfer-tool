# main.py
import sys
import traceback
import argparse
import os
from feishu_api import get_document_content, debug_api_response
from document_parser import parse_document_content, extract_document_structure
from file_generator import generate_files, update_sidebar, backup_sidebar, push_to_github, generate_document_structure_from_docs, copy_english_to_docs
from translator import set_baidu_api_keys, create_translation_file_structure, translate_document_structure
from llm_translator import set_azure_openai_config, translate_document_with_llm
from config import BAIDU_APP_ID, BAIDU_SECRET_KEY, TARGET_LANGUAGES, DOCUSAURUS_PATH, DOCS_PATH

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
    
    # 百度翻译API参数
    parser.add_argument('--baidu-app-id', help='百度翻译API的APP ID')
    parser.add_argument('--baidu-secret-key', help='百度翻译API的密钥')
    
    # Azure OpenAI API参数
    parser.add_argument('--use-llm', action='store_true', help='使用大模型(GPT-4o)进行翻译，而不是百度翻译API')
    parser.add_argument('--azure-endpoint', help='Azure OpenAI API的端点URL')
    parser.add_argument('--azure-api-key', help='Azure OpenAI API的密钥')
    parser.add_argument('--azure-deployment', default='gpt-4o', help='Azure OpenAI API的部署名称，默认为gpt-4o')
    
    parser.add_argument('--languages', help='要翻译的目标语言，用逗号分隔，例如：en,ja,ko。默认翻译为日文、韩文、英文、繁体中文、简体中文')
    parser.add_argument('--fix-order', action='store_true', help='检查并修正文档排序')
    args = parser.parse_args()
    
    # 如果指定了修正文档排序
    if args.fix_order:
        print("开始检查并修正文档排序...")
        from category_tool import check_and_fix_document_order
        if check_and_fix_document_order(DOCUSAURUS_PATH):
            print("文档排序检查与修正完成")
            sys.exit(0)
        else:
            print("文档排序检查与修正失败")
            sys.exit(1)
    
    # 设置目标语言
    target_languages = TARGET_LANGUAGES
    if args.languages:
        target_languages = args.languages.split(',')
    
    # 确定使用哪种翻译方法
    use_llm = args.use_llm
    

    # 设置百度翻译API密钥
    print("使用百度翻译API")
    baidu_app_id = args.baidu_app_id or BAIDU_APP_ID
    baidu_secret_key = args.baidu_secret_key or BAIDU_SECRET_KEY
        
    # 如果提供了百度翻译API密钥，设置它们
    if baidu_app_id != "YOUR_BAIDU_APP_ID" and baidu_secret_key != "YOUR_BAIDU_SECRET_KEY":
        set_baidu_api_keys(baidu_app_id, baidu_secret_key)

    # 设置Azure OpenAI API配置
    azure_endpoint = args.azure_endpoint
    azure_api_key = args.azure_api_key
    azure_deployment = args.azure_deployment or "gpt-4o"
    
    # 检查是否提供了必要的Azure OpenAI API配置
    if not azure_endpoint or not azure_api_key:
        print("错误: 使用大模型翻译需要提供Azure OpenAI API的端点URL和密钥")
        print("请使用--azure-endpoint和--azure-api-key参数提供这些信息")
        sys.exit(1)
        
    # 设置Azure OpenAI API配置
    set_azure_openai_config(azure_endpoint, azure_api_key, azure_deployment)
    
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
                if use_llm:
                    # 检查Azure OpenAI API配置是否已设置
                    if not azure_endpoint or not azure_api_key:
                        print("错误: 使用大模型翻译需要提供Azure OpenAI API的端点URL和密钥")
                        print("请使用--azure-endpoint和--azure-api-key参数提供这些信息")
                        sys.exit(1)
                    
                    # 使用大模型翻译文档内容
                    translate_document_with_llm(document_structure, target_languages, force_translate=args.force_translate)
                    print("成功使用大模型翻译文档内容")
                else:
                    # 检查百度翻译API密钥是否已设置
                    if baidu_app_id == "YOUR_BAIDU_APP_ID" or baidu_secret_key == "YOUR_BAIDU_SECRET_KEY":
                        print("警告: 百度翻译API密钥未设置，无法执行翻译步骤")
                        print("请在config.py中设置BAIDU_APP_ID和BAIDU_SECRET_KEY，或使用--baidu-app-id和--baidu-secret-key参数")
                        sys.exit(1)
                    
                    # 使用百度翻译API翻译文档内容
                    translate_document_structure(document_structure, target_languages, force_translate=args.force_translate)
                    print("成功使用百度翻译API翻译文档内容")
            
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
            # 创建翻译文件结构（无论使用哪种翻译方法，都需要创建文件结构）
            create_translation_file_structure(document_structure, target_languages, use_llm=use_llm)
            print("成功创建翻译文件结构")
            
            if use_llm:
                # 检查Azure OpenAI API配置是否已设置
                if not azure_endpoint or not azure_api_key:
                    print("错误: 使用大模型翻译需要提供Azure OpenAI API的端点URL和密钥")
                    print("请使用--azure-endpoint和--azure-api-key参数提供这些信息")
                else:
                    # 使用大模型翻译文档内容
                    translate_document_with_llm(document_structure, target_languages, force_translate=args.force_translate)
                    print("成功使用大模型翻译文档内容")
            else:
                # 检查百度翻译API密钥是否已设置
                if baidu_app_id == "YOUR_BAIDU_APP_ID" or baidu_secret_key == "YOUR_BAIDU_SECRET_KEY":
                    print("警告: 百度翻译API密钥未设置，跳过翻译步骤")
                    print("请在config.py中设置BAIDU_APP_ID和BAIDU_SECRET_KEY，或使用--baidu-app-id和--baidu-secret-key参数")
                else:
                    # 使用百度翻译API翻译文档内容
                    translate_document_structure(document_structure, target_languages, force_translate=args.force_translate)
                    print("成功使用百度翻译API翻译文档内容")
            
            # 7. 确保英文文档同时存在于docs和i18n/en目录下
            en_i18n_path = os.path.join(DOCUSAURUS_PATH, "i18n", "en", "docusaurus-plugin-content-docs", "current")
            if os.path.exists(en_i18n_path):
                copy_english_to_docs(en_i18n_path, DOCS_PATH)
                print("成功将英文文档从i18n/en复制到docs目录")
        
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
