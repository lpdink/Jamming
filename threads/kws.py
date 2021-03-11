import threading, logging
import global_var
import numpy as np


class KeywordSpotting(threading.Thread):
    def __init__(self, in_fs, out_fs, mute_period_frames_count):
        threading.Thread.__init__(self)
        self.daemon = True
        self.in_fs = in_fs
        self.out_fs = out_fs
        self.mute_period_frames_count = mute_period_frames_count
        self.kws_frames_count = 500  # 暂定，根据实际情况进行改变
        self.exit_flag = False

        self.start()

    def run(self):
        while not self.exit_flag:
            # 1.从raw_input池中读取一定长度的数据。该过程可能会被阻塞，直到池中放入了足够本次读取的数据
            processed_input_frames = global_var.processed_input_pool.get(
                int(self.kws_frames_count))

            # 2.如果keyword spotting检测出该数据段中存在关键字，则对该数据进行重采样，填充后，存入keyword池
            if self.kws(processed_input_frames):
                global_var.keyword_pool.put(
                    self.padding(
                        self.resampling(processed_input_frames, self.in_fs,
                                        self.out_fs), 0,
                        self.mute_period_frames_count))

    def stop(self):
        self.exit_flag = True
        self.join()

    def kws(self, frames):
        logging.info("System Clock-{}(s)-Keyword spooting success".format(
            round(global_var.run_time, 2)))
        return True

    def resampling(self, frames, current_fs, target_fs):
        return np.array([])

    def padding(self, frames, padding_value, padding_num):
        return np.random.rand(1000)


# class ASRManager(object):
#     def __init__(self):
#         super(ASRManager, self).__init__()
#         self.asr_threads = []
#         self.dll_path = "ASR.dll"

#     def create_asr_thread(self):
#         asr_thread = ASRThread(self.dll_path)
#         asr_thread.run()
#         self.asr_threads.append(asr_thread)

#     def kill_all(self):
#         for asr_thread in self.asr_threads:
#             asr_thread.stop()
#             self.asr_threads.remove(asr_thread)

# class ASRThread(threading.Thread):
#     def __init__(self, dll_path):
#         super(ASRThread, self).__init__()

#         self.c = ctypes.CDLL(dll_path)

#     def run(self):
#         # 获取声音片段
#         sound = global_var.send_data.get()
#         # 数据类型转换：float ndarray->（C）void*
#         sound.ctypes.data_as(ctypes.POINTER(ctypes.c_void_p))
#         # 调用c中函数，返回值为c中true和false，在python中是0，1
#         back = self.c.function(sound)
#         if (back != 0):
#             global_var.lock_ars.acquire()
#             global_var.is_jamming = False
#             global_var.keyword_cache = sound
#             global_var.lock_ars.release()
#             print("success")
#         print("run")

#     def stop(self):
#         # self.__flag.set()  # 将线程从暂停状态恢复, 如何已经暂停的话
#         # self.__running.clear()  # 设置为False
#         pass