#交互与展示模块
import os
import sys
import datetime
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *

#资源路径，确保打包成.exe后依然能找到资源
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class YogaDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YogaAI Pro v3.0 - 临床监测版")
        self.resize(1400, 950)
        self.setStyleSheet("QMainWindow { background-color: #0F172A; }")
        
        self.view_mode = "front_muscle"
        self.setup_ui()

    def setup_ui(self):
        self.central = QWidget()
        self.setCentralWidget(self.central)
        self.main_lay = QVBoxLayout(self.central)
        self.main_lay.setContentsMargins(20, 20, 20, 20)

        # 1. 顶部：患者管理栏
        input_layout = QHBoxLayout()
        self.patient_name = QLineEdit()
        self.patient_name.setPlaceholderText("请输入患者姓名以存档...")
        self.patient_name.setStyleSheet("""
            height: 40px; background: #1E293B; color: white; 
            padding-left: 10px; border-radius: 5px; font-size: 15px;
        """)
        
        self.btn_save = QPushButton("💾 保存并存档报告")
        self.btn_save.setStyleSheet("""
            background-color: #10B981; color: white; 
            font-weight: bold; min-width: 200px; height: 40px; border-radius: 5px;
        """)
        
        input_layout.addWidget(self.patient_name, stretch=8)
        input_layout.addWidget(self.btn_save, stretch=2)
        self.main_lay.addLayout(input_layout)

        # 2. 中间：画面展示区
        content = QHBoxLayout()
        self.video_label = QLabel("摄像头准备中...")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(850, 600)
        self.video_label.setStyleSheet("background: black; border-radius: 10px; border: 2px solid #3B82F6;")
        content.addWidget(self.video_label, stretch=7)

        # 右侧：肌肉和骨骼button
        sidebar = QVBoxLayout()
        btn_lay = QHBoxLayout()
        self.btn_m = QPushButton("肌肉图")
        self.btn_s = QPushButton("骨骼图")
        btn_lay.addWidget(self.btn_m)
        btn_lay.addWidget(self.btn_s)
        sidebar.addLayout(btn_lay)

        self.anatomy_label = QLabel()
        self.anatomy_label.setFixedSize(350, 450)
        self.anatomy_label.setStyleSheet("background: #1E293B; border-radius: 10px;")
        sidebar.addWidget(self.anatomy_label)

        # 脊柱侧弯标签 
        self.val_sh = QLabel("高低肩: --°")
        self.val_pl = QLabel("骨盆偏移: --°")
        self.val_sc = QLabel("脊柱侧弯: --°") 
        
        for lb in [self.val_sh, self.val_pl, self.val_sc]:
            lb.setStyleSheet("font-size: 20px; color: #60A5FA; font-weight: bold; margin: 10px 0;")
            sidebar.addWidget(lb)
        # ------------------------------

        sidebar.addStretch()
        content.addLayout(sidebar, stretch=3)
        self.main_lay.addLayout(content)

        # 3. 底部：诊断报告区
        self.report_area = QTextBrowser()
        self.report_area.setStyleSheet("""
            background: #020617; color: #E2E8F0; 
            padding: 15px; border: 1px solid #3B82F6; border-radius: 10px;
        """)
        self.report_area.setMaximumHeight(180)
        self.main_lay.addWidget(self.report_area)

    def save_and_reset(self):
        """处理报告保存到 /reports 文件夹并重置 UI"""
        name = self.patient_name.text().strip() if self.patient_name.text() else "匿名患者"
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        report_dir = os.path.join(os.getcwd(), "reports")
        if not os.path.exists(report_dir):
            os.makedirs(report_dir)
        
        file_path = os.path.join(report_dir, f"{name}_{timestamp}.txt")
        
        try:
            report_content = self.report_area.toPlainText()
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"YogaAI 康复报告 - {name}\n")
                f.write(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("-" * 40 + "\n")
                f.write(report_content)
            
            QMessageBox.information(self, "成功", f"报告已存至: {file_path}")
            
            self.patient_name.clear()
            self.report_area.setHtml("<p style='color: #94A3B8;'>就绪。等待下一位患者输入姓名...</p>")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def update_frame(self, pixmap):
        self.video_label.setPixmap(pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def update_anatomy(self, status):
        img_rel_path = os.path.join("assets", f"{self.view_mode}.png")
        path = get_resource_path(img_rel_path)
        
        if not os.path.exists(path): 
            print(f"!!! 找不到图片资源: {path}")
            return
        pix = QPixmap(path).scaled(self.anatomy_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        ptr = QPainter(pix)
        ptr.setRenderHint(QPainter.Antialiasing)
        

        coords = {
            "neck": (0.5, 0.18), 
            "shoulder_l": (0.35, 0.25), 
            "shoulder_r": (0.65, 0.25), 
            "pelvis": (0.5, 0.65),
            "spine": (0.5, 0.45) 
        }
        for part, s in status.items():
            if s == "issue" and part in coords:
                x, y = coords[part]
                if "back" in self.view_mode: x = 1.0 - x
                ptr.setBrush(QColor(239, 68, 68, 180))
                ptr.drawEllipse(int(x*pix.width())-10, int(y*pix.height())-10, 20, 20)
        ptr.end()
        self.anatomy_label.setPixmap(pix)