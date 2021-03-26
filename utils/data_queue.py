import threading

import numpt as np
from threading import Condition


class DataQueue():
    def __init__(self):
        self.condition = threading.Condition()
        self.datas = []

    # 获取全部数据
    def get_all(self):
        re = self.datas.copy()
        self.datas = []
        return re

    # 清空pool
    def clear(self):
        self.datas = []

    # 判断pool是否为空
    def is_empty(self):
        if len(self.datas) == 0:
            return True
        else:
            return False

    # 获取queue大小
    def size(self):
        return len(self.datas)

    def put(self, data):
        self.datas.append(data)

    def get(self, count):
        if count > len(self.datas):
            count = len(self.datas)
        re = self.datas[0:count].copy()
        self.datas = np.delete(self.datas, range(0, count))
        return re