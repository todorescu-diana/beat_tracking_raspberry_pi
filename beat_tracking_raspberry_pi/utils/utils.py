import numpy as np
import librosa
import matplotlib.pyplot as plt
import sounddevice as sd
import madmom
from constants.constants import FRAME_DURATION, FPS
from utils.gpio_setup import init_gpio, cleanup_gpio
import time
import threading
import RPi.GPIO as GPIO
import constants.pins as pins

def beats_to_frame_indices(beat_positions_seconds, frame_rate=FPS):
    return np.round(beat_positions_seconds * frame_rate).astype(int)


def one_hot_encode_beats(beat_positions_frames, total_frames):
    one_hot_vector = np.zeros(total_frames, dtype=float)
    for frame_index in beat_positions_frames:
        if frame_index < total_frames:  # ensure frame index is within range
            one_hot_vector[int(frame_index)] = 1.  # convert frame_index to integer scalar
    return one_hot_vector


def plot_activations(beat_activations):
    # calculate time in seconds for each time frame
    print(len(beat_activations))
    time_frames = range(len(beat_activations))  # example time frames
    time_seconds = np.array(time_frames) * FRAME_DURATION  # convert time frames to seconds as numpy array

    # plot both beat activations and spectrogram in separate subplots within the same window
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # plot beat activations against frames
    ax1.plot(beat_activations, label='Beat Activation', color='blue')
    ax1.set_title('Model Beat Activation Output (Frames)')
    ax1.set_xlabel('Frame Index')
    ax1.set_ylabel('Activation Probability')
    ax1.legend()
    ax1.grid(True)

    # plot beat activations against time in seconds
    ax2.plot(time_seconds, beat_activations, label='Beat Activation', color='blue')
    ax2.set_title('Model Beat Activation Output (Seconds)')
    ax2.set_xlabel('Time (seconds)')
    ax2.set_ylabel('Activation Probability')
    ax2.legend()
    ax2.grid(True)

    plt.tight_layout()  # adjust layout to prevent overlap
    plt.show()


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
    

def play_rhythm(beat_times):
    try:
        start_time = time.time()
        for beat in beat_times:
            # Calculate the time to wait until the next beat
            wait_time = beat - (time.time() - start_time) - 0.025
            if wait_time > 0:
                time.sleep(wait_time)
            # Activate the solenoid
            GPIO.output(pins.SOLENOID_CONTROL, GPIO.HIGH)
            time.sleep(0.05)  # The duration the solenoid stays active (adjust as needed)
            GPIO.output(pins.SOLENOID_CONTROL, GPIO.LOW)
            time.sleep(0.05)
    except Exception as e:
        print(f"Exception in play_rhythm thread: {e}")
    finally:
        GPIO.cleanup()


def play_audio_with_gpio(track, detected_beats):
    try:
        y, sr = librosa.load(track.audio_path, sr=None)
        click_track = librosa.clicks(frames=librosa.time_to_frames(detected_beats, sr=sr), sr=sr,
                                     length=len(y), click_freq=1000)

        min_len = min(len(y), len(click_track))
        y = y[:min_len]

        # combine the audio tracks
        combined_audio = np.vstack((y, click_track))
        
        # Event to signal thread stop
        stop_event = threading.Event()

        # Start the GPIO control thread
        rhythm_thread = threading.Thread(target=play_rhythm, args=(detected_beats,))
        rhythm_thread.start()

        # play the combined audio tracks
        sd.play(combined_audio.T, samplerate=sr)
    #     sd.play(click_track, samplerate=sr)
        sd.wait()

        # Wait for the rhythm thread to finish
        rhythm_thread.join()
    #     play_rhythm(detected_beats)
    except Exception as e:
        print(f"Exception in play_audio_with_gpio: {e}")
        stop_event.set()
        rhythm_thread.join()
    else:
        stop_event.set()
        rhythm_thread.join()


def get_detected_beats_dbn(beat_activations):
    # track beats with a DBN
    beat_tracker = madmom.features.beats.DBNBeatTrackingProcessor(
        correct=True, min_bpm=55.0, max_bpm=215.0, fps=FPS, transition_lambda=100, threshold=0.05
    )
    detected_beats = beat_tracker(beat_activations)

    return detected_beats


def get_longest_continuous_segment_length(bool_list):
    max_length = 0.
    current_length = 0.

    for value in bool_list:
        if value:
            current_length += 1.
        else:
            max_length = max(max_length, current_length)
            current_length = 0.

    # check if the last segment is the longest
    max_length = max(max_length, current_length)

    return max_length

def get_longest_continuous_segment_bounds(bool_list):
    max_length = 0
    current_length = 0
    lower_bound = 0
    upper_bound = 0
    max_lower_bound = 0
    max_upper_bound = 0

    for index, value in enumerate(bool_list):
        if value:
            current_length += 1
            if current_length == 1:
                lower_bound = index  # update lower bound
            upper_bound = index  # update upper bound
        else:
            if current_length > max_length:
                max_length = current_length
                max_lower_bound = lower_bound  # update max lower bound
                max_upper_bound = upper_bound  # update max upper bound
            current_length = 0

    # check if the last segment is the longest
    if current_length > max_length:
        max_length = current_length
        max_lower_bound = lower_bound
        max_upper_bound = upper_bound

    return max_lower_bound, max_upper_bound

def get_all_except_longest_continuous_segment_bounds(bool_list):
    max_length = 0
    current_length = 0
    lower_bound = 0
    upper_bound = 0
    max_lower_bound = 0
    max_upper_bound = 0

    all_bound_except_longest = []

    for index, value in enumerate(bool_list):
        if value:
            current_length += 1
            if current_length == 1:
                lower_bound = index  # update lower bound
            upper_bound = index  # update upper bound
        else:
            if current_length > max_length:
                max_length = current_length
                all_bound_except_longest.append((lower_bound, upper_bound))
                max_lower_bound = lower_bound  # update max lower bound
                max_upper_bound = upper_bound  # update max upper bound
            current_length = 0

    # check if the last segment is the longest
    if current_length > max_length:
        all_bound_except_longest.append((lower_bound, upper_bound))
        max_length = current_length
        max_lower_bound = lower_bound
        max_upper_bound = upper_bound

    filtered_all_bound_except_longest = [t for t in all_bound_except_longest if t != (max_lower_bound, max_upper_bound)]

    return filtered_all_bound_except_longest


def sum_continuous_true_segments(lst):
    continuous_sum = 0  # initialize the sum of continuous True segments
    current_segment_length = 0  # initialize the length of the current True segment

    for item in lst:
        if item:  # if the current item is True
            current_segment_length += 1  # Increment the length of the current segment
        else:  # if the current item is False
            if current_segment_length > 1:  # if the current segment length is greater than 1
                continuous_sum += current_segment_length  # add the current segment length to the continuous sum
            current_segment_length = 0  # reset the current segment length

    # check if there's an unprocessed segment at the end
    if current_segment_length > 1:
        continuous_sum += current_segment_length

    return continuous_sum
