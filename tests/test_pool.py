from utils.pool import *

import numpy as np
import threading,time

def run():
    a = PoolBlockGet()
    b = PoolBlockPut()
    class ThreadA(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)

        def run(self):
            for i in range(15):
                time.sleep(1)
                a.put(np.random.rand(100))
                print("A put")

       

    class ThreadB(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)

        def run(self):
            for i in range(2):
                tmp = a.get(500)
                print("B get",type(tmp))


    p = ThreadA()
    g = ThreadB()
    p.daemon = True



    
    g.daemon = True

    p.start()
    g.start()

    tmp = input("")
    # p.stop()
    # g.stop()
   
