"""Audio analysis engine: BPM detection, energy tracking, spectral mood estimation.

Designed to work reliably with the Reachy Mini's built-in microphone
picking up ambient music. No user configuration needed.
"""

import collections
import math
import threading
import time
from typing import Optional

import numpy as np
import sounddevice as sd


class AudioEngine:
    """Listens to audio, detects BPM, energy, and estimates mood."""

    def __init__(self, device=None, samplerate=16000):
        self.device = device or self._find_mic()
        self.samplerate = samplerate
        self.hop = 512
        self.stream = None

        # Volume tracking
        self.smoothed_vol = 0.0
        self.peak_vol = 0.0
        self.silence_threshold = 0.012
        self.vol_history = collections.deque(maxlen=100)

        # Onset/beat detection
        self.onset_times = collections.deque(maxlen=200)
        self.prev_energy = 0.0
        self.onset_threshold = 1.5  # energy ratio for onset
        self.energy_history = collections.deque(maxlen=50)

        # BPM estimation
        self.bpm = 120.0
        self.bpm_confidence = 0.0
        self.last_bpm_update = 0.0

        # Spectral features for mood
        self.spectral_centroid = 0.0  # brightness
        self.spectral_energy_low = 0.0  # bass
        self.spectral_energy_high = 0.0  # treble
        self.mood = "happy"
        self.energy_level = 0.5  # 0-1 overall energy

        # Beat tracking
        self.beat_count = 0
        self.last_beat_time = 0.0
        self.expected_beat_interval = 0.5  # 120 BPM default
        self.beat_phase = 0.0

        self._lock = threading.Lock()

    @staticmethod
    def _find_mic():
        """Auto-detect the Reachy Mini microphone."""
        try:
            devices = sd.query_devices()
            # Look for reachymini_audio_src first
            for i, d in enumerate(devices):
                if 'reachymini_audio_src' in d.get('name', ''):
                    return i
            # Fall back to any input device
            for i, d in enumerate(devices):
                if d.get('max_input_channels', 0) > 0:
                    return i
        except Exception:
            pass
        return None  # Use default

    def start(self):
        # Try specified device, then fallback to default
        for dev in [self.device, None]:
            try:
                self.stream = sd.InputStream(
                    device=dev,
                    samplerate=self.samplerate,
                    blocksize=self.hop,
                    channels=1,
                    dtype="float32",
                    callback=self._callback,
                )
                self.stream.start()
                print(f"Audio: using device {dev}", flush=True)
                return
            except Exception as e:
                print(f"Audio: device {dev} failed: {e}", flush=True)
                continue
        raise RuntimeError("No working audio input device found")

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()

    def _callback(self, indata, frames, time_info, status):
        samples = indata[:, 0].astype(np.float32)
        now = time.time()

        # Volume
        vol = float(np.abs(samples).mean())
        self.smoothed_vol = self.smoothed_vol * 0.7 + vol * 0.3
        self.peak_vol = max(self.peak_vol * 0.995, vol)
        self.vol_history.append(round(vol, 4))

        if vol < self.silence_threshold:
            return

        # Energy for onset detection
        energy = float(np.sum(samples ** 2))
        self.energy_history.append(energy)

        # Onset detection: sudden energy increase
        if len(self.energy_history) > 5:
            avg_energy = np.mean(list(self.energy_history)[-10:])
            if avg_energy > 0 and energy > avg_energy * self.onset_threshold:
                # Debounce: minimum 0.15s between onsets
                if now - self.last_beat_time > 0.15:
                    self.onset_times.append(now)
                    self.last_beat_time = now
                    self.beat_count += 1

        self.prev_energy = energy

        # Spectral analysis (every few callbacks to save CPU)
        if self.beat_count % 3 == 0:
            self._analyze_spectrum(samples)

        # BPM estimation (every 2 seconds)
        if now - self.last_bpm_update > 2.0 and len(self.onset_times) > 4:
            self._estimate_bpm()
            self.last_bpm_update = now

        # Mood estimation (based on spectral features)
        self._estimate_mood()

    def _analyze_spectrum(self, samples):
        """Simple spectral analysis for mood detection."""
        fft = np.abs(np.fft.rfft(samples))
        freqs = np.fft.rfftfreq(len(samples), 1.0 / self.samplerate)

        if len(fft) == 0:
            return

        # Spectral centroid (brightness)
        total = np.sum(fft)
        if total > 0:
            self.spectral_centroid = float(np.sum(freqs * fft) / total)

        # Energy in frequency bands
        low_mask = freqs < 300  # bass
        mid_mask = (freqs >= 300) & (freqs < 2000)  # mids
        high_mask = freqs >= 2000  # treble

        self.spectral_energy_low = float(np.sum(fft[low_mask])) if np.any(low_mask) else 0
        self.spectral_energy_high = float(np.sum(fft[high_mask])) if np.any(high_mask) else 0

        # Overall energy level (normalized)
        self.energy_level = min(1.0, self.smoothed_vol * 8)

    def _estimate_bpm(self):
        """Estimate BPM from onset intervals using autocorrelation-like approach."""
        onsets = list(self.onset_times)
        if len(onsets) < 5:
            return

        # Calculate intervals between consecutive onsets
        intervals = [onsets[i + 1] - onsets[i] for i in range(len(onsets) - 1)]

        # Filter reasonable intervals (60-200 BPM range: 0.3s to 1.0s)
        valid = [i for i in intervals if 0.3 <= i <= 1.0]
        if len(valid) < 3:
            # Try half-intervals (double time)
            valid = [i for i in intervals if 0.15 <= i <= 0.5]
            if len(valid) < 3:
                return

        # Cluster intervals to find the dominant one
        # Simple approach: histogram binning
        bins = np.arange(0.15, 1.05, 0.02)
        hist, edges = np.histogram(valid, bins=bins)

        if np.max(hist) < 2:
            return

        # Find the peak bin
        peak_idx = np.argmax(hist)
        peak_interval = (edges[peak_idx] + edges[peak_idx + 1]) / 2

        # Refine: average intervals near the peak
        near_peak = [v for v in valid if abs(v - peak_interval) < 0.05]
        if near_peak:
            avg_interval = np.mean(near_peak)
            new_bpm = 60.0 / avg_interval

            # Sanity check: 60-200 BPM
            if 60 <= new_bpm <= 200:
                confidence = len(near_peak) / len(valid)
                # Smooth BPM changes
                if self.bpm_confidence < 0.3:
                    self.bpm = new_bpm
                else:
                    self.bpm = self.bpm * 0.7 + new_bpm * 0.3
                self.bpm_confidence = confidence
                self.expected_beat_interval = 60.0 / self.bpm

    def _estimate_mood(self):
        """Estimate mood from spectral features."""
        # High energy + high centroid = intense
        # High energy + low centroid = funky (bass heavy)
        # Low energy + high centroid = chill
        # Medium everything = happy

        e = self.energy_level
        bright = self.spectral_centroid

        if e > 0.7 and bright > 2000:
            self.mood = "intense"
        elif e > 0.6 and bright < 1500:
            self.mood = "funky"
        elif e < 0.35:
            self.mood = "chill"
        else:
            self.mood = "happy"

    @property
    def has_music(self):
        return self.smoothed_vol > self.silence_threshold

    def get_state(self):
        """Return current state for the dashboard."""
        return {
            "volume": round(self.smoothed_vol, 4),
            "peak_volume": round(self.peak_vol, 4),
            "volume_history": list(self.vol_history),
            "bpm": round(self.bpm),
            "bpm_confidence": round(self.bpm_confidence, 2),
            "beat_count": self.beat_count,
            "mood": self.mood,
            "energy_level": round(self.energy_level, 2),
            "spectral_centroid": round(self.spectral_centroid),
            "has_music": self.has_music,
        }
