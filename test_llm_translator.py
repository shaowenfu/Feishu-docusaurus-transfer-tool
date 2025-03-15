# test_llm_translator.py
import os
import sys
import argparse
from llm_translator import set_azure_openai_config, translate_with_llm

def main():
    """
    测试大模型翻译功能
    """
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='测试大模型翻译功能')
    parser.add_argument('--azure-endpoint', required=True, help='Azure OpenAI API的端点URL')
    parser.add_argument('--azure-api-key', required=True, help='Azure OpenAI API的密钥')
    parser.add_argument('--azure-deployment', default='gpt-4o', help='Azure OpenAI API的部署名称，默认为gpt-4o')
    parser.add_argument('--input-file', required=True, help='要翻译的Markdown文件路径')
    parser.add_argument('--target-language', default='en', help='目标语言代码，默认为英语(en)')
    parser.add_argument('--output-file', help='翻译结果输出文件路径，默认为input-file名称加上语言代码')
    args = parser.parse_args()
    
    # 设置Azure OpenAI API配置
    set_azure_openai_config(args.azure_endpoint, args.azure_api_key, args.azure_deployment)
    
    # 读取输入文件
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"读取输入文件失败: {str(e)}")
        sys.exit(1)
    
    print(f"正在使用大模型翻译文件: {args.input_file} 到 {args.target_language}...")
    
    # 执行翻译
    translated_content = translate_with_llm(content, args.input_file, args.target_language)
    
    if translated_content:
        # 确定输出文件路径
        if args.output_file:
            output_file = args.output_file
        else:
            # 从输入文件路径生成输出文件路径
            base_name, ext = os.path.splitext(args.input_file)
            output_file = f"{base_name}_{args.target_language}{ext}"
        
        # 写入翻译结果
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(translated_content)
            print(f"翻译成功，结果已保存到: {output_file}")
        except Exception as e:
            print(f"写入输出文件失败: {str(e)}")
            print("翻译结果:")
            print("=" * 80)
            print(translated_content)
            print("=" * 80)
    else:
        print("翻译失败")

if __name__ == "__main__":
    main()
