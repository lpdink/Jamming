import numpy as np
import logging

import settings


class Modulate():
    f_c = 24000  # 载波频率
    f_s = 50000  # 载波频率
    amplitude = 1  # 归一化幅度
    channel_num = 7  # 声道数

    belta = 1  # PM调制使用系数

    # AM调制
    @classmethod
    def am_modulate(cls, audio_clip):
        # 检查
        if not isinstance(audio_clip, np.ndarray):
            raise TypeError("Input audio clip must be numpy array!")

        if audio_clip.dtype not in (np.float64, np.float32, np.float16):
            raise TypeError("Input audio clip must be float numpy!")

        if audio_clip.ndim != 1:
            raise ValueError("Input message must be 1D!")

        if settings.OUTPUT_CHANNEL not in (1, 2):
            raise ValueError("Input channel must be 1 or 2!")

        # 生成载波信号
        t = np.linspace(0,
                        audio_clip.size / settings.OUT_FS,
                        num=audio_clip.size)
        carry = np.sin(2 * np.pi * cls.f_c * t)

        # 左声道部分信号生成
        re_left = carry * audio_clip  # *为星乘，@为点乘

        # 右声道部分信号生成
        re_right = carry.copy()

        if settings.OUTPUT_CHANNEL == 1:
            re = re_left + re_right
            return cls.amplitude * re / 2
        else:
            return (cls.amplitude * re_left, cls.amplitude * re_right)

    @classmethod
    def pm_modulate(cls, audio_clip):
        # 检查
        if not isinstance(audio_clip, np.ndarray):
            raise TypeError("Input audio clip must be numpy array!")

        if audio_clip.dtype not in (np.float64, np.float32, np.float16):
            raise TypeError("Input audio clip must be float numpy!")

        if audio_clip.ndim != 1:
            raise ValueError("Input message must be 1D!")

        if settings.OUTPUT_CHANNEL != 2:
            raise ValueError("Input channel must be 2!")

        # 生成时间序列
        t = np.linspace(0,
                        audio_clip.size / settings.OUT_FS,
                        num=audio_clip.size)

        # 左声道部分信号生成
        re_left = np.sin(2 * np.pi * cls.f_c * t +
                         cls.belta * np.cumsum(audio_clip))

        # 右声道部分信号生成
        re_right = np.sin(2 * np.pi * cls.f_s * t)

        return (cls.amplitude * re_left, cls.amplitude * re_right)

    @classmethod
    def convolve(cls, x):
        size = 2 * x.shape[0] - 1
        x = np.fft.fft(x, size)
        x = x * x
        return np.fft.ifft(x)

    @classmethod
    def get_leakage(cls, f_sequence_array):
        size = 2 * f_sequence_array.shape[1] - 1
        res = np.zeros(size, dtype=np.complex128)
        for x in f_sequence_array:
            convolve_sequence = cls.convolve(x)
            res = res + convolve_sequence
        res = np.abs(res)
        res **= 2
        return res.sum()

    @classmethod
    def split(cls, f_sequence, split_points):
        num = split_points.size
        size = f_sequence.shape[0]
        f_sequence_array = np.array([])

        pre_point = 0
        for point in split_points:
            now_f_sequence = np.zeros(size, dtype=np.complex128)
            now_f_sequence[pre_point + 1:point + 1] = f_sequence[pre_point + 1:point + 1]
            now_f_sequence[size - point - 1: size - pre_point] = f_sequence[size - point - 1: size - pre_point]
            if pre_point == 0:
                now_f_sequence[0] = f_sequence[0]
            now_f_sequence = np.real(np.fft.ifft(now_f_sequence))
            f_sequence_array = np.append(f_sequence_array, now_f_sequence)
            pre_point = point

        f_sequence_array = f_sequence_array.reshape((num, size))
        return f_sequence_array

    @classmethod
    def split_normal(cls, audio_clip, split_points=np.array([19000, 20000, 21000, 22000, 23000], dtype=int)):
        size = audio_clip.size
        f_sequence = np.fft.fft(audio_clip)
        split_points = split_points * (size // settings.OUT_FS)
        split_points = np.append(split_points, size // 2 - 1)
        tmp = cls.split(f_sequence, split_points)
        return tmp

    @classmethod
    def get_array(cls, audio_clip):
        size = audio_clip.size
        t = np.linspace(0, size / settings.OUT_FS, num=size)
        carry = np.sin(2 * np.pi * cls.f_c * t)
        tmp_audio = carry * audio_clip

        audio_array = cls.split_normal(tmp_audio)
        audio_array = np.row_stack((audio_array, carry))

        return audio_array
