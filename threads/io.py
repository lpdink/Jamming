import time, logging
import pyaudio
import numpy as np
import matplotlib.pyplot as plt

import global_var, settings
from utils.codec import Codec
from utils.modulate import Modulate


class InputOutPut():
    def __init__(self, input_format, input_channel, input_fs, output_format,
                 output_channel, output_fs, frames_per_buffer):
        self.input_format = input_format
        self.input_channel = input_channel
        self.input_fs = input_fs
        self.output_format = output_format
        self.output_channel = output_channel
        self.output_fs = output_fs
        self.frames_per_buffer = frames_per_buffer
        self.run()

    def run(self):
        self.pa = pyaudio.PyAudio()
        try:
            self.stream = self.pa.open(
                format=self.input_format,
                channels=self.input_channel,
                rate=self.input_fs,
                input=True,
                output=False,
                frames_per_buffer=self.frames_per_buffer,
                stream_callback=InputOutPut.read_audio)
        except:
            logging.warning("No input device detected!")
        try:
            self.stream = self.pa.open(
                format=self.output_format,
                channels=self.output_channel,
                rate=self.output_fs,
                input=False,
                output=True,
                frames_per_buffer=self.frames_per_buffer,
                stream_callback=InputOutPut.write_audio)
        except:
            logging.warning("No output device detected!")

        self.stream.start_stream()

    def stop(self):
        # y = np.array([])
        # for i in range(10):
        #     y = np.append(y, NoiseLib.get_noise_clip(10000),axis=0)
        # plt.plot(y)
        # plt.show()
        # noise_clip = InputOutput.decode_single_channel(
        #     NoiseLib.get_wave_bytes_buffer(0))

        # noise_clip = Modulate.am_modulate_single_channel(noise_clip)
        # out_data = InputOutput.encode_single_channel(noise_clip)
        # import wave
        # wf1 = wave.open(r".\waves\modulated\yes_no_left.wav", "wb")
        # # wf2 = wave.open(r".\waves\modulated\yes_no_right.wav","wb")

        # wf1.setnchannels(1)
        # wf1.setsampwidth(3)
        # wf1.setframerate(8000)
        # wf1.writeframes(out_data)

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
        raw_input_frames = Codec.decode_bytes_to_audio(in_data)
        # 2.数据存入raw_input池，此过程不会被阻塞
        global_var.raw_input_pool.put(raw_input_frames)

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
        out_data = Codec.encode_audio_to_bytes(modulated_output_frames)

        return (out_data, pyaudio.paContinue)