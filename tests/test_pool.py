# from utils.cycle_pool import CyclePool
# from utils.non_cycle_pool import NonCyclePool

# import numpy as np

# a = NonCyclePool(100)

# for i in range(1, 2):
#     a.put(np.random.rand(i))
#     for j in range(1, 100, 1):
#         if a.get(j).size != j:
#             print(a.size(), "get", j)


# print(a.index)

# print(a.get(20).size)
# print(a.index)

import threading,time


class A(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.lock = threading.Lock()
        self.start()

    def run(self):
        if self.lock.locked():
            self.lock.release()
        while True:
            print("*")
            time.sleep(1)

a = A()



