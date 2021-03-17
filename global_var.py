import threading, settings
from utils.pool import PoolBlockGet, PoolBlockPut, PoolNoBlock

raw_input_pool = PoolBlockGet(settings.IN_FS *
                              (settings.CHIRP_LENGTH + settings.NOISE_LENGTH))
processed_input_pool = PoolBlockGet(settings.IN_FS *
                                    (settings.KWS_FRAME_LENGTH))
last_input_pool = PoolNoBlock()
noise_pool = PoolBlockPut(settings.FRAMES_PER_BUFFER)
keyword_pool = PoolNoBlock()

run_time = 0  # 运行时间

is_jamming = True  #KWS检测结果决定是否开启干扰