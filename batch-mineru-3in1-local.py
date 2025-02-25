import os
from loguru import logger
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.read_api import read_local_office, read_local_images

def process_single_pdf(pdf_path: str, output_dir: str):
    """处理单个PDF文件"""
    pdf_name = os.path.basename(pdf_path)
    name_without_suff = os.path.splitext(pdf_name)[0]
    logger.info(f"开始处理PDF文件: {pdf_name}")
    
    # 准备输出目录
    local_image_dir = os.path.join(output_dir, "images")
    local_md_dir = output_dir
    image_dir = str(os.path.basename(local_image_dir))
    
    os.makedirs(local_image_dir, exist_ok=True)
    
    image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
    
    # 读取PDF内容
    logger.info("正在读取PDF文件内容...")
    reader = FileBasedDataReader("")
    pdf_bytes = reader.read(pdf_path)
    
    # 处理PDF
    logger.info("开始分析PDF文件...")
    ds = PymuDocDataset(pdf_bytes)
    
    if ds.classify() == SupportedPdfParseMethod.OCR:
        logger.info("使用OCR模式处理PDF")
        infer_result = ds.apply(doc_analyze, ocr=True)
        pipe_result = infer_result.pipe_ocr_mode(image_writer)
    else:
        logger.info("使用文本模式处理PDF")
        infer_result = ds.apply(doc_analyze, ocr=False)
        pipe_result = infer_result.pipe_txt_mode(image_writer)
    
    # 生成输出文件
    logger.debug(f"生成模型分析文件: {name_without_suff}_model.pdf")
    infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))
    
    logger.debug(f"生成布局分析文件: {name_without_suff}_layout.pdf")
    pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))
    
    logger.debug(f"生成文本分析文件: {name_without_suff}_spans.pdf")
    pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))
    
    logger.debug(f"生成Markdown文件: {name_without_suff}.md")
    pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
    
    logger.debug(f"生成内容列表: {name_without_suff}_content_list.json")
    pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)
    
    logger.debug(f"生成中间JSON文件: {name_without_suff}_middle.json")
    pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')
    
    logger.info(f"完成PDF文件处理: {pdf_name}")

def process_image_file(file_path: str, output_dir: str):
    """处理图片文件"""
    image_name = os.path.basename(file_path)
    name_without_suff = os.path.splitext(image_name)[0]
    logger.info(f"开始处理图片文件: {image_name}")
    
    # 准备输出目录
    local_image_dir = os.path.join(output_dir, "images")
    local_md_dir = output_dir
    image_dir = str(os.path.basename(local_image_dir))
    
    os.makedirs(local_image_dir, exist_ok=True)
    
    image_writer = FileBasedDataWriter(local_image_dir)
    md_writer = FileBasedDataWriter(local_md_dir)
    
    # 读取图片文件内容
    logger.info("正在读取图片文件...")
    ds = read_local_images(file_path)[0]
    
    # 处理图片
    logger.info("使用OCR模式处理图片")
    infer_result = ds.apply(doc_analyze, ocr=True)
    pipe_result = infer_result.pipe_ocr_mode(image_writer)
    
    # 生成输出文件
    logger.debug(f"生成模型分析文件: {name_without_suff}_model.pdf")
    infer_result.draw_model(os.path.join(local_md_dir, f"{name_without_suff}_model.pdf"))
    
    logger.debug(f"生成布局分析文件: {name_without_suff}_layout.pdf")
    pipe_result.draw_layout(os.path.join(local_md_dir, f"{name_without_suff}_layout.pdf"))
    
    logger.debug(f"生成文本分析文件: {name_without_suff}_spans.pdf")
    pipe_result.draw_span(os.path.join(local_md_dir, f"{name_without_suff}_spans.pdf"))
    
    logger.debug(f"生成Markdown文件: {name_without_suff}.md")
    pipe_result.dump_md(md_writer, f"{name_without_suff}.md", image_dir)
    
    logger.debug(f"生成内容列表: {name_without_suff}_content_list.json")
    pipe_result.dump_content_list(md_writer, f"{name_without_suff}_content_list.json", image_dir)
    
    logger.debug(f"生成中间JSON文件: {name_without_suff}_middle.json")
    pipe_result.dump_middle_json(md_writer, f'{name_without_suff}_middle.json')
    
    logger.info(f"完成图片文件处理: {image_name}")

def process_office_file(file_path: str, output_dir: str):
    """处理Office文件"""
    file_name = os.path.basename(file_path)
    name_without_suff = os.path.splitext(file_name)[0]
    logger.info(f"开始处理Office文件: {file_name}")
    
    # 准备输出目录
    local_image_dir = os.path.join(output_dir, "images")
    local_md_dir = output_dir
    image_dir = str(os.path.basename(local_image_dir))
    
    os.makedirs(local_image_dir, exist_ok=True)
    logger.debug(f"创建输出目录: {local_image_dir}")
    
    image_writer = FileBasedDataWriter(local_image_dir)
    md_writer = FileBasedDataWriter(local_md_dir)
    
    try:
        # 使用 read_local_office 直接处理 Office 文件
        logger.info("正在读取Office文件内容...")
        datasets = read_local_office(file_path, encoding='utf-8')  # 显式指定 UTF-8 编码
        logger.info(f"文件包含 {len(datasets)} 个页面/幻灯片")
        
        for idx, ds in enumerate(datasets):
            current_name = f"{name_without_suff}_{idx+1}" if len(datasets) > 1 else name_without_suff
            logger.info(f"处理第 {idx+1}/{len(datasets)} 个页面: {current_name}")
            
            try:
                if ds.classify() == SupportedPdfParseMethod.OCR:
                    logger.info(f"使用OCR模式处理页面 {idx+1}")
                    infer_result = ds.apply(doc_analyze, ocr=True)
                    pipe_result = infer_result.pipe_ocr_mode(image_writer)
                else:
                    logger.info(f"使用文本模式处理页面 {idx+1}")
                    infer_result = ds.apply(doc_analyze, ocr=False)
                    pipe_result = infer_result.pipe_txt_mode(image_writer)
                
                # 检查文本内容是否包含乱码
                sample_text = pipe_result.get_text()[:100] if hasattr(pipe_result, 'get_text') else ""
                if sample_text:
                    logger.debug(f"页面 {idx+1} 文本样例: {sample_text}")
                    
                # 生成输出文件时指定编码
                logger.debug(f"生成模型分析文件: {current_name}_model.pdf")
                infer_result.draw_model(os.path.join(local_md_dir, f"{current_name}_model.pdf"))
                
                logger.debug(f"生成布局分析文件: {current_name}_layout.pdf")
                pipe_result.draw_layout(os.path.join(local_md_dir, f"{current_name}_layout.pdf"))
                
                logger.debug(f"生成文本分析文件: {current_name}_spans.pdf")
                pipe_result.draw_span(os.path.join(local_md_dir, f"{current_name}_spans.pdf"))
                
                logger.debug(f"生成Markdown文件: {current_name}.md")
                pipe_result.dump_md(md_writer, f"{current_name}.md", image_dir, encoding='utf-8')
                
                logger.debug(f"生成内容列表: {current_name}_content_list.json")
                pipe_result.dump_content_list(md_writer, f"{current_name}_content_list.json", image_dir, encoding='utf-8')
                
                logger.debug(f"生成中间JSON文件: {current_name}_middle.json")
                pipe_result.dump_middle_json(md_writer, f'{current_name}_middle.json', encoding='utf-8')
                
            except Exception as e:
                logger.error(f"处理页面 {idx+1} 时出错: {str(e)}")
                continue
                
            logger.info(f"完成页面 {idx+1} 处理")
            
    except Exception as e:
        logger.error(f"处理Office文件时出错: {str(e)}")
        raise
        
    logger.info(f"完成Office文件处理: {file_name}")

def process_files(input_dir: str, output_base_dir: str):
    """批量处理指定目录下的所有支持文件"""
    logger.info(f"开始扫描目录 {input_dir}")
    
    if not os.path.exists(input_dir):
        logger.error(f"输入目录 {input_dir} 不存在")
        return
    
    # 支持的文件类型分类
    supported_files = {
        'pdf': [],
        'office': [],
        'image': []
    }
    
    # 文件类型映射
    file_type_map = {
        '.pdf': 'pdf',
        '.doc': 'office', '.docx': 'office', 
        '.ppt': 'office', '.pptx': 'office',
        '.xls': 'office', '.xlsx': 'office',
        '.jpg': 'image', '.jpeg': 'image', 
        '.png': 'image', '.bmp': 'image',
        '.tiff': 'image', '.gif': 'image'
    }
    
    # 扫描并分类文件
    for file in os.listdir(input_dir):
        ext = os.path.splitext(file)[1].lower()
        if ext in file_type_map:
            file_type = file_type_map[ext]
            supported_files[file_type].append(file)
    
    # 统计并输出文件数量
    total_files = sum(len(files) for files in supported_files.values())
    if total_files == 0:
        logger.warning(f"目录 {input_dir} 中没有找到支持的文件")
        return
    
    logger.info("文件扫描统计:")
    logger.info(f"- PDF文件: {len(supported_files['pdf'])} 个")
    logger.info(f"- Office文件: {len(supported_files['office'])} 个")
    logger.info(f"- 图片文件: {len(supported_files['image'])} 个")
    logger.info(f"总计: {total_files} 个文件待处理")
    
    # 按类型批量处理文件
    for file_type, files in supported_files.items():
        if not files:
            continue
            
        logger.info(f"\n开始处理{file_type.upper()}类型文件 ({len(files)}个)")
        for i, file in enumerate(files, 1):
            file_path = os.path.join(input_dir, file)
            name_without_suff = os.path.splitext(file)[0]
            output_dir = os.path.join(output_base_dir, name_without_suff)
            
            logger.info(f"[{i}/{len(files)}] 开始处理 {file_type.upper()} 文件: {file}")
            
            try:
                os.makedirs(output_dir, exist_ok=True)
                if file_type == 'pdf':
                    process_single_pdf(file_path, output_dir)
                elif file_type == 'office':
                    process_office_file(file_path, output_dir)
                elif file_type == 'image':
                    process_image_file(file_path, output_dir)
                logger.info(f"完成处理: {file}")
            except Exception as e:
                logger.error(f"处理 {file} 时出错: {str(e)}")
                continue

if __name__ == '__main__':
    input_dir = "/workspace/MinerU/filestoconvert"  # 替换为实际的输入目录
    output_dir = "/workspace/MinerU/output"  # 替换为实际的输出目录
    
    process_files(input_dir, output_dir)