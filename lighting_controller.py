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
        self.divide_by = 1
        
        self.panel1_color = [255, 0, 0]
        self.panel2_color = [255, 0, 0]
        
        self.auto_color_change = False
        self.alternating = False
        self.alt_state = True
        self.dance_mode = False
        self.sine_mode = False
        self.color_fade_mode = False
        self.strobe_active = False
        self.glitch_mode = False
        self.pop_pastel = False
        self.barbie_mode = False

    def set_preset(self, preset_name):
        # CRITICAL: This is the method MIDI calls!
        print(f"!!! LOGIC: Setting Preset to {preset_name} !!!")
        
        self.auto_color_change = False
        self.alternating = False
        self.dance_mode = False
        self.sine_mode = False
        self.color_fade_mode = False
        self.strobe_active = False
        self.glitch_mode = False
        self.pop_pastel = False
        self.barbie_mode = False
        self.divide_by = 1
        self.mode = preset_name # Set mode first
        
        if preset_name == "techno_red":
            self.mode = "pulse"
            self.panel1_color = [255, 0, 0]
            self.panel2_color = [255, 0, 0]
        elif preset_name == "acid_green":
            self.mode = "pulse"
            self.panel1_color = [50, 255, 0]
            self.panel2_color = [200, 255, 0]
        elif preset_name == "industrial_amber":
            self.mode = "sine"
            self.sine_mode = True
            self.panel1_color = [255, 100, 0]
            self.panel2_color = [255, 50, 0]
        elif preset_name == "berlin_white":
            self.mode = "pulse"
            self.panel1_color = [255, 255, 255]
            self.panel2_color = [255, 255, 255]
        elif preset_name == "house_shuffle":
            self.mode = "pulse"
            self.alternating = True
            self.panel1_color = [255, 255, 0]
            self.panel2_color = [0, 255, 255]
        elif preset_name == "vivid_pop":
            self.mode = "rainbow"
            self.color_fade_mode = True
        elif preset_name == "barbie_party":
            self.mode = "pulse"
            self.barbie_mode = True
        elif preset_name == "dance_rg":
            self.mode = "static"
            self.dance_mode = True
            self.panel1_color = [255, 0, 0]
            self.panel2_color = [0, 255, 0]
        elif preset_name == "minimal_glitch":
            self.mode = "glitch"
            self.glitch_mode = True
        elif preset_name == "strobe_white":
            self.mode = "strobe"
            self.strobe_active = True
        elif preset_name == "blackout":
            self.mode = "blackout"

    def on_beat(self):
        if not self.audio_reactive: return
        self.last_beat_time = float(time.time())
        self._process_beat()

    def _process_beat(self):
        if self.mode == "blackout": return
        self.beat_count += 1
        self.last_visual_beat_time = float(time.time())
        
        if self.beat_count % self.divide_by == 0:
            if self.alternating: self.alt_state = not self.alt_state
            if self.dance_mode:
                self.panel1_color, self.panel2_color = self.panel2_color, self.panel1_color
            if self.barbie_mode:
                pinks = [[255,20,147], [255,105,180], [255,0,255]]
                self.panel1_color = random.choice(pinks)
                self.panel2_color = random.choice(pinks)
            if self.mode == "pulse": self.brightness = 1.0

    def update(self):
        now = float(time.time())
        if self.audio_reactive and self.bpm > 0:
            beat_interval = 60.0 / float(self.bpm)
            if now - self.last_beat_time >= beat_interval:
                self.last_beat_time = now
                self._process_beat()

        eff_b = 1.0
        p1_c, p2_c = self.panel1_color, self.panel2_color
        
        if self.mode == "blackout":
            self._apply_off()
            return
        elif self.mode == "strobe":
            eff_b = 1.0 if (int(now * 30) % 2 == 0) else 0.0
            p1_c, p2_c = [255,255,255], [255,255,255]
        elif self.glitch_mode or self.mode == "glitch":
            eff_b = 1.0 if random.random() > 0.95 else 0.05
        elif self.color_fade_mode or self.mode == "rainbow":
            period = (60.0 / self.bpm) * 32 if self.bpm > 0 else 10.0
            hue = (now % period) / period
            self.panel1_color = self._hsv_to_rgb(hue, 1.0, 1.0)
            self.panel2_color = self._hsv_to_rgb((hue + 0.1) % 1.0, 1.0, 1.0)
            p1_c, p2_c = self.panel1_color, self.panel2_color
            eff_b = 1.0
        elif self.sine_mode or self.mode == "sine":
            period = (60.0 / self.bpm) * 16 if self.bpm > 0 else 8.0
            eff_b = 0.425 + 0.375 * math.sin((now * 2 * math.pi) / period)
        elif self.mode == "pulse":
            if self.audio_reactive:
                self.brightness *= 0.85
                eff_b = self.brightness
            else:
                eff_b = 1.0

        if self.alternating and self.mode == "pulse":
            b1 = eff_b if self.alt_state else 0.0
            b2 = eff_b if not self.alt_state else 0.0
            self._apply_panel(self.panel1_addr, p1_c, b1)
            self._apply_panel(self.panel2_addr, p2_c, b2)
        else:
            self._apply_panel(self.panel1_addr, p1_c, eff_b)
            self._apply_panel(self.panel2_addr, p2_c, eff_b)

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
        self.sender.set_channel(addr, 255)
        self.sender.set_channel(addr+1, r)
        self.sender.set_channel(addr+2, g)
        self.sender.set_channel(addr+3, b)

    def _apply_off(self):
        for i in range(1, 65): self.sender.set_channel(i, 0)

    def set_address(self, fixture, addr):
        if fixture == "panel1": self.panel1_addr = int(addr)
        if fixture == "panel2": self.panel2_addr = int(addr)
