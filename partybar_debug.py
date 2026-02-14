import time
import sys
from dmx_sender import DMXSender


def partybar_debug():
    SERIAL_PORT = "/dev/cu.usbserial-BG03LVHM"
    START_ADDR = 30
    NUM_CHANNELS = 15  # 15CH mode

    print("--- PARTYBAR 2 DEBUGGER ---")
    print(f"Targeting Port: {SERIAL_PORT}")
    print(f"Base Address: {START_ADDR}")
    print("Commands: Enter channel index (1-15) or 'n' for next, 'q' to quit.")

    sender = DMXSender(port=SERIAL_PORT)
    try:
        sender.start()
    except Exception as e:
        print(f"Error: {e}")
        return

    current_ch = 1

    try:
        while True:
            # Reset all Partybar channels
            for i in range(NUM_CHANNELS):
                sender.set_channel(START_ADDR + i, 0)

            # Fire current channel
            sender.set_channel(START_ADDR + current_ch - 1, 255)

            print(
                f"\n>>> TESTING CHANNEL {START_ADDR + current_ch - 1} (Offset {current_ch}) <<<"
            )
            print("What do you see?")

            cmd = input("Channel Index (1-15), [n]ext, or [q]uit: ").strip().lower()

            if cmd == "q":
                break
            elif cmd == "n" or cmd == "":
                current_ch = (current_ch % NUM_CHANNELS) + 1
            else:
                try:
                    val = int(cmd)
                    if 1 <= val <= NUM_CHANNELS:
                        current_ch = val
                    else:
                        print("Please enter 1-15.")
                except ValueError:
                    print("Invalid input.")

    except KeyboardInterrupt:
        pass
    finally:
        # All OFF before exit
        for i in range(NUM_CHANNELS):
            sender.set_channel(START_ADDR + i, 0)
        time.sleep(0.5)
        sender.stop()
        print("\nDebug stopped.")


if __name__ == "__main__":
    partybar_debug()
