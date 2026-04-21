import os
import base64
from io import BytesIO
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# 设置 DashScope API Key
# 获取地址：https://help.aliyun.com/zh/dashscope/developer-reference/activate-dashscope-and-create-an-api-key
os.environ["DASHSCOPE_API_KEY"] = "sk-51b422ad7151406b8c3ddb1ce0a424ba"

def pdf_to_images(pdf_path, dpi=200, poppler_path=None):
    """
    将 PDF 文件的每一页转换为图片
    
    Args:
        pdf_path: PDF 文件路径
        dpi: 图片分辨率，默认 200
        poppler_path: Windows 下 Poppler 的路径（可选）
        
    Returns:
        list: PIL Image 对象列表
    """
    from pdf2image import convert_from_path
    
    print(f"正在将 PDF 转换为图片: {pdf_path}")
    
    # Windows 下需要指定 Poppler 路径
    kwargs = {"dpi": dpi}
    if poppler_path and os.name == 'nt':
        kwargs["poppler_path"] = poppler_path
        print(f"使用 Poppler: {poppler_path}")
    
    images = convert_from_path(pdf_path, **kwargs)
    print(f"成功提取 {len(images)} 页图片")
    return images


def image_to_base64(image):
    """
    将 PIL Image 转换为 base64 编码
    
    Args:
        image: PIL Image 对象
        
    Returns:
        str: base64 编码的字符串
    """
    buffered = BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str


def analyze_image_with_qwen(image_base64, llm):
    """
    使用千问多模态大模型分析图片并生成说明文字
    
    Args:
        image_base64: base64 编码的图片
        llm: ChatOpenAI 实例
        
    Returns:
        str: 生成的说明文字
    """
    # 构建多模态消息
    message = HumanMessage(
        content=[
            {
                "type": "text",
                "text": "请详细描述这张图片的内容，包括：\n1. 图片中的主要元素和对象\n2. 文字内容（如果有）\n3. 图表或数据的含义（如果有）\n4. 整体布局和视觉风格\n请用中文回答。"
            },
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            }
        ]
    )
    
    # 调用千问多模态模型
    response = llm.invoke([message])
    return response.content


def parse_pdf_with_multimodal(pdf_path, output_dir=None, poppler_path=None):
    """
    主函数：使用多模态大模型整体解析 PDF 图文
    
    Args:
        pdf_path: PDF 文件路径
        output_dir: 可选，保存提取图片的目录
        poppler_path: Windows 下 Poppler 的路径（可选）
        
    Returns:
        list: LangChain Document 对象列表
    """
    # 配置千问多模态模型（qwen-vl-max 支持视觉理解）
    llm = ChatOpenAI(
        model="qwen-vl-max",  # 千问视觉语言模型
        openai_api_key=os.environ["DASHSCOPE_API_KEY"],
        openai_api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
        temperature=0.7
    )
    
    # 第一步：将 PDF 转换为图片
    images = pdf_to_images(pdf_path, poppler_path=poppler_path)
    
    # 如果需要保存提取的图片
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
        print(f"保存图片到: {output_dir}")
    
    documents = []
    
    # 第二步和第三步：分析每页图片并生成 Document
    for page_num, image in enumerate(images, start=1):
        print(f"\n{'='*60}")
        print(f"正在处理第 {page_num}/{len(images)} 页...")
        
        # 保存图片（可选）
        if output_dir:
            image_path = os.path.join(output_dir, f"page_{page_num}.jpg")
            image.save(image_path, "JPEG")
            print(f"已保存图片: {image_path}")
        
        # 转换为 base64
        image_base64 = image_to_base64(image)
        
        # 使用千问多模态模型分析图片
        try:
            description = analyze_image_with_qwen(image_base64, llm)
            print(f"✓ 第 {page_num} 页分析完成")
            print(f"说明文字长度: {len(description)} 字符")
        except Exception as e:
            print(f"✗ 第 {page_num} 页分析失败: {e}")
            description = f"[第 {page_num} 页分析失败: {str(e)}]"
        
        # 创建 LangChain Document 对象
        doc = Document(
            page_content=description,
            metadata={
                "source": pdf_path,
                "page": page_num,
                "total_pages": len(images),
                "type": "multimodal_analysis"
            }
        )
        documents.append(doc)
    
    print(f"\n{'='*60}")
    print(f"处理完成！共生成 {len(documents)} 个 Document 对象")
    
    return documents


if __name__ == "__main__":
    # 示例：解析 PDF 文件
    # 使用项目中的 PDF 文件
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pdf_path = os.path.join(base_dir, "data", "复杂PDF", "billionaires_page-1-5.pdf")
    
    # 可选：保存提取的图片
    output_dir = os.path.join(base_dir, "data", "复杂PDF", "extracted_images")
    
    # Windows 下需要安装 Poppler 并配置路径
    # 下载地址：https://github.com/oschwartz10612/poppler-windows/releases/
    # 解压后设置路径，例如：
    # poppler_path = r"D:\tools\poppler-24.08.0\Library"
    poppler_path = None  # 如果已安装 Poppler，请设置此路径
    
    # 执行解析
    documents = parse_pdf_with_multimodal(pdf_path, output_dir, poppler_path)
    
    # 打印结果示例
    print("\n" + "="*60)
    print("解析结果示例（第1页）:")
    print("="*60)
    if documents:
        print(f"\n元数据: {documents[0].metadata}")
        print(f"\n说明文字:\n{documents[0].page_content[:500]}...")
