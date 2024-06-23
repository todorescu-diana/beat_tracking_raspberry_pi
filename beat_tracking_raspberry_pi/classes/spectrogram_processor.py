import numpy as np
import librosa
import matplotlib.pyplot as plt
import librosa.feature
from constants.constants import FPS, NUM_BINS, FIXED_SAMPLE_RATE, N_FFT, F_MIN, F_MAX


class SpectrogramProcessor:
    def __init__(self, fps=FPS, num_bins=NUM_BINS, target_sample_rate=FIXED_SAMPLE_RATE, n_fft=N_FFT):
        self.fps = fps
        self.num_bins = num_bins
        self.sample_rate = target_sample_rate
        self.n_fft = n_fft
        self.hop_length = int(self.sample_rate / self.fps)
        self.filter_bank = librosa.filters.mel(sr=self.sample_rate, n_fft=self.n_fft, n_mels=self.num_bins,
                                                fmin=F_MIN, fmax=F_MAX)
        
    @staticmethod
    def spectrogram_type():
        return 'mel'

    def process(self, audio_path):
      try:

        # load audio file using librosa
        y, original_sr = librosa.load(audio_path)

        # resample to the target sample rate
        y_resampled = librosa.resample(y, orig_sr=original_sr, target_sr=self.sample_rate)

        # calculate power spectrogram
        stft = librosa.stft(y_resampled, n_fft=self.n_fft, win_length=2048, window='hann', hop_length=self.hop_length)
        magnitude_spectrogram = np.abs(stft) ** 2

        # apply mel filter bank
        mel_spectrogram = np.dot(self.filter_bank, magnitude_spectrogram)

        # convert to decibels
        spectrogram_db = librosa.power_to_db(mel_spectrogram, ref=np.max)

        spectrogram_transposed = spectrogram_db.T

        return spectrogram_transposed
      
      except Exception as e:
        print("Exception occurred: ", e)
        return []
      

    def plot_spectrogram(self, spectrogram, duration_s=None, cmap='gist_heat'):
        # calculate number of frames to display based on duration
        if duration_s is not None:
            num_frames_to_display = int(duration_s * self.sample_rate / self.hop_length)
            spectrogram = spectrogram[:num_frames_to_display, :]

        # determine the number of bins from the shape of the spectrogram
        num_bins = spectrogram.shape[1]

        # determine y-axis tick positions
        y_tick_positions = np.arange(0, num_bins, int(num_bins / 5))

        # plot spectrogram
        plt.figure(figsize=(10, 4))
        librosa.display.specshow(spectrogram.T, sr=self.sample_rate, hop_length=self.hop_length, x_axis='time',
                                 fmin=F_MIN, fmax=F_MAX)

        plt.yticks(y_tick_positions)
        plt.ylabel('mel bins')
        plt.xlabel('time [s]')
        plt.colorbar(format='%+2.0f dB')
        plt.title("mel spectrogram")
        plt.set_cmap(cmap)
        plt.tight_layout()
        plt.show()