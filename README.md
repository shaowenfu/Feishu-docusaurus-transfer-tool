# 飞书文档转Docusaurus工具

这个工具用于从飞书API获取《命理Tips》文档内容，并将其转换为Markdown格式，然后集成到现有的Docusaurus项目中。

## 功能

1. 从飞书API获取文档内容
2. 解析文档结构，提取二级标题和三级标题
3. 在Docusaurus项目中创建相应的目录和文件
4. 更新Docusaurus的侧边栏配置
5. 推送更改到Github（可选）

## 使用方法

1. 确保已安装Python 3.6+和必要的依赖：
   ```bash
   pip install requests
   ```

2. 配置`config.py`文件：
   - 设置飞书应用的APP_ID和APP_SECRET
   - 设置文档的DOC_TOKEN
   - 设置Docusaurus项目路径

3. 运行脚本：
   ```bash
   python main.py
   ```

## 文件说明

- `config.py`: 配置文件，存储API密钥等信息
- `feishu_api.py`: 飞书API相关函数
- `document_parser.py`: 文档解析相关函数
- `file_generator.py`: 文件生成相关函数
- `main.py`: 主程序入口

## 注意事项

1. 如果文档结构解析失败，脚本会将提取的内容保存到`extracted_content.md`文件，以便手动处理。
2. 在更新Docusaurus配置前，脚本会自动备份`sidebars.ts`文件。
3. 如果推送到Github失败，脚本会提供手动推送的步骤。

## 常见问题

1. 如果遇到API认证问题，请检查APP_ID和APP_SECRET是否正确。
2. 如果遇到文档解析问题，可能是因为文档结构与预期不符，请查看调试输出的JSON结构。
3. 如果遇到文件写入问题，请确保有足够的权限访问Docusaurus项目目录。
