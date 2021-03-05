import threading
from utils.pool import PoolBlockGet, PoolBlockPut, PoolNoBlock

raw_input_pool = PoolBlockGet()
processed_input_pool = PoolBlockGet()
last_input_pool = PoolNoBlock()
noise_pool = PoolBlockPut()
keyword_pool = PoolNoBlock()

run_time = 0  # 运行时间

is_jamming = True  #KWS检测结果决定是否开启干扰