import abc, threading, random
import sounddevice as sd
import numpy as np

import global_var
from utils.anc import ActiveNoiseControl
from utils.codec import Codec
from utils.modulate import Modulate


class SoundDeviceInput(threading.Thread):
    def __init__(self, nosie_lib, in_fs, in_channel, in_bit_depth,
                 chirp_nosie_length, simulation_length):
        threading.Thread.__init__(self)
        # 初始化配置
        self.daemon = True
        self.exit_flag = False
        self.noise_lib = nosie_lib
        self.in_fs = in_fs
        self.in_channel = in_channel
        self.in_bit_depth = in_bit_depth
        self.chirp_nosie_frames_count = int(chirp_nosie_length * in_fs)
        self.simulation_length = simulation_length
        params = {
            "samplerate": in_fs,
            "channels": in_channel,
            "dtype": np.float32,
        }

        # 为输入设备创建输入流
        self.stream = sd.InputStream(**params)
        # 开始线程
        self.start()

    def run(self):
        self.stream.start()
        while not self.exit_flag:
            # 1.读取输入音频数据。此过程会阻塞，直到有足够多的数据
            frames, _ = self.stream.read(self.chirp_nosie_frames_count)
            frames = np.squeeze(frames)

            # 3.输入定位
            located_frames = ActiveNoiseControl.location(
                frames, self.noise_lib.get_down_chirp(self.in_fs))

            # 4.信道估计 or 噪声消除
            if global_var.run_time < self.simulation_length:
                ActiveNoiseControl.channel_simulation(
                    located_frames, self.noise_lib.get_chirp_noise(self.in_fs))
            else:
                processed_input_frames = ActiveNoiseControl.eliminate_noise(
                    located_frames, self.noise_lib.get_chirp_noise(self.in_fs))
                global_var.processed_input_pool.put(processed_input_frames)

            # 5.更新系统时间
            global_var.run_time += self.chirp_nosie_frames_count / self.in_fs
        self.stream.stop()
        self.stream.close()

    def stop(self):
        self.exit_flag = True
        self.join()


class SoundDeviceOutput(threading.Thread):
    def __init__(self, out_fs, out_channel, out_bit_depth, frames_per_buffer,
                 usb_card_keyword):
        threading.Thread.__init__(self)
        # 初始化配置
        self.daemon = True
        self.exit_flag = False
        self.out_fs = out_fs
        self.out_channels = out_channel
        self.out_bit_depth = out_bit_depth
        self.frames_per_buffer = frames_per_buffer
        params = {
            "samplerate": out_fs,
            "device": None,
            "channels": out_channel,
            "dtype": np.float32,
        }

        # 为当前所有可用输出设备创建输出流
        self.devices = OutputDeviceIterable(usb_card_keyword)
        self.streams = StreamsIterable()
        for index, info in self.devices:
            print(index, info["name"])
            params["device"] = index
            self.streams.append(sd.OutputStream(**params))
        self.start()

    def run(self):
        for stream in self.streams:
            stream.start()
        while not self.exit_flag:
            # 1.如果keyword池非空，则读取数据。跳3
            if not global_var.keyword_pool.is_empty():
                raw_output_frames = global_var.keyword_pool.get(
                    self.frames_per_buffer)
            # 2.如果keyword池为空，直接读取noise池中数据。跳3
            else:
                raw_output_frames = global_var.noise_pool.get(
                    self.frames_per_buffer)

            # 3.调制
            modulated_output_frames = Modulate.am_modulate(
                raw_output_frames, 2, self.out_fs)
            out_data = np.float32(
                np.stack(
                    (modulated_output_frames[0], modulated_output_frames[1]),
                    1))

            # 5.分声道输出
            for i, stream in enumerate(self.streams):
                stream.write(out_data)  # 此过程会阻塞，直到填入数据被全部消耗
        for stream in self.streams:
            stream.stop()
            stream.close()

    def stop(self):
        self.exit_flag = True
        self.join()


class DeviceIterable(abc.ABC):
    def __init__(self):
        self.index_infoss = []

    @abc.abstractmethod
    def _get_devices_by_keyword(self, device_keyword):
        pass


class OutputDeviceIterable(DeviceIterable):
    def __init__(self, device_keyword="Realtek USB2.0 Audio"):
        super(OutputDeviceIterable, self).__init__()
        self._get_devices_by_keyword(device_keyword)
        print("Output", self.index_infoss)

    def _get_devices_by_keyword(self, device_keyword):
        self.index_infoss = list(
            filter(
                lambda index_info: device_keyword in index_info[-1]["name"] and
                index_info[-1]["max_output_channels"] == 2,
                enumerate(sd.query_devices())))
        del self.index_infoss[-1]

    # 迭代对象最简单写法，无需迭代器。index自动从0开始递增
    def __getitem__(self, index):
        return self.index_infoss[index]


class InputDeviceIterable(DeviceIterable):
    def __init__(self, device_keyword="Realtek(R) Audio"):
        super(InputDeviceIterable, self).__init__(
        )  # 继承父类构造方法，也可写成DeviceIterable.__init__(self,*args)
        self._get_devices_by_keyword(device_keyword)
        print("Input", self.index_infoss)

    def _get_devices_by_keyword(self, device_keyword):
        pass

    # __iter__要求必须返回迭代器。带有yield，当作生成器，即迭代器。
    def __iter__(self):
        for index, _ in self.index_infoss:
            yield index


class StreamsIterable():
    def __init__(self):
        self.streams = []

    def __repr__(self):
        return "Streams count [{}]".format(len(self.streams))

    # 返回迭代器，传统写法
    def __iter__(self):
        return StreamsIterator(self.streams)

    def append(self, stream):
        self.streams.append(stream)


class StreamsIterator():
    def __init__(self, streams):
        self.streams = streams
        self.index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            stream = self.streams[self.index]
        except IndexError:
            raise StopIteration()
        self.index += 1
        return stream