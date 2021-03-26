import math
import random

import numpy as np
import logging

import settings


class Modulate():
    f_c = 40000  # 载波频率
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
        tmp = np.fft.fft(x, size)
        tmp = tmp * tmp
        tmp = np.fft.ifft(tmp)
        return tmp

    @classmethod
    def frequency_to_time(cls, sequence_array):
        # 频域转为时域
        audio_array = np.array([])
        for now_f_sequence in sequence_array:
            now_f_sequence = np.real(np.fft.ifft(now_f_sequence))
            audio_array = np.append(audio_array, now_f_sequence)

        audio_array = audio_array.reshape(sequence_array.shape)
        return audio_array

    @classmethod
    def get_leakage(cls, f_sequence, split_points):

        f_sequence_array = cls.split(f_sequence, split_points)
        # 只计算FFT后频域的前一半
        length = f_sequence_array.shape[1] // 2
        size = 2 * length - 1

        res = np.zeros(size, dtype=np.complex128)
        count = f_sequence_array.shape[0]
        pre = 0
        for index in range(count - 1):
            now = split_points[index]
            convolve_sequence = cls.convolve(f_sequence_array[index][pre + 1:now + 1])
            now_size = convolve_sequence.size
            res[pre + 1:pre + now_size + 1] = res[pre + 1:pre + now_size + 1] + convolve_sequence
            pre = now
        res = np.abs(res)
        res **= 2
        return res.sum()

    @classmethod
    def split(cls, f_sequence, split_points):  # 根据分割点切分频率

        size = f_sequence.shape[0]
        split_points = split_points * (size // settings.OUT_FS)
        split_points = np.append(split_points, int(size // 2 - 1))

        num = split_points.size
        f_sequence_array = np.array([])

        pre_point = 0
        for point in split_points:
            now_f_sequence = np.zeros(size, dtype=np.complex128)

            # 对称切分频率
            now_f_sequence[pre_point + 1:point + 1] = f_sequence[pre_point + 1:point + 1]
            now_f_sequence[size - point - 1: size - pre_point] = f_sequence[size - point - 1: size - pre_point]

            # 处理直流分量
            if pre_point == 0:
                now_f_sequence[0] = f_sequence[0]

            f_sequence_array = np.append(f_sequence_array, now_f_sequence)
            pre_point = point

        f_sequence_array = f_sequence_array.reshape((num, size))
        return f_sequence_array

    @classmethod
    def split_normal(cls, audio_clip, split_points=np.array([50, 100, 1000, 4000, 10000], dtype=int)):
        # 时域转化为频域
        fft = np.fft.fft(audio_clip)
        f_sequence = fft

        # 切分频率
        tmp = cls.split(f_sequence, split_points)

        return cls.frequency_to_time(tmp)

    @classmethod
    def SA(cls, audio_clip):
        f_sequence = np.fft.fft(audio_clip)
        now_points = ans_points = np.array([50, 100, 1000, 4000, 10000], dtype=int)
        ans = cls.get_leakage(f_sequence, ans_points)
        T = 150
        tt = 1e-10
        d = 0.95
        while T > tt:
            nxt_points = now_points.copy()
            size = nxt_points.size
            for index in range(size - 1):
                if random.randint(0, 1) == 0:
                    if index == 0:
                        pre = 1
                    else:
                        pre = nxt_points[index - 1] + 1
                    nxt_points[index] = random.randint(pre, now_points[index])
                else:
                    nxt = nxt_points[index + 1] - 1
                    nxt_points[index] = random.randint(now_points[index], nxt)
            now_ans = cls.get_leakage(f_sequence, now_points)
            new_ans = cls.get_leakage(f_sequence, nxt_points)
            if new_ans > ans:
                ans = new_ans
                ans_points = nxt_points
            delta = now_ans - new_ans
            if delta > 0 or math.exp(delta / T) * 100000 > random.randint(0, 100000):
                now_points = nxt_points.copy()
            # print(now_points)
            T *= d
        print(ans_points)
        tmp = cls.split(f_sequence, ans_points)
        tmp = cls.frequency_to_time(tmp)
        return tmp

    @classmethod
    def get_array(cls, audio_clip):  # 调制并切分声波

        # 检查
        if not isinstance(audio_clip, np.ndarray):
            raise TypeError("Input audio clip must be numpy array!")
        if audio_clip.dtype not in (np.float64, np.float32, np.float16):
            raise TypeError("Input audio clip must be float numpy!")
        if audio_clip.ndim != 1:
            raise ValueError("Input message must be 1D!")
        if settings.OUTPUT_CHANNEL not in (1, 2):
            raise ValueError("Input channel must be 1 or 2!")

        # 产生载波
        size = audio_clip.size
        t = np.linspace(0, size / settings.OUT_FS, num=size)
        carry = np.sin(2 * np.pi * cls.f_c * t)

        # 切割音频
        audio_array = cls.split_normal(audio_clip)  # 固定切割点
        # audio_array = cls.SA(audio_clip) # SA优化减少leakage

        # 用载波对切割后的音频进行调制
        for i in range(audio_array.shape[0]):
            audio_array[i] = audio_array[i] * carry
        audio_array = np.row_stack((audio_array, carry))

        return audio_array
