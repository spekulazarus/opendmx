import mido
import time

print("MIDI Test Tool - Press keys on your LPK25...")
try:
    port_name = None
    for name in mido.get_input_names():
        if "LPK25" in name: port_name = name
    
    if not port_name:
        print("Error: LPK25 not found!")
    else:
        with mido.open_input(port_name) as inport:
            print(f"Listening on {port_name}. Press keys now.")
            for msg in inport:
                if msg.type == 'note_on':
                    print(f"Key Pressed! Note: {msg.note} | Velocity: {msg.velocity}")
except KeyboardInterrupt:
    print("\nTest stopped.")
