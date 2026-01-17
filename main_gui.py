#主程序，负责调度各模块
import sys, cv2, time, pythoncom, os, datetime, traceback
from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QImage, QPixmap

from ui.main_window import YogaDashboard
from core.stabilizer import PoseStabilizer
from core.analyzer import PostureAnalyzer
from utils.visualizer import YogaVisualizer
from utils.audio import YogaAudio
import mediapipe as mp

# 处理 PyInstaller 打包后的 MediaPipe 资源路径问题
if hasattr(sys, '_MEIPASS'):
    # 指向打包后的 _internal/mediapipe 目录
    mp_path = os.path.join(sys._MEIPASS, 'mediapipe')
    
    # 强制注入环境变量，让底层 C++ 引擎去这里找模型
    os.environ['MEDIAPIPE_BINARY_GRAPH_PATH'] = mp_path
    
    # 针对 0.10.x 版本的特殊补丁：重定向资源查找函数
    from mediapipe.python import resource_util
    resource_util.set_resource_dir(mp_path)
    print(f">>> 已强制重定向 MediaPipe 资源路径: {mp_path}")
#资源路径，确保打包成.exe后依然能找到资源
def get_resource_path(relative_path):
    """ 处理 PyInstaller 打包后的路径问题 """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
#启动引擎
class YogaAIController:
    def __init__(self):

        print(">>> [1/5] 初始化多线程 COM...")
        pythoncom.CoInitialize() 
        
        self.app = QApplication(sys.argv)
        self.window = YogaDashboard()
        
        print(">>> [2/5] 启动摄像头...")
        self.cap = cv2.VideoCapture(0)
        
        print(">>> [3/5] 加载 MediaPipe 模型...")
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            model_complexity=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        self.stabilizer = PoseStabilizer()
        self.analyzer = PostureAnalyzer()
        self.visualizer = YogaVisualizer()
        self.audio = YogaAudio()
        
        self.last_voice_time = 0 
        self.setup_connections()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_loop)
        self.timer.start(33) 
        print(">>> [5/5] 系统已就绪。")

    def setup_connections(self):
        try:
            self.window.btn_m.clicked.connect(lambda: self.switch_view("muscle"))
            self.window.btn_s.clicked.connect(lambda: self.switch_view("skeleton"))
            self.window.btn_save.clicked.connect(self.handle_save)
        except AttributeError as e:
            print(f"!!! 界面连接失败: {e}。")

    def handle_save(self):
        if hasattr(self.window, 'save_and_reset'):
            self.window.save_and_reset()

    def switch_view(self, mode):
        side = "back" if "front" in self.window.view_mode else "front"
        self.window.view_mode = f"{side}_{mode}"

    def update_loop(self):
        try:
            ret, frame = self.cap.read()
            if not ret or frame is None:
                return

            frame = cv2.flip(frame, 1)
            h, w, ch = frame.shape
            #绘制检测圈圈
            cv2.circle(frame, (w // 2, h // 2), 200, (200, 200, 200), 1, cv2.LINE_AA)
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(rgb_frame)

            if results.pose_landmarks:
                # 检测人体是否在中心区域附近 ---
                lm = results.pose_landmarks.landmark
                # 获取躯干核心中心（肩部 11,12 和 髋部 23,24 的几何平均中心）
                center_x = (lm[11].x + lm[12].x + lm[23].x + lm[24].x) / 4
                center_y = (lm[11].y + lm[12].y + lm[23].y + lm[24].y) / 4
                
                # 计算与屏幕中心 (0.5, 0.5) 的欧式距离 (归一化坐标)
                dist_from_center = ((center_x - 0.5)**2 + (center_y - 0.5)**2)**0.5
                
                # 设定阈值：0.5 (覆盖屏幕大部分核心区域，排除边缘杂波)
                if dist_from_center < 0.5:
                    # 1. 只有进入中心区域，才绘制骨架和执行分析
                    frame = self.visualizer.draw_skeleton(frame, results.pose_landmarks)
                    points = self.stabilizer.smooth(results.pose_landmarks)
                    metrics = self.analyzer.get_metrics(points)
                    
                    status, report_html, voice_text = self.analyzer.analyze_clinical(
                        metrics, self.window.patient_name.text() or "待测患者"
                    )
                    
                    # 2. 实时刷新 UI 
                    self.window.val_sh.setText(f"高低肩: {abs(metrics['sh']):.1f}°")
                    self.window.val_pl.setText(f"骨盆偏移: {abs(metrics['pl']):.1f}°")
                    
                    if hasattr(self.window, 'val_sc'):
                        self.window.val_sc.setText(f"脊柱侧弯: {abs(metrics['sc']):.1f}°")
                    
                    self.window.report_area.setHtml(report_html)
                    self.window.update_anatomy(status)

                    # 3. 语音触发
                    now = time.time()
                    if voice_text and (now - self.last_voice_time > 6):
                        print(f">>> 逻辑触发语音播报: {voice_text}")
                        self.audio.speak(voice_text)
                        self.last_voice_time = now
                else:
                    # 如果检测到人但在边缘，给予视觉提示而不进行监测
                    cv2.putText(frame, "KEEP TARGET IN CENTER CIRCLE", (w // 2 - 180, 60), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            # 将画面渲染到 UI 窗口
            qt_img = QImage(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB).data, w, h, w*ch, QImage.Format_RGB888).copy()
            self.window.update_frame(QPixmap.fromImage(qt_img))

        except Exception as e:
            traceback.print_exc()

    def run(self):
        self.window.show()
        return self.app.exec()

if __name__ == "__main__":
    controller = YogaAIController()
    sys.exit(controller.run())