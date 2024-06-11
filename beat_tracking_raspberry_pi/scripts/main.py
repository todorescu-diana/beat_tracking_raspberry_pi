import sys
sys.path.append('/home/raspberrypi5/Desktop/beat_tracking_v2')
import time
from utils.file_utils import access_usb_storage
from classes.spectrogram_processor import SpectrogramProcessor
from classes.spectrogram_sequence import SpectrogramSequence
from utils.utils import get_detected_beats_dbn, play_audio_with_clicktrack, play_audio_with_gpio, play_rhythm
import constants.pins as pins
from classes.audio_track import AudioTrack
from keras.models import load_model
from utils.lcd_utils import init_lcd, get_lcd
from utils.gpio_setup import cleanup_gpio, init_gpio
import RPi.GPIO as GPIO
import subprocess

def get_track_title(audio_path):
    # find the position of the last '/'
    last_slash_index = audio_path.rfind('/')
    # find the position of the last '.'
    last_dot_index = audio_path.rfind('.')
    
    # extract the substring between the last '/' and the last '.'
    if last_slash_index != -1 and last_dot_index != -1 and last_dot_index > last_slash_index:
        return audio_path[last_slash_index + 1:last_dot_index]
    else:
        return None

def audio_callback(lcd, audio_path):
    track_title = get_track_title(audio_path)
    lcd.message("Processing track: " + track_title + '...')
    time.sleep(0.1)
    
    pre_processor = SpectrogramProcessor()
    
    track = AudioTrack(audio_path)
    track_dict = {track_title: track}
    
    tracks_sequence = SpectrogramSequence(data_sequence_tracks=track_dict, data_sequence_pre_processor=pre_processor, data_sequence_pad_frames=2)
    
    model = load_model('/home/raspberrypi5/Desktop/beat_tracking_v2/models/trained_gtzan_v2_best.h5')

    beats = model.predict(tracks_sequence[0])
    beat_activations = beats.squeeze()
    beat_detections = get_detected_beats_dbn(beat_activations)
    
    lcd.clear()
    lcd.message("Playing track: " + track_title + ' with beats')
    time.sleep(0.5)
    play_audio_with_gpio(track, beat_detections)
    
        
def main():
    init_gpio()
    init_lcd()
    try:
        access_usb_storage(audio_callback)
#         play_rhythm([])
    except Exception as e:
        print("exception: ", e)
        print("EXCEPT")
    finally:
        print("NOW UNMOUNT ...")
        subprocess.run(['sudo', 'umount', '/mnt/usb'])
        print("UNMOUNTED!")
        GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
        print("FINALLY")
        cleanup_gpio()

if __name__ == "__main__":
    main()
