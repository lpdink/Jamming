import threading, logging, os
import numpy as np
from pocketsphinx import DefaultConfig, Decoder, get_model_path, get_data_path
from scipy import signal

import global_var


class KeywordSpotting(threading.Thread):
    def __init__(self, in_fs, out_fs, mute_period_length, kws_frame_length):
        threading.Thread.__init__(self)
        self.daemon = True
        self.in_fs = in_fs
        self.out_fs = out_fs
        self.mute_period_frames_count = int(in_fs * mute_period_length)
        self.kws_frames_count = int(in_fs * kws_frame_length)
        self.exit_flag = False
        # 初始化配置
        model_path = get_model_path()
        config = Decoder.default_config()
        config.set_string('-hmm', os.path.join(model_path, 'en-us'))  # 声学模型路径
        # config.set_string('-lm',"./tests/7567.lm")
        config.set_string('-dict',
                          os.path.join(model_path,
                                       'cmudict-en-us.dict'))  # 字典路径
        config.set_string('-keyphrase', 'alexa')
        config.set_float('-kws_threshold', 1e-20)
        config.set_string('-logfn', './logs/tmp')  # INFO输出到其他位置
        self.decoder = Decoder(config)
        self.decoder.start_utt()

        self.start()

    def run(self):
        while not self.exit_flag:
            # 1.从input池中读取一定长度的数据。该过程可能被阻塞，直到池中存在足够多数据。
            processed_input_frames = global_var.processed_input_pool.get(
                self.kws_frames_count)

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
        buf = frames.tobytes()
        if buf:
            self.decoder.process_raw(buf, False, False)
            if self.decoder.hyp() != None:
                print([(seg.word, seg.prob, seg.start_frame, seg.end_frame)
                       for seg in self.decoder.seg()])
                print("Detected keyphrase, restarting search")
                self.decoder.end_utt()
                self.decoder.start_utt()
                return True
        return False

    def resampling(self, frames, current_fs, target_fs):
        return signal.resample(frames, target_fs)
        #return np.array([])

    def padding(self, frames, padding_value, padding_num):
        res = np.pad(frames, (0, padding_num),
                     'constant',
                     constant_values=(padding_value, padding_value))
        return res