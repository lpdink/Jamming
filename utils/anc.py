import threading, time, math, logging, global_var
import numpy as np
from scipy import signal

import global_var, settings
from threads.nl import NoiseLib

import matplotlib.pyplot as plt


class ActiveNoiseControl():
    def __init__(self, out_fs, in_fs, chirp_noise_length,
                 simulation_length):
        self.output_fs = out_fs
        self.input_fs = in_fs
        self.chirp_noise_length = chirp_noise_length
        self.simulation_length = simulation_length
        self.H = np.array([])

    def anc(self, raw_input_frames: bytes) -> np.ndarray:
        # Test
        # self.c1 = 0
        # self.c2 = 0
        # self.tmp = np.array([])

        # 1.包络检测，并找到最大值点下标。用于同步
        max_index = self.find_max(
            self.envelope(
                raw_input_frames,
                self._resample(NoiseLib.get_down_chirp(), self.output_fs,
                               self.input_fs)))

        # 2.从last_input池中读取保存的上轮右半数据
        last_input_frames = global_var.history_queue.get_all()

        # 3.将本轮数据的右半保存至last_input池
        global_var.last_input_pool.put(raw_input_frames[max_index:])

        # 4.拼接上轮右半数据核本轮左半数据
        joined_input_frames = np.concatenate(
            (last_input_frames, raw_input_frames[0:max_index]))

        # 5.如果系统刚启动，则进行信道估计，更新self.H
        if global_var.run_time <= self.simulation_length:
            self.channel_simulation(
                joined_input_frames,
                self._resample(NoiseLib.get_chirp_noise(), self.output_fs,
                               self.input_fs))
            return None
        # 6.如果已经完成信道估计，则使用self.H核和噪声库噪声来进行噪声消除
        else:
            return self.eliminate_noise(
                joined_input_frames,
                self._resample(NoiseLib.get_chirp_noise(), self.output_fs,
                               self.input_fs))

    def envelope(self, frames, chirp):
        # 包络检测模块。会将frames分段与chirp信号进行卷积
        # frames：输入原始信号
        # chirp：用于解调原始信号的卷积信号
        # res：返回的卷积结果
        N1 = len(frames)
        N2 = len(chirp)

        res = []
        i = 0
        while i < N1:
            N = min(N2, N1 - i)
            frames_freq = np.fft.fft(frames[i:i + N])
            chirp_freq = np.fft.fft(chirp[0:N])
            tmp = frames_freq * chirp_freq
            tmp = list(np.zeros((math.floor(N / 2) + 1))) + list(
                tmp[math.floor(N / 2) - 1:N + 1] * 2)
            res = res + list(abs(np.fft.ifft(tmp)))[0:N - 1]
            i = i + N2

        return np.array(res)

    def find_max(self, frames):
        # 若Clip中有一个最大值点，则输出其下标。若有两个值大小差距在阈值(0.3)以内的最大值点，则输出其下标的中位点
        # frames：需要检测最大值点的输入声音片段
        # max_index：返回的最大值点下标
        first_max_index = 0
        for i in range(1, len(frames)):
            if frames[i] > frames[first_max_index]:
                first_max_index = i

        second_max_index = 0
        for i in range(1, len(frames)):
            if frames[i] > frames[second_max_index] and i != first_max_index:
                second_max_index = i

        threshold = 0.3
        if frames[first_max_index] / frames[second_max_index] <= 1 + threshold:
            max_index = math.floor((first_max_index + second_max_index) / 2)
        else:
            max_index = first_max_index
        return max_index

    def channel_simulation(self, reality_frames, ideal_frames):
        logging.info("System Clock-{}(s)-Channel simulation".format(
            round(global_var.run_time, 2)))
        print(len(reality_frames), len(ideal_frames))
        # self.tmp = np.concatenate((self.tmp,ideal_frames))
        # self._save_data(reality_frames,
        #                 "./tests/saved/train_x{}.npy".format(self.c1))
        # self._save_data(ideal_frames,
        #                 "./tests/saved/train_y{}.npy".format(self.c1))
        # self.c1 += 1

    def eliminate_noise(self, reality_frames, ideal_frames):
        logging.info("System Clock-{}(s)-Eliminate noise".format(
            round(global_var.run_time, 2)))
        print(len(reality_frames), len(ideal_frames))
        # self._save_data(reality_frames,
        #                 "./tests/saved/test_x{}.npy".format(self.c2))
        # self._save_data(ideal_frames,
        #                 "./tests/saved/test_y{}.npy".format(self.c2))
        # self.c2 += 1
        return reality_frames

    def _resample(self, frames, src_fs, dst_fs):
        return signal.resample(frames, int(frames.size / src_fs * dst_fs))

    def _save_data(self, data, save_fillname):
        np.save(save_fillname, data)
