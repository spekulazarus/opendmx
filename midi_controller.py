import mido
import threading
import time

class MIDIController:
    def __init__(self, lighting_controller):
        self.lc = lighting_controller
        self.running = False
        self.thread = None
        self.last_preset = "techno_red"
        
        # Exact Mapping from your AKAI LPK25 test log
        self.mapping = {
            48: "techno_red",
            50: "acid_green",
            52: "industrial_amber",
            53: "berlin_white",
            
            55: "house_shuffle",
            57: "dance_rg",
            59: "alternating_kick",
            60: "minimal_glitch",
            
            62: "barbie_party",
            64: "vivid_pop",
            65: "sunset_slow",
            67: "pastel_dream",
            
            72: "blackout"
        }
        self.strobe_note = 71

    def start(self):
        try:
            # Explicitly look for 'LPK25' as seen in the test
            port_name = None
            for name in mido.get_input_names():
                if "LPK25" in name:
                    port_name = name
                    break
            
            if not port_name:
                print("MIDI: AKAI LPK25 port not found in mido.get_input_names()")
                return

            self.running = True
            self.thread = threading.Thread(target=self._listen, args=(port_name,), daemon=True)
            self.thread.start()
            print(f"MIDI: SUCCESS! Now listening on {port_name}")
        except Exception as e:
            print(f"MIDI Startup Error: {e}")

    def _listen(self, port_name):
        try:
            with mido.open_input(port_name) as inport:
                for msg in inport:
                    if not self.running: break
                    
                    # Log to console so we see it working in dmx_debug.log
                    print(f"MIDI Input: {msg}")
                    
                    if msg.type == 'note_on' and msg.velocity > 0:
                        if msg.note == self.strobe_note:
                            self.lc.set_preset("strobe_white")
                        elif msg.note in self.mapping:
                            preset = self.mapping[msg.note]
                            self.last_preset = preset
                            self.lc.set_preset(preset)
                            
                    elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                        if msg.note == self.strobe_note:
                            # Revert to last used preset after strobe
                            self.lc.set_preset(self.last_preset)
        except Exception as e:
            print(f"MIDI Runtime Error: {e}")
