from setuptools import setup, find_packages

"""
Setup script for the ResumeAnalyse package.
This script uses setuptools to define the package structure, dependencies,
and entry points for executable scripts.
该文件用于定义 ResumeAnalyse 包的安装配置，包括包结构、依赖项和可执行脚本入口点。以便使用setuptools进行打包和分发。
"""
# Find sub-packages found in the current directory (e.g., rabbitmq, entity).
# Since we map the root package 'ResumeAnalyse' to '.', these become submodules
# of ResumeAnalyse (e.g., ResumeAnalyse.rabbitmq).
found_packages = find_packages(where=".")
packages = ["ResumeAnalyse"] + [f"ResumeAnalyse.{pkg}" for pkg in found_packages]

setup(
    name="ResumeAnalyse",
    version="0.1.0",
    description="Resume Analysis System Backend",

    # Define package structure
    packages=packages,
    package_dir={"ResumeAnalyse": "."},

    # Python version compatibility
    python_requires=">=3.8",

    # Dependencies
    install_requires=[
        "langchain",
        "langgraph",
        "pydantic",
        "pika",
        "docling",
        "langchain-chroma",
        "langchain-huggingface",
        "numpy",
        # Add other dependencies here if needed (e.g., openai)
    ],

    # Entry points allow generating executables (e.g., 'resume-services')
    entry_points={
        "console_scripts": [
            "resume-services=ResumeAnalyse.StartupServices:start_all_services",
        ],
    },

    # Include non-code files specified in MANIFEST.in or package logic
    include_package_data=True,
)

