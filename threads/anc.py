import threading, time
import numpy as np
import math

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
        # 包络检测模块。会将frames分段与chirp信号进行卷积
        # frames：输入原始信号
        # chirp：用于解调原始信号的卷积信号
        # res：返回的卷积结果
        N1=len(frames)
        N2=len(chirp)
        
        res=[]
        i=0
        while i<N1:
            N=min(N2,N1-i)
            frames_freq=np.fft.fft(frames[i:i+N])
            chirp_freq=np.fft.fft(chirp[0:N])
            tmp=frames_freq*chirp_freq
            tmp=np.zeros((1,math.floor(N/2)+1))+tmp[math.floor(N/2):N]*2
            res=res+abs(np.fft.ifft(tmp))

            i=i+N2

        return res

    def find_max(self, frames):
        # 若Clip中有一个最大值点，则输出其下标。若有两个值大小差距在阈值(0.3)以内的最大值点，则输出其下标的中位点
        # frames：需要检测最大值点的输入声音片段
        # max_index：返回的最大值点下标
        first_max_index=0
        for i in range(1,len(frames)):
            if frames[i]>frames[first_max_index]:
                first_max_index=i
        
        second_max_index=0
        for i in range(1,len(frames)):
            if frames[i]>frames[second_max_index] and i!=first_max_index:
                second_max_index=i

        threshold=0.3
        if frames[first_max_index]/frames[second_max_index]<=1+threshold:
            max_index=math.floor((first_max_index+second_max_index)/2)
        else:
            max_index=first_max_index
        
        return max_index

    def channel_simulation(self, reality_frames, ideal_frames):
        pass

    def eliminate_noise(self, reality_frames, ideal_frames):
        pass