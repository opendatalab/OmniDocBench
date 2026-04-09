import os
import base64
import mimetypes
from pathlib import Path

# 注意：根据实际SDK调整导入
# from zhipuai import ZhipuAI  # 如果是官方SDK
from zai import ZhipuAiClient  # 保持原样，假设这是正确的

def process_images_to_markdown(api_key, image_folder_path, markdown_folder_path=None):
    """
    将图片文件夹中的所有图片转换为布局解析的Markdown文件
    
    Args:
        api_key: 智谱AI API密钥
        image_folder_path: 图片文件夹路径
        markdown_folder_path: Markdown输出文件夹路径，默认为图片文件夹内的"markdown_output"文件夹
    """
    # 初始化客户端
    client = ZhipuAiClient(api_key=api_key)
    
    # 设置Markdown输出文件夹
    if markdown_folder_path is None:
        markdown_folder_path = os.path.join(image_folder_path, "markdown_output")
    
    # 创建Markdown输出文件夹
    os.makedirs(markdown_folder_path, exist_ok=True)
    
    # 支持的图片格式
    supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif'}
    
    # 遍历图片文件夹
    for filename in os.listdir(image_folder_path):
        # 检查文件是否为支持的图片格式
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in supported_extensions:
            continue
        
        # 构建完整的图片文件路径
        image_path = os.path.join(image_folder_path, filename)
        
        # 生成对应的Markdown文件名
        md_filename = os.path.splitext(filename)[0] + ".md"
        md_path = os.path.join(markdown_folder_path, md_filename)
        
        # 检查Markdown文件是否已经存在
        if os.path.exists(md_path):
            print(f"已跳过: {filename} (对应的Markdown文件已存在)")
            continue
        
        print(f"正在处理: {filename}")
        
        try:
            # 读取图片文件并转换为base64
            with open(image_path, 'rb') as image_file:
                img_data = image_file.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # 获取MIME类型
            mime_type, _ = mimetypes.guess_type(image_path)
            if mime_type is None:
                # 如果无法推断，根据扩展名设置默认值
                if file_ext in ['.jpg', '.jpeg']:
                    mime_type = 'image/jpeg'
                elif file_ext == '.png':
                    mime_type = 'image/png'
                elif file_ext == '.gif':
                    mime_type = 'image/gif'
                elif file_ext == '.bmp':
                    mime_type = 'image/bmp'
                elif file_ext == '.webp':
                    mime_type = 'image/webp'
                elif file_ext in ['.tiff', '.tif']:
                    mime_type = 'image/tiff'
                else:
                    mime_type = 'image/jpeg'  # 默认
            
            # 调用布局解析 API
            response = client.layout_parsing.create(
                model="glm-ocr",
                file=f"data:{mime_type};base64,{img_base64}"
            )
            
            # 提取md_results字段的内容
            md_content = response.md_results
            print(md_content)
            # 将内容写入Markdown文件
            with open(md_path, 'w', encoding='utf-8') as md_file:
                md_file.write(md_content)
            
            print(f"  已保存: {md_filename}")
            
            # 可选：打印一些统计信息
            if hasattr(response, 'usage'):
                print(f"  消耗token数: {response.usage.total_tokens}")
            
        except Exception as e:
            print(f"  处理失败 {filename}: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print(f"\n处理完成！Markdown文件保存在: {markdown_folder_path}")
    return markdown_folder_path


# 使用示例
if __name__ == "__main__":
    # 你的智谱AI API密钥
    API_KEY = "API_KEY"  # 请替换为你的实际API密钥
    
    # 图片文件夹路径
    IMAGE_FOLDER = "IMAGE_FOLDER"  # 请替换为你的图片文件夹路径
    MARKDOWN_FOLDER = "MARKDOWN_FOLDER"
    
    # 调用函数处理图片
    output_folder = process_images_to_markdown(
        api_key=API_KEY,
        image_folder_path=IMAGE_FOLDER,
        markdown_folder_path=MARKDOWN_FOLDER  # 可选参数
    )
    
    print(f"Markdown文件输出目录: {output_folder}")