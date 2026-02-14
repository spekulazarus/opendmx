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

        self.flux_history = deque(maxlen=128)
        self.last_beat_time = 0.0
        self.min_interval = 0.25

        self.current_volume = 0.0
        self.current_device_name = "Searching..."
        self.prev_log_mag = None

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
                t_capture = time.perf_counter()
                data = self.stream.read(self.chunk, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.int16).astype(np.float32)

                self.current_volume = float(np.max(np.abs(samples)) / 32768.0)

                beat_detected, precise_time = self._detect_beat(samples, t_capture)

                if beat_detected and self.on_beat_callback:
                    self.on_beat_callback(precise_time)
            except Exception as e:
                print(f"Audio Loop Error: {e}")
                break

    def _detect_beat(self, samples, t_capture):
        fft = np.fft.rfft(samples)
        mag = np.abs(fft)

        freqs = np.fft.rfftfreq(len(samples), 1.0 / self.rate)
        bass_idx = np.where((freqs >= 20) & (freqs <= 200))[0]
        bass_mag = mag[bass_idx]

        log_mag = np.log10(bass_mag + 1.0)
        flux = 0.0
        if self.prev_log_mag is not None and len(self.prev_log_mag) == len(log_mag):
            flux = float(np.sum(np.maximum(0, log_mag - self.prev_log_mag)))
        self.prev_log_mag = log_mag

        self.flux_history.append(flux)

        if len(self.flux_history) > 20:
            local_flux = list(self.flux_history)
            threshold = np.median(local_flux) * 2.5 + 0.1

            if flux > threshold:
                now = time.perf_counter()
                if now - self.last_beat_time > self.min_interval:
                    peak_in_chunk = np.argmax(np.abs(samples))
                    precise_t = t_capture + (peak_in_chunk / float(self.rate))

                    self.last_beat_time = now
                    return True, precise_t

        return False, 0.0


if __name__ == "__main__":

    def test_cb(t):
        print(f"BEAT at {t:.3f}")

    a = AudioAnalyzer()
    a.start(callback=test_cb)
    try:
        while True:
            time.sleep(1)
    except:
        a.stop()
