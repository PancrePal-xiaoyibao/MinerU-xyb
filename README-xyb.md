## 主要更新
### 图片链接改为云端，方便Rag生成回答中的Markdown的图文显示
1. s3（sealos存储桶/腾讯cos/阿里oss）的存储：pdf文件解析后，图片会在本地和s3存储桶都存一份，方便后续使用
2. 转化后的markdown文件中的图片以图片链接的形式存在，方便Rag生成回答中的Markdown的图文显示

### 修改了magic-pdf.json
增加了对于的开关配置
‘’‘
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
            "objectstorageapi.cloud.sealos.top"
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
’‘’


## batch-mineru-3in1-s3.py修改配置
1. 存储桶的选择和参数配置
line31
‘’‘
    if storage_config['image_storage'] == 's3':
        bucket_name = list(config['bucket_info'].keys())[0]  # 获取第一个 bucket 名称，配合上面的magic-pdf.json使用，第一个或者第二个存储桶，修改[0]的数字就可以，0是第一个，1是第二个，以此类推；
        bucket_info = config['bucket_info'][bucket_name]
        access_key = bucket_info[0] #对应access key
        secret_key = bucket_info[1] #对应secure key
        base_url = f"https://{bucket_info[2]}" 对应url
’‘’

2.