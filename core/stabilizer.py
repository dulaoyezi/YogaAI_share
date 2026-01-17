#一欧元滤波算法，延迟低，计算量小，适合实时姿态平滑
import numpy as np

class OneEuroFilter:
    def __init__(self, freq=30, min_cutoff=1.0, beta=0.007, d_cutoff=1.0):
        self.freq = freq
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        self.x_prev = None
        self.dx_prev = None

    def _alpha(self, cutoff):
        tau = 1.0 / (2 * np.pi * cutoff)
        te = 1.0 / self.freq
        return 1.0 / (1.0 + tau / te)

    def smooth(self, x):
        if self.x_prev is None:
            self.x_prev = x
            self.dx_prev = np.zeros_like(x)
            return x
        
        te = 1.0 / self.freq
        dx = (x - self.x_prev) / te
        edx = self._alpha(self.d_cutoff) * dx + (1 - self._alpha(self.d_cutoff)) * self.dx_prev
        cutoff = self.min_cutoff + self.beta * np.abs(edx)
        alpha = self._alpha(cutoff)
        result = alpha * x + (1 - alpha) * self.x_prev
        
        self.x_prev, self.dx_prev = result, edx
        return result

class PoseStabilizer:
    def __init__(self, freq=30):
        self.filter = OneEuroFilter(freq=freq)

    def smooth(self, landmarks):
        # 将 Mediapipe 的坐标转为 Numpy 数组进行矩阵运算
        curr = np.array([[lm.x, lm.y] for lm in landmarks.landmark])
        return self.filter.smooth(curr)