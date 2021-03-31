import logging, sys, os
import numpy as np

import settings
from threads.io import PyaudioInput, PyaudioOutput
# from threads.io2 import SoundDeviceInput, SoundDeviceOutput
from threads.kws import KeywordSpotting
from threads.nl import NoiseLib


def run():
    # 启动程序
    # os.close(sys.stderr.fileno())
    _config_logging()
    logging.info("Start jamming programmer")
    nl_thread = NoiseLib(settings.OUT_FS, settings.NOISE_LENGTH,
                         settings.CHIRP_LENGTH)
    input_thread = PyaudioInput(
        nl_thread, settings.IN_FS, settings.IN_CHANNEL, settings.IN_BIT_DEPTH,
        settings.CHIRP_LENGTH + settings.NOISE_LENGTH,
        settings.SIMULATION_LENGTH,settings.IN_DEVICE_KEYWORD)
    # output_thread = PyaudioOutput(settings.OUT_FS, settings.OUT_CHANNEL,
    #                                   settings.OUT_BIT_DEPTH,
    #                                   settings.FRAMES_PER_BUFFER,
    #                                   settings.OUT_DEVICE_KEYWORD)
    # kws_thread = KeywordSpotting(
    #     settings.IN_FS, settings.OUT_FS,
    #     np.floor(settings.OUT_FS * settings.MUTE_PERIOD_LENGTH),
    #     settings.KWS_FRAME_LENGTH)
    input("")
    logging.info("Stop jamming programmer")
    # kws_thread.stop()
    # output_thread.stop()
    input_thread.stop()
    nl_thread.stop()


def _config_logging():
    if not os.path.exists("logs"):
        os.mkdir("logs")

    # log_filename = datetime.datetime.now().strftime("%Y-%m-%d-%H%M") + ".log"
    log_filename = "test.log"
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


if __name__ == "__main__":
    run()