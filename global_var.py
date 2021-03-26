import threading, settings
from utils.pool import PoolBlockGet, PoolBlockPut, PoolNoBlock
from utils.data_queue import DataQueue

raw_input_pool = PoolBlockGet(settings.IN_FS *
                              (settings.CHIRP_LENGTH + settings.NOISE_LENGTH))
processed_input_pool = PoolBlockGet(settings.IN_FS *
                                    (settings.KWS_FRAME_LENGTH))
last_input_pool = PoolNoBlock()
noise_pool = PoolBlockPut(settings.FRAMES_PER_BUFFER)
keyword_pool = PoolNoBlock()

run_time = 0  # 运行时间