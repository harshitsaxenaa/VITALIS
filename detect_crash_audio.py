import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import librosa

CRASH_LABELS = ["Car crash", "Tire squeal", "Skidding", "Siren", "Glass"]



yamnet_model = hub.load('https://tfhub.dev/google/yamnet/1')
def load_class_names():
    path = tf.keras.utils.get_file(
        'yamnet_class_map.csv',
        'https://raw.githubusercontent.com/tensorflow/models/master/research/audioset/yamnet/yamnet_class_map.csv'
    )
    with open(path, 'r') as f:
        lines = f.readlines()[1:]  # skip header
        class_names = [line.strip().split(',')[2] for line in lines]
    return class_names

def load_audio(file_path):
    waveform, sr = librosa.load(file_path, sr=16000)
    return waveform

def detect_crash(file_path, threshold=0.1):
    class_names = load_class_names()
    waveform = load_audio(file_path)
    
    scores, _, _ = yamnet_model(waveform)
    mean_scores = tf.reduce_mean(scores, axis=0).numpy()

    detected = False
    print("\n🎧 Top Predictions:")
    for i in np.argsort(mean_scores)[::-1][:10]:  # Top 10
        label = class_names[i]
        score = mean_scores[i]
        print(f" - {label}: {score:.3f}")
        if label in CRASH_LABELS and score > threshold:
            print(f"\n Crash-related sound detected: {label} ({score:.2f})")
            detected = True

    return detected

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python detect_crash_audio.py <audio_file>")
    else:
        audio_file = sys.argv[1]
        result = detect_crash(audio_file)
        if result:
            print("\n✅ Crash Detected!")
        else:
            print("\n❌ No Crash Sound Detected.")
