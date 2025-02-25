import os
from loguru import logger
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod

def process_single_pdf(pdf_path: str, output_dir: str):
    """处理单个PDF文件"""
    pdf_name = os.path.basename(pdf_path)
    name_without_suff = os.path.splitext(pdf_name)[0]
    
    # 准备输出目录
    local_image_dir = os.path.join(output_dir, "images")
    local_md_dir = output_dir
    image_dir = str(os.path.basename(local_image_dir))
    
    os.makedirs(local_image_dir, exist_ok=True)
    
    image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
    
    # 读取PDF内容
    reader = FileBasedDataReader("")
    pdf_bytes = reader.read(pdf_path)
    
    # 处理PDF
    ds = PymuDocDataset(pdf_bytes)
    
    if ds.classify() == SupportedPdfParseMethod.OCR:
        infer_result = ds.apply(doc_analyze, ocr=True)
        pipe_result = infer_result.pipe_ocr_mode(image_writer)
    else:
        infer_result = ds.apply(doc_analyze, ocr=False)
        pipe_result = infer_result.pipe_txt_mode(image_writer)
    
    # 生成输出文件
    infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))
    model_inference_result = infer_result.get_infer_res()
    pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))
    pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))
    
    # 保存各种格式的输出
    pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
    pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)
    pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')

def process_pdf_files(input_dir: str, output_base_dir: str):
    """批量处理指定目录下的PDF文件"""
    logger.info(f"开始处理目录 {input_dir} 中的PDF文件")
    
    if not os.path.exists(input_dir):
        logger.error(f"输入目录 {input_dir} 不存在")
        return
    
    # 获取所有PDF文件
    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        logger.warning(f"目录 {input_dir} 中没有找到PDF文件")
        return
    
    logger.info(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 处理每个PDF文件
    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join(input_dir, pdf_file)
        pdf_name = os.path.splitext(pdf_file)[0]
        output_dir = os.path.join(output_base_dir, pdf_name)
        
        logger.info(f"[{i}/{len(pdf_files)}] 开始处理: {pdf_file}")
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            process_single_pdf(pdf_path, output_dir)
            logger.info(f"完成处理: {pdf_file}")
        except Exception as e:
            logger.error(f"处理 {pdf_file} 时出错: {str(e)}")
            continue

if __name__ == '__main__':
    input_dir = "/workspace/MinerU/pdftoconvert"  # 替换为实际的输入目录
    output_dir = "/workspace/MinerU/pdfoutput"  # 替换为实际的输出目录
    
    process_pdf_files(input_dir, output_dir)