"""
fingerprint.py
Ye script Shazam jaisa "fingerprint" banati hai kisi bhi audio file ka.

BASIC IDEA (simple lafzon mein):
1. Audio file ko numbers mein convert karte hain (waveform)
2. Us waveform ka "spectrogram" banate hain (yani: kis waqt pe kaunsi
   frequency kitni loud thi — ek tasveer jaisa data)
3. Spectrogram mein sabse "loud/tez" points (peaks) dhoondte hain
4. In peaks ko jodkar (pairs banakar) ek unique number (hash) banate hain
5. Ye hash hi song ki "pehchan" (fingerprint) hai — thora sa hilne/shor
   ke bawajood wahi rehta hai

Isi wajah se Shazam shor-sharabe wali jagah pe bhi gaana pehchan leta hai.
"""

import numpy as np
import librosa
from scipy.ndimage import maximum_filter


def generate_fingerprint(audio_path):
    """
    Ek audio file ka path lekar, uske fingerprints (hashes) return karta hai.

    Return: list of (hash, time_offset) tuples
    """

    # Step 1: Audio file load karein
    # sr=22050 -> standard sample rate, mono=True -> ek hi channel (stereo nahi)
    y, sr = librosa.load(audio_path, sr=22050, mono=True)

    # Step 2: Spectrogram banayein (STFT = Short-Time Fourier Transform)
    # Ye batata hai: har chhote se time-window mein kaunsi frequencies maujood thin
    stft = librosa.stft(y, n_fft=2048, hop_length=512)
    spectrogram = np.abs(stft)  # sirf magnitude (loudness) chahiye, phase nahi

    # Step 3: Peaks dhoondein (jo points apne aas-paas ke mukable sabse loud hain)
    # maximum_filter har point ko uske neighbourhood ke max se compare karta hai
    local_max = maximum_filter(spectrogram, size=(20, 20)) == spectrogram

    # Bohot halke (quiet) peaks ko ignore karein — sirf meaningful peaks chahiye
    threshold = np.mean(spectrogram) * 2
    peaks = np.argwhere(local_max & (spectrogram > threshold))

    # peaks[i] = [frequency_bin, time_bin]
    # Time actual seconds mein convert karne ke liye:
    times = librosa.frames_to_time(peaks[:, 1], sr=sr, hop_length=512)
    freqs = peaks[:, 0]

    # Step 4: Peaks ko time ke hisaab se sort karein (zaroori hai pairing ke liye)
    order = np.argsort(times)
    freqs = freqs[order]
    times = times[order]

    # Step 5: Peaks ko pairs mein jodkar hash banayein
    # Har peak ko apne se aage wale 5 peaks ke saath jodte hain (Shazam ka tareeqa)
    fingerprints = []
    fan_out = 5  # har peak ko kitne aane wale peaks ke saath jodna hai

    for i in range(len(freqs)):
        for j in range(1, fan_out):
            if i + j < len(freqs):
                freq1 = freqs[i]
                freq2 = freqs[i + j]
                t1 = times[i]
                t2 = times[i + j]
                time_delta = t2 - t1

                # Sirf reasonable time-gap wale pairs rakhein (0 se 10 sec ke beech)
                if 0 < time_delta <= 10:
                    # Ek unique hash banayein in teeno cheezon se:
                    # freq1, freq2, aur unke darmiyan time ka farq
                    hash_val = hash((int(freq1), int(freq2), round(time_delta, 2)))
                    # Python ka hash() bohot bada/negative ho sakta hai,
                    # isay Postgres BIGINT range mein fit karte hain:
                    hash_val = hash_val % (2**63 - 1)

                    fingerprints.append((hash_val, float(t1)))

    return fingerprints


# ==============================
# Test: is file ko seedha run karke check karein
# ==============================
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Use: python fingerprint.py path/to/song.mp3")
        sys.exit(1)

    audio_file = sys.argv[1]
    print(f"🎵 Fingerprint bana rahe hain: {audio_file}")

    fps = generate_fingerprint(audio_file)
    print(f"✅ Total {len(fps)} fingerprints bane.")
    print("Pehle 5 samples:", fps[:5])