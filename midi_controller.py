import mido
import threading
import time

class MIDIController:
    def __init__(self, lighting_controller):
        self.lc = lighting_controller
        self.running = False
        self.thread = None
        self.last_preset = "techno_red"
        
        # STRICT WHITE KEY MAPPING (48 to 72)
        self.mapping = {
            48: "techno_red",      # Key 1
            50: "acid_green",      # Key 2
            52: "industrial_amber",# Key 3
            53: "white_kick",      # Key 4
            55: "minimal_void",    # Key 5
            57: "dance_rg",        # Key 6
            59: "factory_floor",   # Key 7
            60: "code_red",        # Key 8
            62: "pastel_dreams",   # Key 9
            64: "rainbow_flow",    # Key 10
            65: "barbie_party",    # Key 11
            67: "minimal_glitch",  # Key 12
            69: "alternating_kick",# Key 13
            72: "blackout"         # Key 15
        }
        self.strobe_note = 71      # Key 14 (B)

    def start(self):
        try:
            ports = mido.get_input_names()
            target_port = next((p for p in ports if "LPK25" in p), None)
            
            if not target_port:
                print("MIDI: LPK25 not found.")
                return

            self.running = True
            self.thread = threading.Thread(target=self._listen, args=(target_port,), daemon=True)
            self.thread.start()
            print(f"MIDI: Active on {target_port} (White Keys Only)")
        except Exception as e:
            print(f"MIDI Error: {e}")

    def _listen(self, port_name):
        try:
            with mido.open_input(port_name) as inport:
                for msg in inport:
                    if not self.running: break
                    if msg.type == 'note_on' and msg.velocity > 0:
                        if msg.note == self.strobe_note:
                            self.lc.set_preset("strobe_white")
                        elif msg.note in self.mapping:
                            preset = self.mapping[msg.note]
                            if preset != "blackout": self.last_preset = preset
                            self.lc.set_preset(preset)
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        if msg.note == self.strobe_note:
                            self.lc.set_preset(self.last_preset)
        except Exception as e:
            print(f"MIDI Runtime Error: {e}")
