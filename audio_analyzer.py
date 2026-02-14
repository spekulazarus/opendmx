import pyaudio
import numpy as np
import threading
import time
from collections import deque


class AudioAnalyzer:
    def __init__(self, device_name="BlackHole 2ch", rate=44100, chunk=2048):
        self.rate = rate
        self.chunk = chunk
        self.device_name = device_name
        self.device_index = None
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.running = False
        self.on_beat_callback = None

        self.threshold = 1.3
        self.history_size = 40
        self.history = deque(maxlen=self.history_size)

        self.last_beat_time = 0.0
        self.min_interval = 0.36

        self.current_volume = 0.0
        self.current_device_name = "Searching..."

        self.prev_energy = 0.0
        self.energy_diff_history = deque(maxlen=15)

        self.prev_fft = None
        self.flux_threshold = 0.3

    def list_devices(self):
        devices = []
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            max_inputs = dev.get("maxInputChannels", 0)
            if isinstance(max_inputs, (int, float)) and max_inputs > 0:
                devices.append(
                    {
                        "index": i,
                        "name": dev.get("name", "Unknown"),
                        "channels": int(max_inputs),
                    }
                )
        return devices

    def find_device_index(self):
        for i in range(self.p.get_device_count()):
            dev = self.p.get_device_info_by_index(i)
            name = dev.get("name")
            if isinstance(name, str) and self.device_name in name:
                return i
        return None

    def set_device(self, index):
        was_running = self.running
        self.stop_stream()
        self.device_index = index
        try:
            dev_info = self.p.get_device_info_by_index(index)
            self.current_device_name = dev_info.get("name", f"Index {index}")
        except:
            self.current_device_name = f"Index {index}"
        if was_running:
            self.start_stream()

    def stop_stream(self):
        self.running = False
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except:
                pass
            self.stream = None

    def start_stream(self):
        try:
            self.stream = self.p.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.chunk,
            )
            self.running = True
            if (
                self.current_device_name == "Searching..."
                and self.device_index is not None
            ):
                try:
                    dev_info = self.p.get_device_info_by_index(self.device_index)
                    self.current_device_name = dev_info.get("name", "Unknown")
                except:
                    pass
            print(f"Audio Stream started: {self.current_device_name}")
        except Exception as e:
            print(f"Error starting audio stream: {e}")

    def start(self, callback=None):
        self.on_beat_callback = callback
        if self.device_index is None:
            self.device_index = self.find_device_index()
        self.start_stream()
        self.thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_stream()
        self.p.terminate()

    def _analysis_loop(self):
        while self.running:
            if not self.stream:
                time.sleep(0.1)
                continue
            try:
                chunk_time = time.time()
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)

                # Precise Peak Time for Sync
                peak_idx = np.argmax(np.abs(samples))
                precise_time = chunk_time + (peak_idx / float(self.rate))

                # Volume for UI
                self.current_volume = float(np.max(np.abs(samples)) / 32768.0)

                beat_detected = self._detect_beat(samples, precise_time)
                if beat_detected and self.on_beat_callback:
                    self.on_beat_callback(precise_time)
            except Exception as e:
                print(f"Audio Loop Error: {e}")
                break

    def _detect_beat(self, samples, current_time):
        self.current_volume = np.max(np.abs(samples)) / 32768.0

        fft = np.fft.rfft(samples)
        freqs = np.fft.rfftfreq(len(samples), 1.0 / self.rate)

        bass_indices = np.where((freqs > 30) & (freqs < 85))[0]
        if len(bass_indices) == 0:
            return False

        bass_energy = np.mean(np.abs(fft[bass_indices]))

        energy_diff = bass_energy - self.prev_energy if self.prev_energy > 0 else 0
        self.prev_energy = bass_energy
        self.energy_diff_history.append(energy_diff)

        spectral_flux = 0.0
        bass_fft_abs = np.abs(fft[bass_indices])
        if self.prev_fft is not None and len(self.prev_fft) == len(bass_fft_abs):
            flux_diff = bass_fft_abs - self.prev_fft
            spectral_flux = np.sum(np.maximum(0, flux_diff))
        self.prev_fft = bass_fft_abs

        if len(self.history) >= 10:
            avg_energy = np.mean(self.history)
            avg_energy_diff = (
                np.mean(self.energy_diff_history)
                if len(self.energy_diff_history) > 5
                else 0
            )

            energy_trigger = (bass_energy > avg_energy * self.threshold) and (
                energy_diff > avg_energy_diff * 1.2
            )
            flux_trigger = spectral_flux > self.flux_threshold

            time_since_last = current_time - self.last_beat_time
            if (energy_trigger or flux_trigger) and time_since_last > self.min_interval:
                self.last_beat_time = current_time
                self.history.append(bass_energy)
                return True

        self.history.append(bass_energy)
        return False


if __name__ == "__main__":

    def my_beat_trigger():
        print("BEAT! \U0001f941")

    analyzer = AudioAnalyzer()
    analyzer.start(callback=my_beat_trigger)
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        analyzer.stop()
