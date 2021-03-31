import threading,time

class T1(threading.Thread):
    def __init__(self):
        super(T1,self).__init__()

        self.start()

    def run(self):
        print("T1!")
        time.sleep(10)

    def get_str(self):
        return "***"

class T2(threading.Thread):
    def __init__(self,t1):
        super(T2,self).__init__()
        self.t1 = t1

        self.start()

    def run(self):
        time.sleep(1)
        print(self.t1.get_str())

if __name__=="__main__":
    t1 = T1()
    t2 = T2(t1)

    t1.join()
    t2.join()