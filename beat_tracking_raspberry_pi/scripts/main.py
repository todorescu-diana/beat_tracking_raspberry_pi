import sys
sys.path.append('/home/raspberrypi5/Desktop/beat_tracking_v2')
import time
from utils.file_utils import access_usb_storage
from classes.spectrogram_processor import SpectrogramProcessor
from classes.spectrogram_sequence import SpectrogramSequence
from utils.utils import get_detected_beats_dbn, play_audio_with_clicktrack, play_audio_with_gpio, play_rhythm, handle_button_press, set_stop_script
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
    last_slash_index = audio_path.rfind('/')
    last_dot_index = audio_path.rfind('.')
    
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
    return
        
def signal_handler(signum, frame):
    display_lcd_content("Exiting ...")
    clear_lcd_content()
    time.sleep(1)
    sys.exit(0)
    
# Function to stop all threads except the main one
def print_other_threads():
    main_thread = threading.current_thread()
    print(threading.enumerate())
    for t in threading.enumerate():
        if t is main_thread:
            continue
        if hasattr(t, "terminate"):
            print("!!!!!!!!!!!!!!!!!!!!")
            t.terminate()  # Example if you have a custom terminate method

def button_callback(channel):
    lcd = get_lcd()
    display_lcd_content("Stopping the script ...")
#     print_other_threads()
    time.sleep(0.5)
    set_stop_script(True)
    time.sleep(0.5)
    handle_button_press(channel)
    do_script_cleanup()
    os.kill(os.getpid(), signal.SIGINT)
        
def main():
    try:
        init_gpio()
        init_lcd()
        lcd = get_lcd()
        display_lcd_content("Initializing ...")
        
        # register the signal handler
        signal.signal(signal.SIGINT, signal_handler)

        # add event detection on the button pin
        GPIO.add_event_detect(pins.BUTTON_STOP_SCRIPT, GPIO.FALLING, callback=button_callback, bouncetime=300)
    
        access_usb_storage(audio_callback)
    except KeyboardInterrupt:
        handle_exception_catch("")
    except Exception as e:
        handle_exception_catch(e)
    else:
        do_script_cleanup()

if __name__ == "__main__":
    main()
