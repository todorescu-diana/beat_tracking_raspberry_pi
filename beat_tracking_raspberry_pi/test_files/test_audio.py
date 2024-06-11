import tensorflow as tf
from MelSpectrogramProcessor import MelSpectrogramProcessor
from Utils import get_detected_beats_DBN, play_audio_with_clicktrack
from AudioTrack import AudioTrack
from SpectrogramSequence import SpectrogramSequence

pre_processor = MelSpectrogramProcessor()

audio_path = './chericherilady.wav'

track = AudioTrack(audio_path)

tracks_new = {"ccl": track}

test_tracks = SpectrogramSequence(data_sequence_tracks=tracks_new, data_sequence_pre_processor=pre_processor, data_sequence_pad_frames=2)

input_test = test_tracks[0]

model = tf.keras.models.load_model('model_1_best.h5')

beats = model.predict(input_test)
beat_activations = beats.squeeze()
beat_detections = get_detected_beats_DBN(beat_activations)

play_audio_with_clicktrack(track, beat_detections)