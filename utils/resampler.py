from scipy import signal


class Resampler():
    @classmethod
    def resample(cls, frames, org_fs, dst_fs):
        return signal.resample(frames, int((frames.size * dst_fs) / org_fs))
