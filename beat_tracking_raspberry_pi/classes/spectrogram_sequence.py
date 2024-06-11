from tensorflow import keras
import sys
import numpy as np
from utils.model_utils import cnn_pad


class SpectrogramSequence(keras.utils.Sequence):
    def __init__(self, data_sequence_tracks, data_sequence_pre_processor, data_sequence_pad_frames=None):
        self.spectrogram = {}
        self.ids = []
        self.pad_frames = data_sequence_pad_frames

        for i, key in enumerate(data_sequence_tracks):
            sys.stderr.write(f'\rProcessing track {i + 1}/{len(data_sequence_tracks)}: {key + " " * 20}')
            sys.stderr.flush()
            track = data_sequence_tracks[key]
            spectrogram = data_sequence_pre_processor.process(track.audio_path)
            self.spectrogram[key] = spectrogram
            self.ids.append(key)

        assert len(self.spectrogram) == len(self.ids)

    def __len__(self):
        return len(self.ids)

    def __getitem__(self, idx):
        # convert int idx to key
        if isinstance(idx, int):
            idx = self.ids[idx]

        # get the full spectrogram and beat information
        data_sequence_spectrogram = self.spectrogram[idx]
        if self.pad_frames:
            data_sequence_spectrogram = cnn_pad(data_sequence_spectrogram, self.pad_frames)

        return data_sequence_spectrogram[np.newaxis, ..., np.newaxis]
    
    def append(self, other):
        assert not any(key in self.ids for key in other.ids), 'IDs must be unique'
        self.spectrogram.update(other.spectrogram)
        self.ids.extend(other.ids)
