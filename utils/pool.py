import logging
import numpy as np
from threading import Condition, Lock


class PoolBase(object):
    def __init__(self):
        self.datas = np.array([])

    # 获取全部数据
    def get_all(self):
        re = self.datas.copy()
        self.datas = np.array([])
        return re

    # 清空pool
    def clear(self):
        self.datas = np.array([])

    # 判断pool是否为空
    def is_empty(self):
        if len(self.datas) == 0:
            return True
        else:
            return False

    # 获取pool大小
    def size(self):
        return len(self.datas)


class PoolBlockGet(PoolBase):
    def __init__(self, needed_count):
        super(PoolBlockGet, self).__init__()
        self.condition = Condition()  # 用于实现线程通信
        self.needed_count = needed_count  # 读取所需数据数量

    # 将数据放入池子。若池子中有足够数据，则释放被阻塞线程
    def put(self, data):
        if not isinstance(data, np.ndarray):
            raise TypeError("Input data must be ndarray!")
        if data.ndim != 1:
            raise ValueError("Input data must be 1D!")

        self.condition.acquire()
        self.datas = np.concatenate((self.datas, data))
        if len(self.datas) >= self.needed_count:
            self.condition.notify_all()
        self.condition.release()

    # 若要求数量大于库存，则阻塞当前线程。否则非循环读取池子中数据
    def get(self, count):
        if count < 0:
            raise ValueError("Input count must >= 0!")
        if not isinstance(count, int):
            raise ValueError("Input count must be integer!")

        self.condition.acquire()
        if count > len(self.datas):  # 所需帧数大于总量，则让调用该方法线程进入等待队列，直到存在足够多数据
            self.needed_count = count
            self.condition.wait()
        re = self.datas[:count].copy()
        self.datas = np.delete(self.datas, range(0, count))
        self.condition.release()

        return re

    def release(self):
        self.condition.acquire()
        self.condition.notify_all()
        self.condition.release()


class PoolBlockPut(PoolBase):
    def __init__(self, needed_count):
        super(PoolBlockPut, self).__init__()
        self.condition = Condition()  # 用于实现线程通信
        self.needed_count = needed_count  # 下一次读取所需数据数量

    # 若池子中有足够数据，则阻塞当前线程，否则将数据放入池子
    def put(self, data):
        if not isinstance(data, np.ndarray):
            raise TypeError("Input data must be ndarray!")
        if data.ndim != 1:
            raise ValueError("Input data must be 1D!")

        self.condition.acquire()
        if len(self.datas) >= self.needed_count:
            self.condition.wait()
        self.datas = np.concatenate((self.datas, data))
        self.condition.release()

    # 非循环读取池子中数据。若取后剩余数据小于所需数量，则释放被阻塞线程
    def get(self, count):
        if count < 0:
            raise ValueError("Input count must >= 0!")
        if not isinstance(count, int):
            raise ValueError("Input count must be integer!")

        if count > len(self.datas):
            count = len(self.datas)
            logging.warning("IO is going to be close!")

        self.condition.acquire()
        re = self.datas[:count].copy()
        self.datas = np.delete(self.datas, range(0, count))
        self.needed_count = count
        if len(self.datas
               ) < 4*self.needed_count:  # 取后剩余数据不够下一次读取，释放被阻塞线程，让其继续生产数据
            self.condition.notify_all()
        self.condition.release()

        return re

    def release(self):
        self.condition.acquire()
        self.condition.notify_all()
        self.condition.release()


class PoolNoBlock(PoolBase):
    def __init__(self):
        super(PoolNoBlock, self).__init__()
        self.rw_mutex = Lock()  # 读写互斥锁

    # 将数据放入池子
    def put(self, data):
        if not isinstance(data, np.ndarray):
            raise TypeError("Input data must be ndarray!")
        if data.ndim != 1:
            raise ValueError("Input data must be 1D!")

        self.rw_mutex.acquire()
        self.datas = np.concatenate((self.datas, data))
        self.rw_mutex.release()

    # 非循环读取池子中数据。若frame_count大于池中数据重量，则读取所有数据
    def get(self, count):
        if count < 0:
            raise ValueError("Input count must >= 0!")
        if not isinstance(count, int):
            raise ValueError("Input count must be integer!")

        self.rw_mutex.acquire()
        if count > len(self.datas):
            count = len(self.datas)
        re = self.datas[:count].copy()
        self.datas = np.delete(self.datas, range(0, count))
        self.rw_mutex.release()

        return re


# class CyclePool(BasePool):
#     def __init__(self, capacity=np.inf):
#         super(CyclePool, self).__init__(capacity)
#         self.index = 0  # 获取数据下标缓存

#     # 循环读取池子中流数据，若要求数量大于库存，则会读取一部分相同数据
#     def get(self, frame_count):
#         if frame_count < 0:
#             raise ValueError("Input frame count must >= 0!")

#         if not isinstance(frame_count, int):
#             raise ValueError("Input frame count must be integer!")

#         self.rw_mutex.acquire()

#         start_index = self.index
#         end_index = start_index + frame_count

#         total_frame_count = self.frames.size
#         if total_frame_count == 0:
#             return np.zeros(shape=(frame_count))

#         re = []
#         for i in range(start_index, end_index, 1):
#             re.append(self.frames[i % total_frame_count])
#         self.index = end_index % total_frame_count
#         re = np.array(re)

#         self.rw_mutex.release()

#         return re

#     def get_all(self):
#         return self.frames.copy()