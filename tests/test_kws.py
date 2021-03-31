import os, time, wave
from pocketsphinx import *

# def run():
#     def A(a,b):
#         print(a,b)

#     p = {"a":1,"b":2}
#     A(**p)
# def run():
#     model_path = get_model_path()
#     data_path = get_data_path()

#     # Create a decoder with a certain model
#     config = DefaultConfig()
#     config.set_string('-hmm', os.path.join(model_path, 'en-us'))
#     config.set_string('-lm', os.path.join(model_path, 'en-us.lm.bin'))
#     config.set_string('-dict', os.path.join(model_path, 'cmudict-en-us.dict'))
#     config.set_string('-logfn', './logs/tmp')
#     decoder = Decoder(config)

#     # Decode streaming data
#     st = time.time()
#     buf = bytearray(1024)
#     with open(r'waves\raw\no_yes.wav', 'rb') as f:
#         decoder.start_utt()
#         while f.readinto(buf):
#             decoder.process_raw(buf, False, False)
#         decoder.end_utt()
#     print('Best hypothesis segments:', [seg.word for seg in decoder.seg()])
#     print("Cost:",time.time()-st)

# def run():
#     model_path = get_model_path()
#     data_path = get_data_path()

#     config = {
#         'hmm': os.path.join(model_path, 'en-us'),
#         'lm': os.path.join(model_path, 'en-us.lm.bin'),
#         'dict': os.path.join(model_path, 'cmudict-en-us.dict')
#     }

#     ps = Pocketsphinx(**config)
#     st = time.time()
#     ps.decode(audio_file=r'waves\raw\no_yes.wav',
#               buffer_size=2048,
#               no_search=False,
#               full_utt=False)

#     print(ps.segments()
#           )  # => ['<s>', '<sil>', 'go', 'forward', 'ten', 'meters', '</s>']
#     print('Detailed segments:', *ps.segments(detailed=True), sep='\n')
#     print("Cost:",time.time()-st)

# def run():
#     model_path = get_model_path()
#     config = {
#         'audio_file': r'waves\raw\no_yes.wav',
#         'lm': False,
#         'keyphrase': 'alexa',
#         'kws_threshold': 1e-20,
#         'buffer_size': 1024,
#     }

#     audio = AudioFile(**config)

#     st = time.time()
#     for phrase in audio:
#         print(phrase.segments(detailed=True))
#     print("Cost:", time.time() - st)


def run():
    # Create a decoder with certain model
    model_path = get_model_path()
    data_path = "./waves/raw"
    config = Decoder.default_config()
    config.set_string('-hmm', os.path.join(model_path, 'en-us'))
    config.set_string('-dict', os.path.join(model_path, 'cmudict-en-us.dict'))
    config.set_string('-logfn', './logs/tmp')
    config.set_string('-keyphrase', 'alexa')
    config.set_float('-kws_threshold', 1e-20)
    decoder = Decoder(config)
    # decoder.set_kws('keyword', 'keyword.list')
    # decoder.set_search('keyword')
    decoder.start_utt()

    st = time.time()
    with wave.open(os.path.join(data_path, "offer.wav"), "rb") as rf:
        print(rf.getparams())
        while True:
            buf = rf.readframes(1024)
            if buf:
                decoder.process_raw(buf, False, False)
            else:
                break
            if decoder.hyp() != None:
                print([(seg.word, seg.prob, seg.start_frame, seg.end_frame)
                       for seg in decoder.seg()])
                print("Detected keyphrase, restarting search")
                decoder.end_utt()
                decoder.start_utt()
    print("Cost:", time.time() - st)



# def run():
#     speech = LiveSpeech(lm=False, keyphrase='forward', kws_threshold=1e-20)
#     for phrase in speech:
#         print(phrase.segments(detailed=True))
