1. git clone目录到本地


2. 创建mineru环境并安装
‘’‘
conda create -n mineru python=3.10
conda activate mineru
pip install -U "magic-pdf[full]" --extra-index-url https://wheels.myhloli.com -i https://mirrors.aliyun.com/pypi/simple
’‘’

如果报错，问ai或者删除重建环境

我在部署cloudstudio的时候需要完善几个包
‘’‘
apt install update
apt install nano
apt install mesa-common-dev libgl1-mesa-dev libgl1 
 #报错ImportError: libGL.so.1: cannot open shared object file: No such file or directory 表明 magic-pdf 依赖的 cv2 (OpenCV) 库在加载时找不到 libGL.so.1 这个共享库文件

magic-pdf --version 
#应该可以显示版本
’‘’
3. 下载模型
‘’‘
nano download_models.py

#line42
    model_dir = snapshot_download('opendatalab/PDF-Extract-Kit-1.0', allow_patterns=mineru_patterns,cache_dir='填写你自定义的模型下载保存路径 比如:/workspace/model_dir')
    layoutreader_model_dir = snapshot_download('ppaanngggg/layoutreader',cache_dir='填写你自定义的模型下载保存路径 比如：/workspace/model_dir')
    model_dir = model_dir + '/models'

python download_models.py #执行下载就可以了    
’‘’

4. 测试下
'''
cd demo
magic-pdf -p small_ocr.pdf -o ./output
'''
顺利跑通

5. 验证批量转化
上传文件到/pdftoconvert, 图片/pdf/doc文件都放一个
‘’‘
python batch-mineru-3in1-s3.py
’‘’
看下结果。

6. 清理内存
‘’‘
apt autoclean
pip cache purge
’‘’
清理下内存