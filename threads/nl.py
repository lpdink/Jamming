import threading, time, os, logging, wave, math
import pyaudio
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

import global_var, settings
from utils.codec import Codec
from utils.modulate import Modulate


class NoiseLib(threading.Thread):
    def __init__(self, out_fs, noise_length, chirp_length):
        threading.Thread.__init__(self)
        # 配置噪声库
        self.daemon = True
        self.out_fs = out_fs
        self.noise_length = noise_length
        self.chirp_length = chirp_length
        self.f_lower_bound = 100  # 噪声频率下界
        self.f_upper_bound = 1000  # 噪声频率上界
        self.num_of_base = 5  # 噪声基底个数
        self.f1 = 100
        self.f2 = 1e4
        self.exit_flag = False  # 线程退出标志
        NoiseLib.up_chirp_frames, NoiseLib.down_chirp_frames = self.generate_chirp(
        )
        NoiseLib.noise_frames = np.array([])
        # 生成chirp信号
        self.generate_chirp()
        # 读取音频文件
        self.load_wave("./waves/raw/no_yes.wav")
        # 开始运行线程
        self.start()

    def run(self):
        while not self.exit_flag:
            # 1.重新生成随机噪声
            NoiseLib.noise_frames = self.generate_noise()
            chirp_noise_frames = np.concatenate(
                (NoiseLib.up_chirp_frames, NoiseLib.noise_frames))

            # 2.chirp和噪声存入noise池。该过程可能会被阻塞，直到池中数据不够下一次由另外一线程读取
            # global_var.noise_pool.put(chirp_noise_frames)
            global_var.noise_pool.put(self.test_wave[-1])  # Test

    def stop(self):
        self.exit_flag = True
        self.join()

    # 每次生成不同噪声库噪声
    def generate_noise(self):
        noise_frames_count = math.floor(self.out_fs * self.noise_length)
        random_factor = np.random.rand(self.num_of_base)
        # random_factor = np.ones((self.num_of_base))  # Test
        w_bases = np.linspace(self.f_lower_bound, self.f_upper_bound,
                              self.num_of_base)
        t = np.linspace(0, self.noise_length, num=noise_frames_count)
        random_noise = np.zeros(shape=(noise_frames_count))
        for i in range(self.num_of_base):
            random_noise += random_factor[i] * np.sin(
                2 * np.pi * w_bases[i] * t)
        random_noise = random_noise / np.max(np.abs(random_noise))

        return random_noise

    def generate_chirp(self):
        t = np.linspace(0,
                        self.chirp_length,
                        num=math.floor(self.out_fs * self.chirp_length))
        up_chirp = np.cos(2 * np.pi * self.f1 * t +
                          (np.pi *
                           (self.f2 - self.f1) / self.chirp_length) * t**2)
        down_chirp = np.cos(2 * np.pi * self.f2 * t -
                            (np.pi *
                             (self.f2 - self.f1) / self.chirp_length) * t**2)
        return up_chirp, down_chirp

    @classmethod
    def get_chirp_noise(cls):
        return np.concatenate(
            (NoiseLib.up_chirp_frames, NoiseLib.noise_frames))

    @classmethod
    def get_down_chirp(cls):
        return NoiseLib.down_chirp_frames

    def load_wave(self, filename):
        # 根据文件名读取音频文件
        try:
            wf = wave.open(filename, "rb")
            print(wf.getparams())
            nchannels = wf.getparams().nchannels
            sampwidth = wf.getparams().sampwidth
            framerate = wf.getparams().framerate
            nframes = wf.getparams().nframes
            bytes_buffer = wf.readframes(nframes)  # 一次性读取所有frame

            audio_clip = Codec.decode_bytes_to_audio(bytes_buffer, nchannels,
                                                     sampwidth*8)

            audio_clip = signal.resample(
                audio_clip, int(self.out_fs / framerate * nframes))

            self.test_wave = [filename, 2, sampwidth, self.out_fs, audio_clip]
        except:
            raise TypeError("Can't read wave file!")

    # def save_wave(self):
    #     modulated_wave_dir = os.path.join(".\waves", "modulated")
    #     for raw_wave in self.raw_waves:
    #         filename = raw_wave[0]
    #         nchannels = raw_wave[1]
    #         sampwidth = raw_wave[2]
    #         framerate = raw_wave[3]
    #         audio_clip = raw_wave[4]
    #         bytes_buffer = Codec.encode_audio_to_bytes(audio_clip, 2,
    #                                                    pyaudio.paInt16)

    #         wf = wave.open(os.path.join(modulated_wave_dir, filename), "wb")
    #         wf.setnchannels(nchannels)
    #         wf.setsampwidth(sampwidth)
    #         wf.setframerate(framerate)
    #         wf.writeframes(bytes_buffer)

    #         wf.close()

    # print(r"\x"+r" \x".join(format(x,'02x') for x in NoiseLib.raw_noise_data[0][7200:7220]))  # 原始十六进制表示

    # # 获取bytes类型的声音信号
    # @classmethod
    # def get_wave_bytes_buffer(cls, index, frame_count=-1):
    #     if frame_count == -1:
    #         return cls.raw_noise_data[index][-1]

    #     read_index, sampwidth, nframes, data = cls.raw_noise_data[index]
    #     start_index = read_index
    #     end_index = read_index + frame_count * sampwidth
    #     if end_index >= nframes:
    #         re = data[start_index:-1] + data[0:end_index % nframes]
    #     else:
    #         re = data[start_index:end_index]
    #     cls.raw_noise_data[index][0] = end_index % nframes
    #     return re