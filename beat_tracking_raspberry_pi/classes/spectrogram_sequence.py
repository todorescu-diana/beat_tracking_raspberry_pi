import tensorflow as tf
import sys
import numpy as np
from keras.utils import Sequence
from utils.model_utils import cnn_pad


class SpectrogramSequence(Sequence):
    def __init__(self, tracks, pre_processor, pad_frames=None):
        self.ids = []
        self.spectrograms = {}
        self.pad_frames = pad_frames

        for i, key in enumerate(tracks):
            sys.stderr.write(f'\rProcessing track {i + 1}/{len(tracks)}: {key + " " * 20}')
            sys.stderr.flush()

            track = tracks[key]
            spectrogram = pre_processor.process(track.audio_path)
            
            if len(spectrogram):
                self.spectrograms[key] = spectrogram
                self.ids.append(key)
            else:
                continue

        assert len(self.spectrograms) == len(self.ids)

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, idx):
        if isinstance(idx, int):
            idx = self.ids[idx]

        data_sequence_spectrogram = self.spectrograms[idx]
        if self.pad_frames:
            data_sequence_spectrogram = cnn_pad(data_sequence_spectrogram, self.pad_frames)

        return tf.convert_to_tensor(data_sequence_spectrogram[np.newaxis, ..., np.newaxis])
    
    def append(self, other):
        assert not any(key in self.ids for key in other.ids), 'IDs must be unique'
        self.spectrograms.update(other.spectrograms)
        self.ids.extend(other.ids)
