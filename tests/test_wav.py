import wave

def run():
    wf = wave.open("../waves/raw/no_yes.wav", "rb")
    print(wf.getparams())
    # nchannels = wf.getparams().nchannels
    # sampwidth = wf.getparams().sampwidth
    # framerate = wf.getparams().framerate
    # nframes = wf.getparams().nframes
    # bytes_buffer = wf.readframes(nframes)  # 一次性读取所有frame