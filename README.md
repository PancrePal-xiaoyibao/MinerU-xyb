
## 本项目基于MinerU，配合小x宝社区对于RAG的场景需求进行了修改，提供了云端存储，方便在RAG中支持混排能力。同时提供了批量处理的功能，方便用户批量上传，对于导入RAG的pdf文档，图片和不同格式进行有选择的处理，方便用户上传。提供了3种批量处理脚本，可以进行后续修改。


## 主要更新
### 图片链接改为云端，方便Rag生成回答中的Markdown的图文显示
1. s3（sealos存储桶/腾讯cos/阿里oss）的存储：pdf文件解析后，图片会在本地和s3存储桶都存一份，方便后续使用
2. 转化后的markdown文件中的图片以图片链接的形式存在，方便Rag生成回答中的Markdown的图文显示

### 修改了magic-pdf.json
增加了对应的开关配置:
```python
{
    "bucket_info": {
        "填写存储桶的实际名称": [
            "填写存储桶的access key",
            "填写存储桶的Secret Key ",
            "填写存储桶url（不要加https）比如objectstorageapi.cloud.sealos.top"
        ],
        "xyb": [
            "7*****7",
            "dz********5g8",
            "ob***jectstorageapi.cloud.sealos.to***p"
        ]  # 可以支持多个存储桶，在batch-mineru-3in1-s3.py中进行修改
    },
    "storage_config": {
        "image_storage": "s3",
        "enable_local_backup": true
    },
    "models-dir": "/workspace/model_dir/opendatalab/PDF-Extract-Kit-1___0/models",
    "layoutreader-model-dir": "/workspace/model_dir/ppaanngggg/layoutreader",
    "device-mode": "cuda",
    "layout-config": {
        "model": "doclayout_yolo"
    },
    "formula-config": {
        "mfd_model": "yolo_v8_mfd",
        "mfr_model": "unimernet_small",
        "enable": true
    },
    "table-config": {
        "model": "rapid_table",
        "sub_model": "slanet_plus",
        "enable": true,
        "max_time": 400
    },
    "llm-aided-config": {
        "formula_aided": {
            "api_key": "your_api_key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen2.5-7b-instruct",
            "enable": false
        },
        "text_aided": {
            "api_key": "your_api_key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen2.5-7b-instruct",
            "enable": false
        },
        "title_aided": {
            "api_key": "your_api_key",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen2.5-32b-instruct",
            "enable": false
        }
    },
    "config_version": "1.1.1"
```


## batch-mineru-3in1-s3.py修改配置
1. 存储桶的选择和参数配置
line31

```python
    if storage_config['image_storage'] == 's3':
        bucket_name = list(config['bucket_info'].keys())[0]  # 获取第一个 bucket 名称，配合上面的magic-pdf.json使用，第一个或者第二个存储桶，修改[0]的数字就可以，0是第一个，1是第二个，以此类推；
        bucket_info = config['bucket_info'][bucket_name]
        access_key = bucket_info[0] #对应access key
        secret_key = bucket_info[1] #对应secure key
        base_url = f"https://{bucket_info[2]}" 对应url
```


2. 制定自己的输入输出目录
```python
if __name__ == '__main__':
    input_dir = "/workspace/MinerU/filestoconvert"  # 替换为实际的输入目录
    output_dir = "/workspace/MinerU/output"  # 替换为实际的输出目录
```

## 部署方式
1. git clone目录到本地


2. 创建mineru环境并安装
```bash
conda create -n mineru python=3.10
conda activate mineru
pip install -U "magic-pdf[full]" --extra-index-url https://wheels.myhloli.com -i https://mirrors.aliyun.com/pypi/simple
```

如果报错，问ai或者删除重建环境

我在部署腾讯免费的gpu资源-cloudstudio 的时候需要完善几个包
```bash
apt install update
apt install nano
apt install mesa-common-dev libgl1-mesa-dev libgl1 
 #报错ImportError: libGL.so.1: cannot open shared object file: No such file or directory 表明 magic-pdf 依赖的 cv2 (OpenCV) 库在加载时找不到 libGL.so.1 这个共享库文件

magic-pdf --version 
#应该可以显示版本
```

3. 下载模型，模型可以下载到指定的目录，避免GPU服务器每次重置后丢失。
```bash
nano download_models.py

#line42
    model_dir = snapshot_download('opendatalab/PDF-Extract-Kit-1.0', allow_patterns=mineru_patterns,cache_dir='填写你自定义的模型下载保存路径 比如:/workspace/model_dir')
    layoutreader_model_dir = snapshot_download('ppaanngggg/layoutreader',cache_dir='填写你自定义的模型下载保存路径 比如：/workspace/model_dir')
    model_dir = model_dir + '/models'

python download_models.py #执行下载就可以了    
```

4. 测试下
```bash
cd demo
magic-pdf -p small_ocr.pdf -o ./output
```
顺利跑通

5. 验证批量转化
上传文件到/pdftoconvert, 图片/pdf/doc文件都放一个
```bash
mkdir filestoconvert &&cd filestoconvert #如果没有先创建
mkdir output #输出文件
#上传若干文件
python batch-mineru-3in1-s3.py
```
看下结果。

6. 清理内存
```bash
apt autoclean
pip cache purge
```
清理下内存

## 修改 requirement.txt
```bash
#增加了
minio==7.2.15 #MinIO Python SDK for Amazon S3 Compatible Cloud Storage
```

## gpu监控
```bash
apt-get install nvtop
nvtop -m full
```

## 文档
https://mineru.readthedocs.io/ 