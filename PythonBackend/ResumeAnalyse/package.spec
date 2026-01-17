# -*- mode: python ; coding: utf-8 -*-

import sys
import os

block_cipher = None

# 获取当前 spec 文件所在的目录绝对路径
spec_root = os.path.abspath(os.getcwd())
# 项目根目录 (ResumeAnalyse 的上一级，即 ResumeSystem)
# 这样做的目的是为了让 Python 能够通过 'import ResumeAnalyse' 找到包
# 假设我们在 ResumeAnalyse 目录下执行 pyinstaller
project_root = os.path.abspath(os.path.join(spec_root, '..'))

# 定义需要包含的数据文件
# 格式: (源文件路径, 目标文件夹)
datas = [
    ('settings.json', 'ResumeAnalyse'),  # 将 settings.json 打包到 ResumeAnalyse 目录下
    ('chroma_data', 'ResumeAnalyse/chroma_data'), # 包含 vector db 数据
    # 如果有其他静态文件，继续添加
    # ('../Resume_Data', 'Resume_Data'), # 示例：如果需要打包测试数据
]

# 定义隐式导入的包
# PyInstaller 可能无法自动检测到某些动态导入的依赖
hiddenimports = [
    'uvicorn',
    'fastapi',
    'pika',
    'langchain',
    'langgraph',
    'langchain_chroma',
    'langchain_huggingface',
    'chromadb',
    'gradio',
    'sentence_transformers',
    'numpy',
    # 添加你在代码中用到但 pyinstaller 报错说找不到的包
]

a = Analysis(
    ['StartupServices.py'],  # 入口脚本
    pathex=[project_root],   # 关键：添加项目父目录到搜索路径，解决 ModuleNotFoundError: No module named 'ResumeAnalyse'
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ResumeSystemServices', # 打包生成的可执行文件名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True, # 开启控制台窗口，方便查看日志输出
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ResumeSystemServices', # 最终生成的文件夹名称 (dist/ResumeSystemServices)
)

