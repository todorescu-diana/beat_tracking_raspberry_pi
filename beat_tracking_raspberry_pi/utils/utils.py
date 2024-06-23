import numpy as np
import librosa
import sounddevice as sd
import threading
import time
import RPi.GPIO as GPIO
import subprocess
import constants.pins as pins
from constants.constants import FRAME_DURATION, FPS
from utils.gpio_setup import init_gpio, cleanup_gpio
from utils.lcd_utils import get_lcd, display_lcd_content, clear_lcd_content
import madmom

# Define a global flag to signal the thread to stop
stop_event = threading.Event()
stop_script = False

def set_stop_script(val):
    global stop_script
    stop_script = val

# Function to clean up the script
def do_script_cleanup():
    display_lcd_content("Unmounting USB memory device ...")
    time.sleep(2)
    subprocess.run(['sudo', 'umount', '/mnt/usb'])
    display_lcd_content("Unmounted USB memory device.")
    time.sleep(2)
    GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
    display_lcd_content("Cleaning up ...")
    time.sleep(2)
    clear_lcd_content()
    cleanup_gpio()

# Function to handle exceptions
def handle_exception_catch(e):
    display_lcd_content("Handling EXCEPTION: " + str(e))
    time.sleep(4)
    display_lcd_content("Unmounting USB memory device ...")
    time.sleep(2)
    subprocess.run(['sudo', 'umount', '/mnt/usb'])
    display_lcd_content("Unmounted USB memory device.")
    time.sleep(2)
    display_lcd_content("Cleaning up ...")
    time.sleep(2)
    GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
    clear_lcd_content()
    cleanup_gpio()

# convert beat times to frame indices
def beats_to_frame_indices(beat_positions_seconds, frame_rate=FPS):
    return np.round(beat_positions_seconds * frame_rate).astype(int)

# one-hot encode beats in the frames
def one_hot_encode_beats(beat_positions_frames, total_frames):
    one_hot_vector = np.zeros(total_frames, dtype=float)
    for frame_index in beat_positions_frames:
        if frame_index < total_frames:  # ensure frame index is within range
            one_hot_vector[int(frame_index)] = 1.  # convert frame_index to integer scalar
    return one_hot_vector

# play audio with click track
def play_audio_with_clicktrack(track, detected_beats):
    y, sr = librosa.load(track.audio_path, sr=None)
    click_track = librosa.clicks(frames=librosa.time_to_frames(detected_beats, sr=sr), sr=sr,
                                 length=len(y), click_freq=1000)

    min_len = min(len(y), len(click_track))
    y = y[:min_len]

    # combine the audio tracks
    combined_audio = np.vstack((y, click_track))

    # play the combined audio tracks
    sd.play(combined_audio.T, samplerate=sr)
    sd.wait()

# function to play rhythm using GPIO
def play_rhythm(beat_times):
    global stop_event
    while not stop_event.is_set():
        start_time = time.time()
        for beat in beat_times:
            if stop_event.is_set():
                break
            wait_time = beat - (time.time() - start_time)
            if wait_time > 0:
                time.sleep(wait_time)
            GPIO.output(pins.SOLENOID_CONTROL, GPIO.HIGH)
            time.sleep(0.03)
            GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
            time.sleep(0.03)
    return

class StoppableThread(threading.Thread):
    def __init__(self, task, *args, **kwargs):
        global stop_event
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._terminate_flag = stop_event
        self.task = task

    def terminate(self):
        self._terminate_flag.set()
        print("Thread terminating...")

# handle button press to stop audio
def handle_button_press(channel):
    global stop_event
    display_lcd_content("Stopping audio and rhythm ...")
    time.sleep(2)
    stop_event.set()
    sd.stop()  # Stop the audio playback
    time.sleep(0.01)
    GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)

# play audio with GPIO control
def play_audio_with_gpio(track, detected_beats):
    global stop_event
    stop_event.clear()
    
    GPIO.add_event_detect(pins.BUTTON_STOP_AUDIO, GPIO.FALLING, callback=handle_button_press, bouncetime=300)
    
    y, sr = librosa.load(track.audio_path, sr=None)
    click_track = librosa.clicks(frames=librosa.time_to_frames(detected_beats, sr=sr), sr=sr,
                                 length=len(y), click_freq=1000)

    min_len = min(len(y), len(click_track))
    y = y[:min_len]

#     combined_audio = np.vstack((y, click_track))
    combined_audio = y
    sd.play(combined_audio.T, samplerate=sr)


    rhythm_thread = StoppableThread(task=play_rhythm(detected_beats))
    rhythm_thread.start()

    try:
#         sd.play(combined_audio.T, samplerate=sr)
        while not stop_event.is_set():
            time.sleep(0.1)
        rhythm_thread.terminate()
        rhythm_thread.join()
        # rhythm thread terminated
        sd.stop()  # stop the audio playback if the event is set
        if stop_script == True:
            while True:
                time.sleep(0.1)
    except KeyboardInterrupt:
        rhythm_thread.terminate()
        rhythm_thread.join()
        handle_exception_catch("")
    except Exception as e:
        rhythm_thread.terminate()
        rhythm_thread.join()
        handle_exception_catch(e)
    finally:
        if stop_script == False:
            GPIO.remove_event_detect(pins.BUTTON_STOP_AUDIO)
            return
    
# get detected beats using DBN
def get_detected_beats_dbn(beat_activations):
    beat_tracker = madmom.features.beats.DBNBeatTrackingProcessor(
        correct=True, min_bpm=55.0, max_bpm=215.0, fps=FPS, transition_lambda=100, threshold=0.05
    )
    detected_beats = beat_tracker(beat_activations)
    return detected_beats