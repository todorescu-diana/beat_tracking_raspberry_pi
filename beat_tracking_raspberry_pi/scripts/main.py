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
from utils.lcd_utils import init_lcd, get_lcd, clear_lcd_content, display_lcd_content
from utils.gpio_setup import cleanup_gpio, init_gpio
import RPi.GPIO as GPIO
import subprocess
import signal
import os
from utils.utils import handle_exception_catch, do_script_cleanup
import threading

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
        
def signal_handler(signum, frame):
    sys.exit(0)
    
# Function to stop all threads except the main one
def print_other_threads():
    main_thread = threading.current_thread()
    print(len(threading.enumerate()))
    for t in threading.enumerate():
        if t is main_thread:
            print("---------- main_thread")
            continue
        print(f"------- thread: {t.name}")
        if hasattr(t, "terminate"):
            t.terminate()  # Example if you have a custom terminate method

def button_callback(channel):
    lcd = get_lcd()
    display_lcd_content("button_callback")
    print_other_threads()
    time.sleep(0.5)
    handle_exception_catch('SCRIPT STOPPING ...')
    os.kill(os.getpid(), signal.SIGINT)
        
def main():
    init_gpio()
    init_lcd()
    lcd = get_lcd()
    
    # Register the signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Add event detection on the button pin
    GPIO.add_event_detect(pins.BUTTON_STOP_SCRIPT, GPIO.FALLING, callback=button_callback, bouncetime=200)

    try:
#         access_usb_storage(audio_callback)
        audio_callback(lcd, '/home/raspberrypi5/Desktop/beat_tracking_v2/audio_wav_files/chericherilady.wav')
        print("RETURNED!!!")
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        print("Script stopped by CTRL+C")
    except Exception as e:
        handle_exception_catch(e)
    else:
        do_script_cleanup()

if __name__ == "__main__":
    main()
