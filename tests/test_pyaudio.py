import pyaudio, random, abc, threading


class PyaudioInput(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # 配置输入线程
        self.daemon = True
        self.exit_flag = False
        self.p = pyaudio.PyAudio()
        params = {
            "rate": 48000,
            "channels": 2,
            "format": self.p.get_format_from_width(2),
            "output": True,
            "frames_per_buffer": 2048,
            "start": False
        }

        # 为输入设备创建输入流
        self.stream = self.p.open(**params)
        self.start()

    def run(self):
        self.stream.start_stream()
        while not self.exit_flag:
            self.stream.read(10000)  # 此过程会阻塞，直到有足够多的数据
        self.stream.stop_stream()
        self.stream.close()

    def stop(self):
        self.exit_flag = True
        self.p.terminate()
        self.join()


class PyaudioOutput(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        # 配置输出线程
        self.daemon = True
        self.exit_flag = False
        self.p = pyaudio.PyAudio()
        params = {
            "rate": 48000,
            "channels": 2,
            "format": self.p.get_format_from_width(2),
            "output": True,
            "frames_per_buffer": 2048,
            "output_device_index": None,
            "start": False
        }

        # 为当前所有可用输出设备创建输出流
        self.devices = OutputDeviceIterable()
        self.streams = StreamsIterable()
        for device_index in self.devices:
            params["output_device_index"] = device_index
            self.streams.append(self.p.open(**params))
        self.start()

    def run(self):
        for stream in self.streams:
            stream.start_stream()
        while not self.exit_flag:
            for i, stream in enumerate(self.streams):
                data = bytes(int(random.random() * 256) for _ in range(10000))
                stream.write(data)  # 此过程会阻塞，直到填入数据被全部消耗
        for stream in self.streams:
            stream.stop_stream()
            stream.close()

    def stop(self):
        self.exit_flag = True
        self.p.terminate()
        self.join()


class DeviceIterable(abc.ABC):
    def __init__(self):
        self.devices_info = []

    @abc.abstractmethod
    def _get_devices_by_keyword(self, device_keyword, host_api):
        pass


class OutputDeviceIterable(DeviceIterable):
    def __init__(self, device_keyword="Realtek(R) Audio", host_api=1):
        super(OutputDeviceIterable, self).__init__()
        self._get_devices_by_keyword(device_keyword, host_api)

    def _get_devices_by_keyword(self, device_keyword, host_api):
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            print(dev_info)
            if device_keyword not in dev_info["name"]:
                continue
            if dev_info["maxOutputChannels"] > 0 and dev_info[
                    "hostApi"] == host_api:
                self.devices_info.append((dev_info["name"], dev_info["index"]))
        p.terminate()

    # 迭代对象最简单写法，无需迭代器。index自动从0开始递增
    def __getitem__(self, index):
        return self.devices_info[index][-1]


class InputDeviceIterable(DeviceIterable):
    def __init__(self, device_keyword="Realtek(R) Audio", host_api=1):
        super(InputDeviceIterable, self).__init__(
        )  # 继承父类构造方法，也可写成DeviceIterable.__init__(self,*args)
        self._get_devices_by_keyword(device_keyword, host_api)

    def _get_devices_by_keyword(self, device_keyword, host_api):
        p = pyaudio.PyAudio()
        for i in range(p.get_device_count()):
            dev_info = p.get_device_info_by_index(i)
            if device_keyword not in dev_info["name"]:
                continue
            if dev_info["maxInputChannels"] > 0 and dev_info[
                    "hostApi"] == host_api:
                self.devices_info.append(dev_info["name"], dev_info["index"])
        p.terminate()

    # __iter__要求必须返回迭代器。带有yield，当作生成器，即迭代器。
    def __iter__(self):
        index = 0
        for device_info in self.devices_info:
            yield device_info[-1]
            index += 1


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

if __name__=="__main__":
    pi = PyaudioInput()
    po = PyaudioOutput()

    input("Press any key to exit>>>")

    pi.stop()
    po.stop()
