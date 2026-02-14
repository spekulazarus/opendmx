import time
import sys
from dmx_sender import DMXSender
from audio_analyzer import AudioAnalyzer
from lighting_controller import LightingController
from web_server import start_web_server, stop_web_server
from midi_controller import MIDIController


def main():
    SERIAL_PORT = "/dev/cu.usbserial-BG03LVHM"
    AUDIO_DEVICE = "BlackHole 2ch"

    sender = DMXSender(port=SERIAL_PORT)
    try:
        sender.start()
    except Exception as e:
        print(f"Could not start DMX: {e}")
        sys.exit(1)

    controller = LightingController(sender)

    # Start MIDI
    midi = MIDIController(controller)
    midi.start()

    analyzer = AudioAnalyzer(device_name=AUDIO_DEVICE)

    start_web_server(controller, analyzer)
    analyzer.start(callback=controller.on_beat)

    print(f"\nVJ SYSTEM READY FOR TOMORROW!")
    print(f"Port: {SERIAL_PORT}")
    print(f"Web Dashboard: http://localhost:5005")

    try:
        while True:
            controller.update()
            time.sleep(0.02)
    except KeyboardInterrupt:
        pass
    finally:
        print("\nVJ SYSTEM SHUTTING DOWN...")
        analyzer.stop()
        sender.stop()
        stop_web_server()


if __name__ == "__main__":
    main()
