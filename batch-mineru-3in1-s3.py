import os
import json  # 添加 json 模块导入
from loguru import logger
from magic_pdf.data.data_reader_writer import FileBasedDataWriter, FileBasedDataReader
from magic_pdf.data.dataset import PymuDocDataset
from magic_pdf.model.doc_analyze_by_custom_model import doc_analyze
from magic_pdf.config.enums import SupportedPdfParseMethod
from magic_pdf.data.read_api import read_local_office, read_local_images
from minio import Minio
import io

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'magic-pdf.json')
    with open(config_path, 'r') as f:
        return json.load(f)

def get_storage_writers(config, output_dir, name_without_suff):
    """根据配置获取存储writer"""
    storage_config = config.get('storage_config', {'image_storage': 'local', 'enable_local_backup': True})
    
    writers = []
    local_image_dir = os.path.join(output_dir, "images")
    
    # 如果使用S3或需要本地备份，创建本地目录
    if storage_config['image_storage'] == 'local' or storage_config['enable_local_backup']:
        os.makedirs(local_image_dir, exist_ok=True)
        writers.append(FileBasedDataWriter(local_image_dir))
    
    # 如果使用S3存储
    if storage_config['image_storage'] == 's3':
        bucket_name = list(config['bucket_info'].keys())[0]  # 获取第一个 bucket 名称
        bucket_info = config['bucket_info'][bucket_name]
        access_key = bucket_info[0]
        secret_key = bucket_info[1]
        base_url = f"https://{bucket_info[2]}"
        
        # 创建MinIO客户端
        endpoint = base_url.replace("https://", "").replace("http://", "")
        secure = base_url.startswith("https://")
        logger.info(f"创建MinIO客户端: endpoint={endpoint}, secure={secure}")
        
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        
        # 使用完整的桶名（包含access_key前缀）
        full_bucket_name = f"{access_key}-{bucket_name}"
        logger.info(f"检查存储桶: {full_bucket_name}")
        
        try:
            if not client.bucket_exists(full_bucket_name):
                client.make_bucket(full_bucket_name)
                logger.info(f"创建存储桶：{full_bucket_name}")
            else:
                logger.info(f"存储桶已存在：{full_bucket_name}")
        except Exception as e:
            logger.warning(f"检查存储桶失败：{str(e)}")
        
        writers.append((client, full_bucket_name, f"images/{name_without_suff}"))
    
    return writers

def get_image_dir(config, output_dir, name_without_suff):
    """获取图片目录路径"""
    storage_config = config.get('storage_config', {'image_storage': 'local'})
    
    if storage_config['image_storage'] == 's3':
        bucket_name = list(config['bucket_info'].keys())[0]
        bucket_info = config['bucket_info'][bucket_name]
        access_key = bucket_info[0]
        endpoint_url = f"https://{bucket_info[2]}"
        full_bucket_name = f"{access_key}-{bucket_name}"
        # 对路径中的空格进行编码
        encoded_name = name_without_suff.replace(' ', '%20')
        return f"{endpoint_url}/{full_bucket_name}/images/{encoded_name}"
    else:
        return "images"

def process_single_pdf(pdf_path: str, output_dir: str):
    """处理单个PDF文件"""
    pdf_name = os.path.basename(pdf_path)
    name_without_suff = os.path.splitext(pdf_name)[0]
    logger.info(f"开始处理PDF文件: {pdf_name}")
    
    # 加载配置
    config = load_config()
    
    # 准备输出目录
    local_image_dir = os.path.join(output_dir, "images")
    local_md_dir = output_dir
    
    # 获取存储writers和图片目录
    image_writers = get_storage_writers(config, output_dir, name_without_suff)
    image_dir = get_image_dir(config, output_dir, name_without_suff)
    md_writer = FileBasedDataWriter(output_dir)
    
    # 读取PDF内容
    logger.info("正在读取PDF文件内容...")
    reader = FileBasedDataReader("")
    pdf_bytes = reader.read(pdf_path)
    
    # 处理PDF
    logger.info("开始分析PDF文件...")
    ds = PymuDocDataset(pdf_bytes)
    
    # 处理PDF时，对每个writer都进行处理
    if ds.classify() == SupportedPdfParseMethod.OCR:
        infer_result = ds.apply(doc_analyze, ocr=True)
        pipe_result = None
        for writer in image_writers:
            if isinstance(writer, tuple):  # MinIO client
                if pipe_result is None:
                    pipe_result = infer_result.pipe_ocr_mode(FileBasedDataWriter(local_image_dir))
                client, bucket_name, prefix = writer
                # 处理每个生成的图片
                logger.info("开始上传图片到 S3...")
                for img_path in os.listdir(local_image_dir):
                    if img_path.endswith(('.png', '.jpg', '.jpeg')):
                        full_path = os.path.join(local_image_dir, img_path)
                        with open(full_path, 'rb') as f:
                            data = f.read()
                            logger.debug(f"上传图片: {img_path}")
                            result = client.put_object(
                                bucket_name,
                                f"{prefix}/{img_path}",
                                io.BytesIO(data),
                                len(data),
                                content_type='image/png'
                            )
                            # 添加上传成功的日志，确保 URL 中的空格被编码
                            encoded_prefix = prefix.replace(' ', '%20')
                            encoded_img_path = img_path.replace(' ', '%20')
                            file_url = f"{base_url}/{bucket_name}/{encoded_prefix}/{encoded_img_path}"
                            logger.info(f"图片上传成功: {file_url}")
                            logger.debug(f"上传成功: etag={result.etag}")
            else:
                pipe_result = infer_result.pipe_ocr_mode(writer)
    else:
        infer_result = ds.apply(doc_analyze, ocr=False)
        pipe_result = None
        for writer in image_writers:
            if isinstance(writer, tuple):  # MinIO client
                if pipe_result is None:
                    pipe_result = infer_result.pipe_txt_mode(FileBasedDataWriter(local_image_dir))
                client, bucket_name, prefix = writer
                # 处理每个生成的图片
                logger.info("开始上传图片到 S3...")
                for img_path in os.listdir(local_image_dir):
                    if img_path.endswith(('.png', '.jpg', '.jpeg')):
                        full_path = os.path.join(local_image_dir, img_path)
                        with open(full_path, 'rb') as f:
                            data = f.read()
                            logger.debug(f"上传图片: {img_path}")
                            client.put_object(
                                bucket_name,
                                f"{prefix}/{img_path}",
                                io.BytesIO(data),
                                len(data),
                                content_type='image/png'
                            )
            else:
                pipe_result = infer_result.pipe_txt_mode(writer)
            
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
        datasets = read_local_office(file_path)  # 移除 encoding 参数
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
                
                # 生成输出文件时移除 encoding 参数
                logger.debug(f"生成Markdown文件: {current_name}.md")
                pipe_result.dump_md(md_writer, f"{current_name}.md", image_dir)
                
                logger.debug(f"生成内容列表: {current_name}_content_list.json")
                pipe_result.dump_content_list(md_writer, f"{current_name}_content_list.json", image_dir)
                
                logger.debug(f"生成中间JSON文件: {current_name}_middle.json")
                pipe_result.dump_middle_json(md_writer, f'{current_name}_middle.json')
                
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