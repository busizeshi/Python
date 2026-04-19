# python虚拟环境
#### 导出依赖包
pip freeze > requirements.txt
#### 导入依赖包
pip install -r requirements.txt
#### 创建虚拟环境
python -m venv venv
#### 激活虚拟环境
source venv/bin/activate
#### 退出虚拟环境
deactivate
#### 删除虚拟环境
rm -rf venv
#### 删除依赖包
rm requirements.txt
#### 列出当前虚拟环境依赖包
pip list
#### 更新依赖包
pip install --upgrade pip