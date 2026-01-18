import numpy as np

class PostureAnalyzer:
    def __init__(self):
        # 阈值设定
        self.THRESH = {"sh": 3.8, "pl": 3.0, "sc": 4.5}
        
        # 初始化平滑缓冲区，防止 AttributeError
        self.prev_metrics = {"sh": 0.0, "pl": 0.0, "sc": 0.0}
        
        # 平滑系数 (0.0 < alpha <= 1.0)
        # alpha 越小越平滑（抖动小），但延迟会变高
        self.alpha = 0.3

    def get_metrics(self, points):
        # 如果没检测到人，直接返回上一次的指标，防止崩溃
        if points is None or len(points) < 25: 
            return self.prev_metrics, False

        try:
            # 强制转换为 NumPy 数组，确保向量数学运算（+ /）有效
            pts = np.array(points)
            # 如果胯部已经到了画面底部 10% 的区域（> 0.9），判定为“未全身入镜”
            if pts[23][1] > 0.9 or pts[24][1] > 0.9:
                return self.prev_metrics, False

            # 高低肩 (Landmarks 11, 12)
            sh_raw = np.degrees(np.arctan2(pts[11][1] - pts[12][1], 
                                         pts[11][0] - pts[12][0]))
            sh = np.clip(sh_raw, -45.0, 45.0)

            # 骨盆倾斜度 (Landmarks 23, 24)
            pl_raw = np.degrees(np.arctan2(pts[23][1] - pts[24][1], 
                                         pts[23][0] - pts[24][0]))
            pl = np.clip(pl_raw, -45.0, 45.0)

            # 脊柱中轴线 
            mid_sh = (pts[11] + pts[12]) / 2
            mid_pl = (pts[23] + pts[24]) / 2
            
            dx = mid_sh[0] - mid_pl[0]
            dy = mid_sh[1] - mid_pl[1] 
            
            sc_raw = np.degrees(np.arctan2(dx, abs(dy)))
            sc = np.clip(sc_raw, -90.0, 90.0)

            # EMA 平滑滤波
            current_metrics = {"sh": sh, "pl": pl, "sc": sc}
            for key in current_metrics:
                self.prev_metrics[key] = (self.alpha * current_metrics[key] + 
                                        (1 - self.alpha) * self.prev_metrics[key])

            return self.prev_metrics, True

        except Exception as e:
            # 打印具体错误到控制台，方便调试
            print(f"PostueAnalyzer Error: {e}")
            return self.prev_metrics, False

    def analyze_clinical(self, m, name="患者"):
        status = {"neck": "ok", "shoulder_l": "ok", "shoulder_r": "ok", "pelvis": "ok", "spine": "ok"}
        issues, prescriptions, voice_advice = [], [], ""

        # 1. 高低肩分析
        if abs(m["sh"]) > self.THRESH["sh"]:
            side = "左" if m["sh"] > 0 else "右"
            status["shoulder_l" if m["sh"] > 0 else "shoulder_r"] = "issue"
            issues.append(f"<b>【高低肩】</b>检测到{side}侧肩峰代偿性上提 ({abs(m['sh']):.1f}°)")
            prescriptions.append(f"建议放松{side}侧肩胛骨周围肌群（斜方肌上束），并下沉肩峰。")
            voice_advice = f"请放松{side}侧肩胛骨，延展颈部。"

        # 2. 骨盆分析
        if abs(m["pl"]) > self.THRESH["pl"]:
            status["pelvis"] = "issue"
            issues.append(f"<b>【骨盆偏移】</b>水平面力线失衡 ({abs(m['pl']):.1f}°)")
            prescriptions.append("建议加强核心稳定性，尝试侧卧抬腿激活中臀肌。")
            if not voice_advice: 
                voice_advice = "请注意收紧核心，稳定骨盆。"

        # 3. 脊柱中轴分析
        if abs(m["sc"]) > self.THRESH["sc"]:
            status["spine"] = "issue"
            issues.append(f"<b>【脊柱力线异常】</b>重心偏离中轴线 ({abs(m['sc']):.1f}°)")
            prescriptions.append("建议进行靠墙站立，尝试向头顶方向‘延展脊柱’。")
            voice_advice += " 请尝试延展脊柱，向上拔高。"

        # 生成 HTML 文本报告
        report_html = f"""
        <div style='font-family: Arial;'>
            <h3 style='color: #60A5FA;'>{name} 的临床生物力学报告</h3>
            <p><b>检测状态：</b>{'<span style="color:#EF4444;">存在代偿风险</span>' if issues else '<span style="color:#10B981;">体态优良</span>'}</p>
            {''.join([f'<li style="color:#E2E8F0;">{i}</li>' for i in issues])}
            <hr style='border: 0.5px solid #334155;'>
            <p style='color: #94A3B8;'><b>康复处方：</b>{'；'.join(prescriptions) if prescriptions else '暂无异常，继续保持。'}</p>
        </div>
        """
        return status, report_html, voice_advice