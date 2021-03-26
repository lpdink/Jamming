import pyaudio
import wave
import time
import sys
from utils.codec import Codec
from utils.modulate import Modulate


def run():
    filename = "./waves/raw/offer.wav"

    wf = wave.open(filename, 'rb')
    print(wf.getparams())

    # instantiate PyAudio (1)
    p = pyaudio.PyAudio()

    # define callback (2)
    def callback(in_data, frame_count, time_info, status):
        data = wf.readframes(frame_count)
        audio_clip = Codec.decode_bytes_to_audio(data, wf.getnchannels(),
                                                 wf.getsampwidth() * 8)
        audio_clip_md = Modulate.am_modulate(audio_clip, 2)
        data = Codec.encode_audio_to_bytes(audio_clip_md, 2, 16)
        return (data, pyaudio.paContinue)

    # open stream using callback (3)
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=2,
                    rate=wf.getframerate(),
                    output=True,
                    stream_callback=callback)

    # start the stream (4)
    stream.start_stream()

    # wait for stream to finish (5)
    while stream.is_active():
        time.sleep(0.1)

    # stop stream (6)
    stream.stop_stream()
    stream.close()
    wf.close()

    # close PyAudio (7)
    p.terminate()