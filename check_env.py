#环境依赖监测脚本
import importlib.util
import sys

def check_package(package_name, import_name=None):
    """
    检查特定包是否都已安装
    """
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    spec = importlib.util.find_spec(import_name)
    if spec is not None:
        return True
    return False

requirements = {
    "numpy": "numpy",
    "mediapipe": "mediapipe",
    "opencv-python": "cv2",
    "PySide6": "PySide6",
    "pyttsx3": "pyttsx3",
    "pyinstaller": "pyinstaller"
}

print("="*30)
print("Yoga AI 环境依赖检测中...")
print("="*30)

missing = []
for pkg, imp in requirements.items():
    status = "OK" if check_package(pkg, imp) else "MISSING"
    print(f"[{status:7}] {pkg}")
    if status == "MISSING":
        missing.append(pkg)

print("-" * 30)
if not missing:
    print("✅ 所有核心依赖已就绪，可以开始运行或打包！")
else:
    print(f"❌ 缺少以下依赖：{', '.join(missing)}")
    print("\n请运行以下命令进行修复：")
    print(f"pip install {' '.join(missing)} -i http://pypi.tuna.tsinghua.edu.cn/simple --trusted-host pypi.tuna.tsinghua.edu.cn")
print("="*30)