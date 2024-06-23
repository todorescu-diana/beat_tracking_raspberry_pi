import numpy as np

FPS = 100

F_MIN = 30
F_MAX = 10000
F_MAX_2 = 15360

FIXED_SAMPLE_RATE = 44100
HOP_LENGTH = int((1 / FPS) * FIXED_SAMPLE_RATE)
N_FFT = 2048
WINDOW = 'hann'
N_MELS = 81

LOG_BASE = 2

N_BANDS_PER_OCTAVE = 12

FRAME_DURATION = 1 / FPS

PAD_FRAMES = 2

NUM_FRAMES = 5

INPUT_SHAPE = (1, None, None, 1)

BINS_PER_OCTAVE = 12
NUM_BINS = 81

# conv layers
ACTIVATION = 'elu'
DROPOUT_RATE = 0.15
# CONV_NUM_FILTERS = 16
CONV_NUM_FILTERS = 20
DROPOUT_RATE = 0.1

# tcn
TCN_KERNEL_SIZE = 5
# TCN_NUM_FILTERS = 16
TCN_NUM_FILTERS = 20
TCN_DILATIONS = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
TCN_NUM_DILATIONS = 11

# k-fold-cross-validation
NUM_FOLDS = 8

# train
NUM_EPOCHS = 100

VALID_DATASET_NAMES = ['ballroom', 'smc', 'dagstuhl_choir', 'beatboxset', 'guitarset_mic', 'guitarset_pickup', 'tiny_aam', 'harmonix_set', 'gtzan_rhythm', 'aam']

DATASET_PATHS = {
    VALID_DATASET_NAMES[0]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[1]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[2]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[3]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[4]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[5]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[6]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[7]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[8]: {
        "audio_dir": '',
        "annot_dir": ''
    },
    VALID_DATASET_NAMES[9]: {
        "audio_dir": '',
        "annot_dir": ''
    }
}

SUMMARY_SAVE_PATH = ''
MODEL_SAVE_PATH = ''
PLOT_SAVE_PATH = ''
RESULTS_DIR_PATH = ''
CSV_LOSSES_PATH = ''

plot_colors = {
    'train': 'darkslategray',
    'val': 'firebrick'
}