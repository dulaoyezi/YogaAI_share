import numpy as np

class LowPassFilter:
    def __init__(self, alpha):
        self.__y = None
        self.__alpha = alpha

    def __call__(self, value):
        if self.__y is None:
            s = value
        else:
            s = self.__alpha * value + (1.0 - self.__alpha) * self.__y
        self.__y = s
        return s

class OneEuroFilter:
    def __init__(self, freq, min_cutoff=1.0, beta=0.0, d_cutoff=1.0):
        self.__freq = freq
        self.__min_cutoff = min_cutoff
        self.__beta = beta
        self.__d_cutoff = d_cutoff
        self.__x_filt = LowPassFilter(self.__alpha(min_cutoff))
        self.__dx_filt = LowPassFilter(self.__alpha(d_cutoff))
        self.__last_x = None

    def __alpha(self, cutoff):
        te = 1.0 / self.__freq
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau / te)

    def __call__(self, x):
        dx = 0.0 if self.__last_x is None else (x - self.__last_x) * self.__freq
        edx = self.__dx_filt(dx)
        cutoff = self.__min_cutoff + self.__beta * abs(edx)
        alpha = self.__alpha(cutoff)
        self.__last_x = x
        return self.__x_filt(alpha * x + (1.0 - alpha) * self.__x_filt._LowPassFilter__y if self.__x_filt._LowPassFilter__y else x)