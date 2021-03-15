import logging, sys, time, os, datetime, math
import pyaudio
import matplotlib.pyplot as plt
import numpy as np

import global_var
import settings

from threads.anc import ActiveNoiseControl
from threads.io import InputOutPut
from threads.kws import KeywordSpotting
from threads.nl import NoiseLib


def run():
    # 启动程序
    config_logging()
    logging.info("Start jamming programmer")
    nl_thread = NoiseLib(settings.OUT_FS, settings.NOISE_LENGTH,
                         settings.CHIRP_LENGTH)
    io_thread = InputOutPut(settings.INPUT_BIT_DEPTH, settings.INPUT_CHANNEL,
                            settings.IN_FS, settings.OUTPUT_BIT_DEPTH,
                            settings.OUTPUT_CHANNEL, settings.OUT_FS,
                            settings.FRAMES_PER_BUFFER)
    anc_thread = ActiveNoiseControl(
        settings.OUT_FS, settings.IN_FS,
        settings.CHIRP_LENGTH + settings.NOISE_LENGTH,
        settings.SIMULATION_LENGTH)
    kws_thread = KeywordSpotting(
        settings.IN_FS, settings.OUT_FS,
        np.floor(settings.OUT_FS * settings.MUTE_PERIOD_LENGTH))
    input("")
    logging.info("Stop jamming programmer")
    nl_thread.stop()
    io_thread.stop()
    anc_thread.stop()
    kws_thread.stop()


def config_logging():
    if not os.path.exists("logs"):
        os.mkdir("logs")

    log_filename = datetime.datetime.now().strftime("%Y-%m-%d-%H%M") + ".log"
    log_filepath = os.path.join(os.path.join(os.getcwd(), "logs"),
                                log_filename)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(stream=sys.stdout)
    fh = logging.FileHandler(filename=log_filepath, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s: %(message)s")
    ch.setFormatter(formatter)
    fh.setFormatter(formatter)
    logger.addHandler(ch)  # 日志输出到终端
    logger.addHandler(fh)  # 日志输出到文件
    logging.getLogger('matplotlib.font_manager').disabled = True  # 禁用字体管理记录器

    logging.info("Current log file {}".format(log_filepath))


def show_data():
    plt.xlim((global_var.run_time - 4, global_var.run_time + 4))

    while not global_var.raw_input_pool.is_empty():
        start_time = global_var.run_time
        end_time = global_var.run_time + settings.FRAMES_PER_BUFFER / settings.IN_FS
        global_var.run_time = end_time
        t = np.linspace(start_time, end_time, settings.FRAMES_PER_BUFFER)
        y = global_var.raw_input_pool.get(settings.FRAMES_PER_BUFFER)

        plt.plot(t, y, "r")
    plt.pause(0.1)


if __name__ == "__main__":
    run()