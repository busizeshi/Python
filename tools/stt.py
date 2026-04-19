"""
FunASR 语音识别 HTTP 服务（完整可运行版）

功能：
1. 启动 Flask Web 服务
2. 接收 Java / ESP32 上传的 wav 音频文件
3. 使用 FunASR 识别中文语音
4. 返回 JSON 文本结果

启动方式：

pip install flask funasr modelscope torch torchaudio

python3 app.py

接口地址：
POST http://服务器IP:5001/stt

form-data:
file = record.wav
"""

import os
import uuid
import tempfile
import traceback
import shutil
import subprocess
from flask import Flask, request, jsonify
from funasr import AutoModel

# =========================
# 初始化 Flask
# =========================
app = Flask(__name__)

# =========================
# 加载模型（首次启动稍慢）
# 推荐中文模型：paraformer-zh
# =========================
print("正在加载 FunASR 模型，请稍候...")

model = AutoModel(
    model="paraformer-zh"
)

print("FunASR 模型加载完成！")


# =========================
# 检查依赖
# =========================
def check_dependencies():
    """检查音频处理依赖是否安装"""
    issues = []
    
    # 检查 ffmpeg
    if shutil.which("ffmpeg") is None:
        issues.append(
            "⚠️  警告: 未检测到 ffmpeg，可能导致音频加载失败。\n"
            "   安装方法:\n"
            "   1. 访问: https://github.com/BtbN/FFmpeg-Builds/releases\n"
            "   2. 下载: ffmpeg-master-latest-win64-gpl.zip\n"
            "   3. 解压并将 bin 目录添加到系统 PATH 环境变量"
        )
    
    # 检查 torchcodec（安全导入检查）
    torchcodec_available = False
    try:
        import importlib.util
        if importlib.util.find_spec("torchcodec") is not None:
            # 模块存在，尝试实际导入验证
            import torchcodec
            torchcodec_available = True
    except (ImportError, RuntimeError, OSError) as e:
        # torchcodec 存在但依赖不满足（如缺少 ffmpeg DLL）
        torchcodec_available = False
    
    if not torchcodec_available:
        issues.append(
            "ℹ️  提示: torchcodec 未安装或不可用（可选，不影响基本功能）\n"
            "   如需使用，请先安装 ffmpeg，然后: pip install torchcodec"
        )
    
    return issues

# 启动时检查依赖
dep_warnings = check_dependencies()
if dep_warnings:
    print("\n" + "="*60)
    for warn in dep_warnings:
        print(warn)
    print("="*60 + "\n")


# =========================
# 首页测试
# =========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "msg": "FunASR 服务运行中",
        "api": "/stt"
    })


# =========================
# 语音识别接口
# =========================
@app.route("/stt", methods=["POST"])
def stt():
    temp_file = None

    try:
        # 判断是否上传文件
        if "file" not in request.files:
            return jsonify({
                "code": 400,
                "msg": "缺少 file 参数"
            })

        file = request.files["file"]

        if file.filename == "":
            return jsonify({
                "code": 400,
                "msg": "文件为空"
            })

        # 临时文件名（跨平台兼容）
        filename = str(uuid.uuid4()) + ".wav"
        temp_file = os.path.join(tempfile.gettempdir(), filename)

        # 保存上传音频
        file.save(temp_file)

        # 开始识别
        result = model.generate(
            input=temp_file
        )

        # FunASR 返回格式处理
        text = ""

        if isinstance(result, list) and len(result) > 0:
            text = result[0].get("text", "").strip()

        return jsonify({
            "code": 200,
            "msg": "success",
            "text": text
        })

    except FileNotFoundError as e:
        error_msg = "音频处理失败，缺少必要的依赖。\n"
        if shutil.which("ffmpeg") is None:
            error_msg += "\n未安装 ffmpeg，请按以下步骤安装：\n"
            error_msg += "1. 访问: https://github.com/BtbN/FFmpeg-Builds/releases\n"
            error_msg += "2. 下载最新 Windows 版本 (ffmpeg-master-latest-win64-gpl.zip)\n"
            error_msg += "3. 解压到 C:\\ffmpeg\n"
            error_msg += "4. 将 C:\\ffmpeg\\bin 添加到系统 PATH 环境变量\n"
            error_msg += "5. 重启终端和 Python 服务\n"
        else:
            error_msg += f"\n详细错误: {str(e)}"
        
        return jsonify({
            "code": 500,
            "msg": error_msg
        })

    except Exception as e:
        traceback.print_exc()

        return jsonify({
            "code": 500,
            "msg": str(e)
        })

    finally:
        # 删除临时文件
        try:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
        except:
            pass


# =========================
# 启动服务
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )
