import time, logging
import pyaudio
import numpy as np
import matplotlib.pyplot as plt

import global_var, settings
from utils.codec import Codec
from utils.modulate import Modulate


class InputOutPut():
    def __init__(self, input_bit_depth, input_channel, input_fs, output_bit_depth,
                 output_channel, output_fs, frames_per_buffer):
        InputOutPut.input_bit_depth = input_bit_depth
        InputOutPut.input_channel = input_channel
        InputOutPut.input_fs = input_fs
        InputOutPut.output_bit_depth = output_bit_depth
        InputOutPut.output_channel = output_channel
        InputOutPut.output_fs = output_fs
        InputOutPut.frames_per_buffer = frames_per_buffer
        self.run()

    def run(self):
        self.pa = pyaudio.PyAudio()
        try:
            self.stream = self.pa.open(
                format=self.pa.get_format_from_width(InputOutPut.input_bit_depth//8),
                channels=InputOutPut.input_channel,
                rate=InputOutPut.input_fs,
                input=True,
                output=False,
                frames_per_buffer=InputOutPut.frames_per_buffer,
                stream_callback=InputOutPut.read_audio)
        except:
            logging.warning("No input device detected!")
        try:
            self.stream = self.pa.open(
                format=self.pa.get_format_from_width(InputOutPut.output_bit_depth//8),
                channels=InputOutPut.output_channel,
                rate=InputOutPut.output_fs,
                input=False,
                output=True,
                frames_per_buffer=InputOutPut.frames_per_buffer,
                stream_callback=InputOutPut.write_audio)
        except:
            logging.warning("No output device detected!")

        self.stream.start_stream()

    def stop(self):
        # 关闭时可能超时，所以使用try
        try:
            self.stream.stop_stream()
            self.stream.close()
            self.pa.terminate()
        except:
            pass

    @staticmethod
    def read_audio(in_data, frame_count, time_info, status):
        # 1.将bytes流输入转换为[-1,1]的浮点数一维数组
        raw_input_frames = Codec.decode_bytes_to_audio(
            in_data, InputOutPut.input_channel, InputOutPut.input_bit_depth)
        # 2.数据存入raw_input池，此过程不会被阻塞
        global_var.raw_input_pool.put(raw_input_frames)
        # 3.更新系统时间
        global_var.run_time = global_var.run_time + InputOutPut.frames_per_buffer / InputOutPut.input_fs

        return (None, pyaudio.paContinue)

    @staticmethod
    def write_audio(in_data, frame_count, time_info, status):
        # 1.如果keyword池非空，则读取数据。若数据长度不够本次输出，则再从noise池中读取一定长度数据，进行拼接补长。跳3
        if not global_var.keyword_pool.is_empty():
            raw_output_frames = global_var.keyword_pool.get(frame_count)
            if raw_output_frames.size < frame_count:
                raw_output_frames = np.concatenate(
                    (raw_output_frames,
                     global_var.noise_pool.get(frame_count -
                                               raw_output_frames.size)))
        # 2.如果keyword池为空，直接读取nosie池中数据。跳3
        else:
            raw_output_frames = global_var.noise_pool.get(frame_count)

        # 3.调制
        modulated_output_frames = Modulate.am_modulate(raw_output_frames)

        # 4.将[-1,1]的浮点数一维数组转换为bytes流输出
        out_data = Codec.encode_audio_to_bytes(modulated_output_frames,
                                               InputOutPut.output_channel,
                                               InputOutPut.output_bit_depth)

        return (out_data, pyaudio.paContinue)