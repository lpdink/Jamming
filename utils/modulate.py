import numpy as np
import logging

import settings


class Modulate():
    f_c = 24000  # 载波频率
    f_s = 50000  # 载波频率
    amplitude = 1  # 归一化幅度

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
            return cls.amplitude * re_left, cls.amplitude * re_right

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

        return cls.amplitude * re_left, cls.amplitude * re_right

    @classmethod
    def get_leakage(cls, f_sequence_array):
        size = 2 * f_sequence_array.shape[1] - 1
        res = np.zeros(size, dtype=np.complexfloating)
        for x in f_sequence_array:
            print(np.convolve(x, x))
            res += np.convolve(x, x)
        res = np.abs(res)
        res **= 2
        return res.sum()

    @classmethod
    def split(cls, f_sequence, split_points):
        f_sequence_array = np.array([])
        size = f_sequence.shape
        pre_point = 0
        for point in split_points:
            now_f_sequence = [0] * pre_point
            now_f_sequence.extend(f_sequence_array[pre_point + 1, split_points])
            now_f_sequence.extend([0] * size - split_points)
            np.append(f_sequence_array, now_f_sequence)
            pre_point = point
        return f_sequence_array

    @classmethod
    def split_normal(cls, f_sequence):
        return []

    @classmethod
    def get_array(cls, audio_clip):
        t = np.linspace(0,
                        audio_clip.size / settings.OUT_FS,
                        num=audio_clip.size)
        carry = np.sin(2 * np.pi * cls.f_c * t)

        # 左声道部分信号生成
        re_left = carry * audio_clip  # *为星乘，@为点乘

        f_sequence = np.fft.fft(re_left)

        tmp_array = cls.split_normal(f_sequence)

        output_array = np.array([])
        for now_f_sequence in tmp_array:
            np.append(output_array, np.fft.ifft(now_f_sequence))

        np.append(output_array, carry)
        return output_array
