import librosa
import pydub
import numpy as np
import soundfile as sf

def load_audio(filename):
    y, sr = librosa.load(filename)

    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    tempo = tempo.item() if isinstance(tempo, np.ndarray) else tempo
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

    chromagram = librosa.feature.chroma_stft(y=y, sr=sr)
    mean_chroma = np.mean(chromagram, axis=1)
    chroma_to_key = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    estimated_key_index = np.argmax(mean_chroma)
    estimated_key = chroma_to_key[estimated_key_index]

    return y, sr, tempo, beat_times, estimated_key

y_first, sr_first, tempo_first, bt_first, key_first = load_audio('two-worlds.mp3')
y_second, sr_second, tempo_second, bt_second, key_second = load_audio('scientist.mp3')
y_fast, sr_fast, tempo_fast, bt_fast, key_fast = load_audio('two-worlds-fast.wav')

print("First tempo:", tempo_first)
print("First key:", key_first)
print("First SR:", sr_first)
print()
print("Second tempo:", tempo_second)
print("Second key:", key_second)
print("Second SR:", sr_second)
print()
print("Adjusted tempo:", tempo_fast)
print("Adjusted key:", key_fast)
print("Adjusted SR", sr_fast)

adjust_factor = tempo_first / tempo_second

y_second = librosa.effects.time_stretch(y_second, rate=adjust_factor)

offset = bt_first[0] - bt_second[0]

if offset > 0:
    y2_aligned = np.pad(y_second, (int(offset * sr_second), 0), mode='constant')
    y1_aligned = y_first
else:
    # Pad the start of y1 with silence
    y1_aligned = np.pad(y_first, (int(-offset * sr_first), 0), mode='constant')
    y2_aligned = y_second

# Pad the shorter track with silence
len_diff = len(y_first) - len(y2_aligned)
if len_diff > 0:
    y2_aligned = np.pad(y2_aligned, (0, len_diff), mode='constant')
else:
    y1_aligned = np.pad(y_first, (0, -len_diff), mode='constant')

# Overlay the two tracks
combined = y1_aligned + y2_aligned

# Normalize the output to prevent clipping
combined = combined / np.max(np.abs(combined))

sf.write('combined_track.wav', combined, sr_first)

# sf.write("two-worlds-fast.wav", y2_fast, sr_second)
