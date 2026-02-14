import mido
import time

print("MIDI Detector started. Looking for ANY input...")
print(f"Initial inputs: {mido.get_input_names()}")

start_time = time.time()
ports = {}

try:
    while time.time() - start_time < 30:
        current_inputs = mido.get_input_names()
        for name in current_inputs:
            if name not in ports:
                print(f"--- NEW DEVICE DETECTED: {name} ---")
                try:
                    ports[name] = mido.open_input(name)
                    print(f"Successfully opened: {name}")
                except Exception as e:
                    print(f"Could not open {name}: {e}")

        for name, port in ports.items():
            for msg in port.iter_pending():
                print(f"[{name}] {msg}")

        time.sleep(0.1)
except KeyboardInterrupt:
    pass
finally:
    for port in ports.values():
        port.close()
    print("Detector stopped.")
