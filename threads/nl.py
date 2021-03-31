import threading, wave, math
import numpy as np

import global_var
from utils.codec import Codec
from utils.resampler import Resampler


class NoiseLib(threading.Thread):
    def __init__(self, out_fs, noise_length, chirp_length):
        threading.Thread.__init__(self)
        # 配置噪声库
        self.daemon = True
        self.exit_flag = False  # 线程退出标志
        self.out_fs = out_fs
        self.noise_length = noise_length
        self.chirp_length = chirp_length
        self.f_lower_bound = 100  # 噪声频率下界
        self.f_upper_bound = 1000  # 噪声频率上界
        self.num_of_base = 30  # 噪声基底个数
        self.f1 = 100
        self.f2 = 1e4
        self.up_chirp_frames, self.down_chirp_frames = self._generate_chirp()
        self.noise_frames = np.array([])
        # self._load_wave("./waves/raw/no_yes.wav")
        # 开始运行线程
        self.start()

    def run(self):
        while not self.exit_flag:
            # 1.重新生成随机噪声
            self.noise_frames = self._generate_noise()
            chirp_noise_frames = np.concatenate(
                (self.up_chirp_frames, self.noise_frames))

            # 2.chirp和噪声存入noise池。该过程可能会被阻塞，直到池中数据不够下一次由另外一线程读取
            global_var.noise_pool.put(chirp_noise_frames)
            # global_var.noise_pool.put(self.test_wave[-1])  # Test

    def stop(self):
        self.exit_flag = True
        self.join()

    # 每次生成不同噪声库噪声
    def _generate_noise(self):
        noise_frames_count = math.floor(self.out_fs * self.noise_length)
        random_factor = np.random.rand(self.num_of_base)
        # print(random_factor)
        # random_factor = np.ones((self.num_of_base))  # Test
        w_bases = np.linspace(self.f_lower_bound, self.f_upper_bound,
                              self.num_of_base)
        t = np.linspace(0, self.noise_length, num=noise_frames_count)
        random_noise = np.zeros(shape=noise_frames_count)
        for i in range(self.num_of_base):
            random_noise += random_factor[i] * np.sin(
                2 * np.pi * w_bases[i] * t)
        random_noise = random_noise / np.max(np.abs(random_noise))

        return random_noise

    def _generate_chirp(self):
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

    def _load_wave(self, filename):
        # 根据文件名读取音频文件
        try:
            wf = wave.open(filename, "rb")
            nchannels = wf.getparams().nchannels
            sampwidth = wf.getparams().sampwidth
            framerate = wf.getparams().framerate
            nframes = wf.getparams().nframes
            bytes_buffer = wf.readframes(nframes)  # 一次性读取所有frame

            audio_clip = Codec.decode_bytes_to_audio(bytes_buffer, nchannels,
                                                     sampwidth * 8)

            audio_clip = Resampler.resample(audio_clip, framerate, self.out_fs)

            self.test_wave = [filename, 2, sampwidth, self.out_fs, audio_clip]
        except:
            raise TypeError("Can't read wave file!")

    def get_chirp_noise(self, dst_fs):
        return Resampler.resample(
            np.concatenate((self.up_chirp_frames, self.noise_frames)),
            self.out_fs, dst_fs)

    def get_down_chirp(self, dst_fs):
        return Resampler.resample(self.down_chirp_frames, self.out_fs, dst_fs)
