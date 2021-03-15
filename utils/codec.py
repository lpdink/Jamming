import logging
import pyaudio
import numpy as np


class Codec():
    # 将bytes类型的字节流转换为归一化的float ndarray
    @staticmethod
    def decode_bytes_to_audio(bytes_buffer, input_channel, input_bit_depth):
        # 检查
        if not isinstance(bytes_buffer, bytes):
            logging.error("Input buffer must be bytes!")
            return bytes_buffer

        if input_channel not in (1, 2):
            raise ValueError("Input channel must be 1 or 2!")

        # 根据输入类型确定split步长
        if input_bit_depth == 16:
            split_step = 2 * input_channel
            max_value = 2**15
        elif input_bit_depth == 24:
            split_step = 3 * input_channel
            max_value = 2**23
        elif input_bit_depth == 32:
            split_step = 4 * input_channel
            max_value = 2**31

        if input_channel == 1:
            # 获取声道信息
            channel = []
            length = len(bytes_buffer)
            for i in range(0, length, split_step):
                channel.append(bytes_buffer[i:i + split_step])

            # 转化为ndarray并且归一化
            channel = np.array([
                int.from_bytes(xi, byteorder='little', signed=True)
                for xi in channel
            ]).astype(np.float64)
            channel = channel / max_value
            re = channel

            return re
        else:
            # 左右声道拆分
            left_channel = []
            right_channel = []
            length = len(bytes_buffer)
            for i in range(0, length, split_step):
                left_channel.append(bytes_buffer[i:i + int(split_step / 2)])
                right_channel.append(bytes_buffer[i + int(split_step / 2):i +
                                                  split_step])

            # 转化为ndarray并且归一化
            left_channel = np.array([
                int.from_bytes(xi, byteorder='little', signed=True)
                for xi in left_channel
            ]).astype(np.float64)
            left_channel = left_channel / max_value
            re_left = left_channel

            right_channel = np.array([
                int.from_bytes(xi, byteorder='little', signed=True)
                for xi in right_channel
            ]).astype(np.float64)
            right_channel = right_channel / np.max(np.abs(right_channel))
            re_right = right_channel

            return (re_left, re_right)

    # 将float类型的ndarray根据扬声器采样深度编码为可以发送的bytes
    @staticmethod
    def encode_audio_to_bytes(audio_clip, output_channel, output_bit_depth):
        if output_channel not in (1, 2):
            raise ValueError("Input channel must be 1 or 2!")

        if output_channel == 1:
            # 单声道检查
            if not isinstance(audio_clip, np.ndarray):
                raise TypeError("Input audio clip must be numpy array!")

            if audio_clip.dtype not in (np.float64, np.float32, np.float16):
                raise TypeError("Input audio clip must be float numpy!")
        else:
            # 双声道检查
            audio_clip_left = audio_clip[0]
            audio_clip_right = audio_clip[1]
            if not isinstance(audio_clip_left, np.ndarray) or not isinstance(
                    audio_clip_right, np.ndarray):
                raise TypeError("Input audio clip must be numpy array!")

            if audio_clip_left.dtype not in (
                    np.float64, np.float32,
                    np.float16) or audio_clip_right.dtype not in (np.float64,
                                                                  np.float32,
                                                                  np.float16):
                raise TypeError("Input audio clip must be float numpy!")

            if audio_clip_left.shape != audio_clip_right.shape:
                raise ValueError("Shape of input audio clip must be the same!")

            # 左右声道填充
            audio_clip = []
            for i in range(audio_clip_left.size):
                audio_clip.append(audio_clip_left[i])
                audio_clip.append(audio_clip_right[i])
            audio_clip = np.array(audio_clip)

        # 根据扬声器采样深度进行转化
        if output_bit_depth == 16:
            re = (audio_clip * 2**15).clip(-2**15, 2**15 - 1).astype(
                np.int16).tobytes()
        elif output_bit_depth == 24:
            re = b""
            for i in range(audio_clip.size):
                tmp = int((audio_clip[i] * 2**23).clip(-2**23, 2**23 - 1))
                re += tmp.to_bytes(3, byteorder='little', signed=True)
        elif output_bit_depth == 32:
            re = (audio_clip * 2**31).clip(-2**31, 2**31 - 1).astype(
                np.int32).tobytes()
        else:
            raise TypeError("Input audio clip type error!")

        return re