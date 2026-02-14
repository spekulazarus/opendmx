import time
import random
import math
from collections import deque

class LightingController:
    def __init__(self, sender):
        self.sender = sender
        self.mode = "techno_red"
        self.audio_reactive = True
        
        self.panel1_addr = 10
        self.panel2_addr = 20
        self.party_bar_addr = 30
        
        self.last_beat_time = 0.0
        self.last_visual_beat_time = 0.0
        self.bpm = 124.0
        self.brightness = 0.0
        self.beat_count = 0
        
        self.last_debounce_time = 0.0
        self.dance_toggle = False
        
        self.p1_c = [255, 0, 0]
        self.p2_c = [255, 0, 0]
        self.pb_c = [255, 0, 0]
        self.derby_rotation = 0
        
        self.sine_mode = False
        self.color_fade_mode = False
        self.strobe_active = False
        self.glitch_mode = False
        self.alternating = False
        self.alt_state = True
        self.void_mode = False
        self.factory_mode = False
        self.pastel_mode = False
        self.police_mode = False

    def set_preset(self, preset_name):
        print(f"!!! VJ LOGIC: Preset -> {preset_name} !!!")
        self.mode = preset_name
        self.sine_mode = False
        self.color_fade_mode = False
        self.strobe_active = False
        self.glitch_mode = False
        self.alternating = False
        self.void_mode = False
        self.factory_mode = False
        self.pastel_mode = False
        self.police_mode = False
        self.derby_rotation = 255
        self.divide_by = 1
        
        # Handle both names for the rainbow
        if preset_name in ["rainbow_flow", "vivid_pop"]:
            self.color_fade_mode = True
            self.mode = "rainbow_flow"
        elif preset_name == "techno_red":
            self.p1_c = self.p2_c = self.pb_c = [255,0,0]
        elif preset_name == "acid_green":
            self.p1_c = self.p2_c = self.pb_c = [0,255,0]
        elif preset_name == "industrial_amber":
            self.sine_mode = True
            self.p1_c = [255,100,0]; self.p2_c = [255,50,0]; self.pb_c = [255,80,0]
            self.derby_rotation = 0
        elif preset_name == "minimal_void":
            self.void_mode = True
            self.derby_rotation = 0
        elif preset_name == "berlin_white":
            self.p1_c = self.p2_c = self.pb_c = [255,255,255]
        elif preset_name == "barbie_party":
            self.p1_c = [255,20,147]; self.p2_c = [255,105,180]; self.pb_c = [255,0,255]
        elif preset_name == "dance_rg":
            self.derby_rotation = 0
        elif preset_name == "alternating_kick":
            self.alternating = True
            self.p1_c = self.p2_c = self.pb_c = [255,0,0]
        elif preset_name == "minimal_glitch":
            self.glitch_mode = True
        elif preset_name == "strobe_white":
            self.strobe_active = True
        elif preset_name == "code_red":
            self.police_mode = True
        elif preset_name == "factory_floor":
            self.factory_mode = True
        elif preset_name == "pastel_dreams":
            self.pastel_mode = True
        elif preset_name == "blackout":
            self.derby_rotation = 0

    def on_beat(self, precise_time=None):
        if not self.audio_reactive: return
        t = float(precise_time) if precise_time else float(time.time())
        if t - self.last_debounce_time > 0.2:
            self.last_beat_time = t
            self.last_debounce_time = t
            self._process_beat()

    def _process_beat(self):
        if self.mode == "blackout": return
        self.beat_count += 1
        self.last_visual_beat_time = float(time.time())
        self.dance_toggle = not self.dance_toggle
        if self.alternating: self.alt_state = not self.alt_state
        self.brightness = 1.0

    def update(self):
        now = float(time.time())
        if self.audio_reactive and self.bpm > 0:
            beat_interval = 60.0 / float(self.bpm)
            if now - self.last_beat_time >= beat_interval:
                self.last_beat_time = now
                self._process_beat()

        eff_b = 1.0
        o_p1, o_p2, o_pb = self.p1_c, self.p2_c, self.pb_c
        
        if self.mode == "blackout":
            self._apply_off(); return
            
        if self.strobe_active:
            eff_b = 1.0 if (int(now * 30) % 2 == 0) else 0.0
            self._apply_panel(self.panel1_addr, [255,255,255], eff_b)
            self._apply_panel(self.panel2_addr, [255,255,255], eff_b)
            self._apply_party_bar_strobe(eff_b)
            return

        if self.mode == "dance_rg":
            if self.dance_toggle: o_p1, o_p2, o_pb = [255,0,0], [0,255,0], [255,0,0]
            else: o_p1, o_p2, o_pb = [0,255,0], [255,0,0], [0,255,0]
            eff_b = 1.0
        elif self.police_mode:
            if self.dance_toggle: o_p1, o_p2, o_pb = [255,0,0], [0,0,255], [255,0,0]
            else: o_p1, o_p2, o_pb = [0,0,255], [255,0,0], [0,0,255]
            eff_b = 1.0 if (int(now * 15) % 2 == 0) else 0.2
        elif self.color_fade_mode:
            # RAINBOW FLOW: Solid 100% brightness, slow color cycle
            period = 10.0 # 10 seconds for a full loop
            hue = (now % period) / period
            o_p1 = self._hsv_to_rgb(hue, 1.0, 1.0)
            o_p2 = self._hsv_to_rgb((hue + 0.1) % 1.0, 1.0, 1.0)
            o_pb = self._hsv_to_rgb((hue + 0.2) % 1.0, 1.0, 1.0)
            eff_b = 1.0
        elif self.sine_mode:
            period = (60.0 / self.bpm) * 16 if self.bpm > 0 else 8.0
            eff_b = 0.425 + 0.375 * math.sin((now * 2 * math.pi) / period)
        elif self.void_mode:
            period = (60.0 / self.bpm) * 32 if self.bpm > 0 else 15.0
            mix = 0.5 + 0.5 * math.sin((now * 2 * math.pi) / period)
            o_p1 = [int(45*mix + 128*(1-mix)), int(27*mix), int(105*mix + 32*(1-mix))]
            o_p2 = [int(128*mix + 45*(1-mix)), int(0), int(32*mix + 105*(1-mix))]
            o_pb = o_p1; eff_b = 0.8
        elif self.factory_mode:
            period = (60.0 / self.bpm) * 8 if self.bpm > 0 else 4.0
            mix = 0.5 + 0.5 * math.sin((now * 2 * math.pi) / period)
            o_p1 = [int(70*mix + 240*(1-mix)), int(130*mix + 248*(1-mix)), int(180*mix + 255*(1-mix))]
            o_p2 = [int(240*mix + 70*(1-mix)), int(248*mix + 130*(1-mix)), int(255*mix + 180*(1-mix))]
            o_pb = [255, 128, 0] if mix > 0.8 else o_p1; eff_b = 0.8
        elif self.pastel_mode:
            bc = (self.beat_count // 2) % 4
            if bc == 0: o_p1, o_p2 = [255,182,193], [230,230,250]
            elif bc == 1: o_p1, o_p2 = [255,203,164], [135,206,235]
            elif bc == 2: o_p1, o_p2 = [230,230,250], [255,182,193]
            else: o_p1, o_p2 = [135,206,235], [255,203,164]
            o_pb = o_p1; self.brightness *= 0.92; eff_b = 0.4 + 0.6 * self.brightness
        elif self.glitch_mode:
            eff_b = 1.0 if random.random() > 0.95 else 0.05
        elif self.audio_reactive:
            self.brightness *= 0.85
            eff_b = self.brightness

        if self.alternating:
            b1 = eff_b if self.alt_state else 0.0; b2 = eff_b if not self.alt_state else 0.0
            self._apply_panel(self.panel1_addr, o_p1, b1); self._apply_panel(self.panel2_addr, o_p2, b2)
        else:
            self._apply_panel(self.panel1_addr, o_p1, eff_b); self._apply_panel(self.panel2_addr, o_p2, eff_b)

        self._apply_party_bar_normal(o_pb, eff_b)

    def _apply_party_bar_strobe(self, brightness):
        addr = self.party_bar_addr; val = int(255 * brightness)
        for i in range(15): self.sender.set_channel(addr + i, 0)
        self.sender.set_channel(addr + 5, val); self.sender.set_channel(addr + 6, val); self.sender.set_channel(addr + 7, val); self.sender.set_channel(addr + 8, val)

    def _apply_party_bar_normal(self, rgb, brightness):
        addr = self.party_bar_addr; r, g, b = [int(float(c) * float(brightness)) for c in rgb]
        rot = self.derby_rotation
        self.sender.set_channel(addr + 0, r); self.sender.set_channel(addr + 1, g); self.sender.set_channel(addr + 2, b); self.sender.set_channel(addr + 3, 0); self.sender.set_channel(addr + 4, rot)
        self.sender.set_channel(addr + 5, r); self.sender.set_channel(addr + 6, g); self.sender.set_channel(addr + 7, b); self.sender.set_channel(addr + 8, 0)
        self.sender.set_channel(addr + 9, r); self.sender.set_channel(addr + 10, g); self.sender.set_channel(addr + 11, b); self.sender.set_channel(addr + 12, 0); self.sender.set_channel(addr + 13, rot)

    def _hsv_to_rgb(self, h, s, v):
        i = int(h * 6); f = h * 6 - i; p = v * (1 - s); q = v * (1 - f * s); t = v * (1 - (1 - f) * s)
        r, g, b = 0, 0, 0
        if i % 6 == 0: r, g, b = v, t, p
        elif i % 6 == 1: r, g, b = q, v, p
        elif i % 6 == 2: r, g, b = p, v, t
        elif i % 6 == 3: r, g, b = p, q, v
        elif i % 6 == 4: r, g, b = t, p, v
        elif i % 6 == 5: r, g, b = v, p, q
        return [int(r * 255), int(g * 255), int(b * 255)]

    def _apply_panel(self, addr, rgb, brightness):
        r, g, b = [int(float(c) * float(brightness)) for c in rgb]
        self.sender.set_channel(addr, 255); self.sender.set_channel(addr+1, r); self.sender.set_channel(addr+2, g); self.sender.set_channel(addr+3, b)

    def _apply_off(self):
        for i in range(1, 65): self.sender.set_channel(i, 0)

    def set_address(self, fixture, addr):
        if fixture == "panel1": self.panel1_addr = int(addr)
        if fixture == "panel2": self.panel2_addr = int(addr)
        if fixture == "party_bar": self.party_bar_addr = int(addr)
