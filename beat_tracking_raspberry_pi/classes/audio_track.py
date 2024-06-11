from classes.beat import Beat


class AudioTrack:
    def __init__(self, audio_path, beat_times=None):
        self.audio_path = audio_path
        self.beats = Beat(beat_times)
