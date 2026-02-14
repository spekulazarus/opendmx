import time
from dmx_sender import DMXSender


def run_tester():
    print("--- DMX Fixture Tester ---")
    port = input("Serial Port (e.g. /dev/cu.usbserial-110): ").strip()
    if not port:
        port = "/dev/cu.usbserial-110"

    sender = DMXSender(port=port)
    try:
        sender.start()
    except Exception as e:
        print(f"Failed to start DMX: {e}")
        return

    print("\nCommands:")
    print("  'c' -> Set channel (e.g. 'c 1 255')")
    print("  'off' -> All channels to 0")
    print("  'q' -> Quit")

    try:
        while True:
            cmd = input("\n> ").strip().lower().split()
            if not cmd:
                continue

            if cmd[0] == "q":
                break
            elif cmd[0] == "off":
                for i in range(1, 513):
                    sender.set_channel(i, 0)
                print("All channels OFF")
            elif cmd[0] == "c" and len(cmd) == 3:
                try:
                    ch = int(cmd[1])
                    val = int(cmd[2])
                    sender.set_channel(ch, val)
                    print(f"Channel {ch} set to {val}")
                except ValueError:
                    print("Invalid input. Use: c [channel] [value]")
            else:
                print("Unknown command. Example: 'c 1 255'")
    except KeyboardInterrupt:
        pass
    finally:
        sender.stop()


if __name__ == "__main__":
    run_tester()
