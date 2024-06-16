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

# Function to clean up the script
def do_script_cleanup():
    print("NOW UNMOUNT ...")
    subprocess.run(['sudo', 'umount', '/mnt/usb'])
    print("UNMOUNTED!")
    GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
    print("FINALLY")
    clear_lcd_content()
    cleanup_gpio()

# Function to handle exceptions
def handle_exception_catch(e):
    display_lcd_content("EXCEPTION HANDLE!!!!")
    lcd = get_lcd()
    display_lcd_content(str(e))
    time.sleep(5)
    print("NOW UNMOUNT ...")
    subprocess.run(['sudo', 'umount', '/mnt/usb'])
    print("UNMOUNTED!")
    GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
    print("FINALLY")
    clear_lcd_content()
    cleanup_gpio()

# Convert beat times to frame indices
def beats_to_frame_indices(beat_positions_seconds, frame_rate=FPS):
    return np.round(beat_positions_seconds * frame_rate).astype(int)

# One-hot encode beats in the frames
def one_hot_encode_beats(beat_positions_frames, total_frames):
    one_hot_vector = np.zeros(total_frames, dtype=float)
    for frame_index in beat_positions_frames:
        if frame_index < total_frames:  # ensure frame index is within range
            one_hot_vector[int(frame_index)] = 1.  # convert frame_index to integer scalar
    return one_hot_vector

# Play audio with click track
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

# Function to play rhythm using GPIO
def play_rhythm(beat_times):
    global stop_event
    while not stop_event.is_set():
        start_time = time.time()
        for beat in beat_times:
            if stop_event.is_set():
                break
            wait_time = beat - (time.time() - start_time) - 0.08
            if wait_time > 0:
                time.sleep(wait_time)
            GPIO.output(pins.SOLENOID_CONTROL, GPIO.HIGH)
            time.sleep(0.045)  # The duration the solenoid stays active (adjust as needed)
            GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
            time.sleep(0.045)
    return

class StoppableThread(threading.Thread):
    def __init__(self, task, *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._terminate_flag = threading.Event()
        self.task = task

    def run(self):
        while not self._terminate_flag.is_set():
            self.perform_task()

    def perform_task(self):
        print("Thread working...")
        time.sleep(1)

    def terminate(self):
        self._terminate_flag.set()
        print("Thread terminating...")

# Handle button press to stop audio
def handle_button_press(channel):
    global stop_event
    stop_event.set()
    sd.stop()  # Stop the audio playback

# Play audio with GPIO control
def play_audio_with_gpio(track, detected_beats):
    global stop_event
    stop_event.clear()
    
    GPIO.add_event_detect(pins.BUTTON_STOP_AUDIO, GPIO.FALLING, callback=handle_button_press, bouncetime=300)
    
    y, sr = librosa.load(track.audio_path, sr=None)
    click_track = librosa.clicks(frames=librosa.time_to_frames(detected_beats, sr=sr), sr=sr,
                                 length=len(y), click_freq=1000)

    min_len = min(len(y), len(click_track))
    y = y[:min_len]

    combined_audio = np.vstack((y, click_track))
    sd.play(combined_audio.T, samplerate=sr)


    rhythm_thread = StoppableThread(task=play_rhythm(detected_beats))
    rhythm_thread.start()

    try:
#         sd.play(combined_audio.T, samplerate=sr)
        while not stop_event.is_set():
            time.sleep(0.1)
        rhythm_thread.terminate()
        rhythm_thread.join()
        print("rhythm thread terminated")
        sd.stop()  # Stop the audio playback if the event is set
    except Exception as e:
        rhythm_thread.terminate()
        rhythm_thread.join()
        handle_exception_catch(e)
    finally:
        return
#     else:
#         stop_event.set()
#         rhythm_thread.terminate()
#         rhythm_thread.join()

# Get detected beats using DBN
def get_detected_beats_dbn(beat_activations):
    beat_tracker = madmom.features.beats.DBNBeatTrackingProcessor(
        correct=True, min_bpm=55.0, max_bpm=215.0, fps=FPS, transition_lambda=100, threshold=0.05
    )
    detected_beats = beat_tracker(beat_activations)
    return detected_beats
