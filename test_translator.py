import os
import sys
from dotenv import load_dotenv
from translator import (
    set_baidu_api_keys,
    translate_markdown,
    split_frontmatter,
    DOCUSAURUS_LANGUAGE_PATHS
)

def test_markdown_translation():
    """测试Markdown文档翻译功能"""
    
    # 加载环境变量
    load_dotenv()
    
    # 设置百度翻译API密钥
    API_KEY = os.getenv("BAIDU_APP_ID")
    SECRET_KEY = os.getenv("BAIDU_SECRET_KEY")
    set_baidu_api_keys(API_KEY, SECRET_KEY)
    
    # 读取源文件
    source_file = "E:/Obsidian_space/HomeOfSherwen/Home_file/CanTianAI/cantian-ai-wiki/docs/天干/乙.md"
    if not os.path.exists(source_file):
        print(f"错误：找不到源文件 {source_file}")
        sys.exit(1)
    
    try:
        with open(source_file, 'r', encoding='utf-8') as f:
            content = f.read()
        print("成功读取源文件")
        
        # 创建目标目录
        target_lang = "en"
        target_dir = "E:/Obsidian_space/HomeOfSherwen/Home_file/CanTianAI/feishu-docusaurus"
        os.makedirs(target_dir, exist_ok=True)
        
        # 翻译内容
        print("开始翻译...")
        translated_content = translate_markdown(content, target_lang)
        
        # 保存翻译结果
        target_file = os.path.join(target_dir, "乙.md")
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(translated_content)
        print(f"翻译完成，已保存到 {target_file}")
        
        # 验证结果
        print("\n翻译结果预览（前500字符）:")
        print("-" * 80)
        print(translated_content[:500])
        print("-" * 80)
        
        # 检查格式
        check_markdown_format(translated_content)
        
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
        sys.exit(1)

def check_markdown_format(content):
    """检查翻译后的Markdown格式是否正确"""
    print("\n开始检查Markdown格式...")
    
    # 检查frontmatter
    if not content.startswith("---"):
        print("警告：frontmatter 可能丢失")
    else:
        # 检查frontmatter格式
        parts = content.split("---", 2)
        if len(parts) >= 3:
            frontmatter = parts[1].strip()
            print(f"Frontmatter内容:\n{frontmatter}")
            
            # 检查frontmatter是否有效
            try:
                import yaml
                yaml_data = yaml.safe_load(f"---\n{frontmatter}\n---")
                print("Frontmatter YAML格式有效")
                print(f"YAML数据: {yaml_data}")
            except Exception as e:
                print(f"警告：Frontmatter YAML格式无效: {str(e)}")
    
    # 检查标题格式
    if "###" not in content:
        print("警告：可能缺少三级标题")
    
    # 检查粗体格式
    bold_count = content.count("**")
    if bold_count % 2 != 0:
        print(f"警告：粗体标记数量不成对 ({bold_count})")
    
    # 检查列表格式
    if "- " not in content:
        print("警告：可能缺少列表标记")
    
    # 检查缩进
    if "  -" not in content:
        print("警告：可能缺少缩进列表")
    
    print("格式检查完成")

def main():
    print("开始测试Markdown翻译功能...")
    test_markdown_translation()
    print("\n测试完成")

if __name__ == "__main__":
    main()
