import numpy as np

class PostureAnalyzer:
    def __init__(self):
        # 阈值：低于此度数视为健康
        self.THRESH = {"sh": 3.8, "pl": 3.0, "sc": 4.5}

    def get_metrics(self, points):
        """
        计算生物力学指标并进行数值限幅
        使用向量夹角算法优化脊柱侧弯检测
        """
        # 1. 高低肩角度 (Landmarks 11, 12)
        sh_raw = np.degrees(np.arctan2(points[11][1] - points[12][1], points[11][0] - points[12][0]))
        sh = np.clip(sh_raw, -45.0, 45.0) # 限幅 45°

        # 2. 骨盆倾斜度 (Landmarks 23, 24)
        pl_raw = np.degrees(np.arctan2(points[23][1] - points[24][1], points[23][0] - points[24][0]))
        pl = np.clip(pl_raw, -45.0, 45.0) # 限幅 45°

        # 3. 脊柱侧向偏移 (向量夹角优化版)
        mid_sh = (points[11] + points[12]) / 2  # 肩部中点
        mid_pl = (points[23] + points[24]) / 2  # 骨盆中点
        
        dx = mid_sh[0] - mid_pl[0]
        dy = mid_sh[1] - mid_pl[1]
        
        # 绝对值 dy 确保参考轴始终向上，避免 180° 翻转
        # 计算出的角度是相对于“垂直向上”的偏离角
        sc_raw = np.degrees(np.arctan2(dx, abs(dy))) 
        sc = np.clip(sc_raw, -90.0, 90.0) # 限幅 90°
        
        return {"sh": sh, "pl": pl, "sc": sc}

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