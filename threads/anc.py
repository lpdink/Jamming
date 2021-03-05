import threading, time
import numpy as np

import global_var, settings
from threads.nl import NoiseLib


class ActiveNoiseControl(threading.Thread):
    def __init__(self, chirp_noise_frames_count, simulation_length):
        threading.Thread.__init__(self)
        self.chirp_noise_frames_count = chirp_noise_frames_count
        self.simulation_length = simulation_length
        self.H = np.array([])
        self.exit_flag = False

        self.start()

    def run(self):
        while not self.exit_flag:
            # 1.从raw_input池中读取与chirp加noise等长的数据。该过程可能会被阻塞，直到池中放入了足够本次读取的数据
            current_input_frames = global_var.raw_input_pool.get(
                self.chirp_noise_frames_count)

            # 2.包络检测，并找到最大值点下标。用于同步
            max_index = self.find_max(
                self.envelope(current_input_frames, NoiseLib.get_down_chirp()))

            # 3.从last_input池中读取保存的上轮右半数据
            last_input_frames = global_var.last_input_pool.get_all()

            # 4.将本轮数据的右半保存至last_input池
            global_var.last_input_pool.put(current_input_frames[max_index:])

            # 5.拼接上轮右半数据核本轮左半数据
            joined_input_frames = last_input_frames.extend(
                current_input_frames[0:max_index])

            # 6.如果系统刚启动，则进行信道估计，更新self.H
            if global_var.run_time <= self.simulation_length:
                self.channel_simulation(joined_input_frames,
                                        NoiseLib.get_chirp_noise())
            # 7.如果已经完成信道估计，则使用self.H核和噪声库噪声来进行噪声消除
            else:
                global_var.processed_input_pool.put(
                    self.eliminate_noise(joined_input_frames,
                                         NoiseLib.get_chirp_noise()))

    def stop(self):
        self.exit_flag = True
        self.join()

    def envelope(self, frames, chirp):
        pass

    def find_max(self, frames):
        pass

    def channel_simulation(self, reality_frames, ideal_frames):
        pass

    def eliminate_noise(self, reality_frames, ideal_frames):
        pass