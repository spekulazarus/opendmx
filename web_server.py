from flask import Flask, render_template_string, request, jsonify
import threading
import time

app = Flask(__name__)
controller = None
audio_analyzer = None

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>LIGHTWEIGHT VJ PRO</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
        :root { --bg: #050505; --surface: #121212; --primary: #f00; --text: #eee; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 10px; overflow-x: hidden; touch-action: manipulation; }
        
        .header { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #222; margin-bottom: 10px; }
        .bpm-display { font-size: 32px; font-weight: 900; color: var(--primary); font-family: monospace; }
        .beat-dot { width: 18px; height: 18px; border-radius: 50%; background: #222; border: 2px solid #333; }
        .beat-dot.active { background: var(--primary); box-shadow: 0 0 15px var(--primary); border-color: #fff; }

        .vj-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 15px; }
        
        .btn { 
            position: relative; padding: 22px 5px; font-size: 13px; font-weight: bold; border: none; border-radius: 10px;
            background: var(--surface); color: var(--text); text-transform: uppercase; transition: all 0.05s;
            box-shadow: 0 3px 0 #000; border: 1px solid #222;
        }
        .btn:active { transform: translateY(2px); box-shadow: none; filter: brightness(1.5); }
        .btn.active-mode { border: 2px solid #fff !important; box-shadow: 0 0 10px rgba(255,255,255,0.2); }

        .btn-techno { border-left: 4px solid #d00; }
        .btn-house { border-left: 4px solid #f80; }
        .btn-pop { border-left: 4px solid #f0f; }

        .strobe-area { margin-top: 10px; }
        .btn-strobe { 
            width: 100%; padding: 35px 0; background: #fff; color: #000; font-size: 22px; font-weight: 900;
            border-radius: 12px; box-shadow: 0 5px 0 #888; border: none;
        }
        .btn-strobe:active { background: #ff0; transform: translateY(2px); box-shadow: 0 2px 0 #666; }

        .btn-blackout { width: 100%; background: #222; color: #555; margin-top: 15px; padding: 12px; font-size: 11px; border: 1px solid #333; border-radius: 8px; }

        .settings-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.98);
            display: none; z-index: 100; padding: 20px; box-sizing: border-box;
        }
        .vj-label { font-size: 9px; color: #444; text-align: left; margin: 10px 0 5px 2px; text-transform: uppercase; letter-spacing: 2px; font-weight: bold; }
        .config-row { display: flex; justify-content: space-between; margin: 15px 0; align-items: center; }
        input[type=number] { width: 60px; padding: 8px; background: #111; color: #fff; border: 1px solid #333; border-radius: 4px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="bpm-display" id="bpm-val">--</div>
        <div class="beat-dot" id="beat-dot"></div>
        <button onclick="toggleSettings()" style="background:none; border:none; color:#333; font-size:24px; padding:10px;">⚙️</button>
    </div>

    <div class="vj-label">Techno / Dark</div>
    <div class="vj-grid">
        <button class="btn btn-techno" onclick="setPreset('techno_red', this)">Red Pulse</button>
        <button class="btn btn-techno" onclick="setPreset('acid_green', this)">Acid Green</button>
        <button class="btn btn-techno" onclick="setPreset('industrial_amber', this)">Industrial Amber</button>
        <button class="btn btn-techno" onclick="setPreset('minimal_void', this)">Minimal Void</button>
    </div>

    <div class="vj-label">House / Shuffle</div>
    <div class="vj-grid">
        <button class="btn btn-house" onclick="setPreset('white_kick', this)">White Kick</button>
        <button class="btn btn-house" onclick="setPreset('dance_rg', this)">R/G Dance</button>
        <button class="btn btn-house" onclick="setPreset('alternating_kick', this)">Alt Kick</button>
        <button class="btn btn-house" onclick="setPreset('factory_floor', this)">Factory Floor</button>
    </div>

    <div class="vj-label">Pop / FX</div>
    <div class="vj-grid">
        <button class="btn btn-pop" onclick="setPreset('barbie_party', this)">Barbie Party</button>
        <button class="btn btn-pop" onclick="setPreset('pastel_dreams', this)">Pastel Dreams</button>
        <button class="btn btn-pop" onclick="setPreset('rainbow_flow', this)">Rainbow Flow</button>
        <button class="btn btn-pop" onclick="setPreset('code_red', this)">Police / Alarm</button>
    </div>

    <div class="vj-grid">
        <button class="btn btn-pop" style="border-left-color:#fff" onclick="setPreset('minimal_glitch', this)">Minimal Glitch</button>
        <button class="btn btn-pop" style="border-left-color:#fff" onclick="setPreset('digital_decay', this)">Digital Decay</button>
    </div>

    <div class="strobe-area">
        <button class="btn btn-strobe" id="strobe-btn" 
            onmousedown="startStrobe()" onmouseup="stopStrobe()" 
            ontouchstart="startStrobe()" ontouchend="stopStrobe()">STROBE</button>
    </div>

    <button class="btn btn-blackout" onclick="setPreset('blackout', this)">MASTER BLACKOUT</button>

    <div id="settings" class="settings-overlay">
        <div onclick="toggleSettings()" style="float:right; font-size:40px; color:#555;">×</div>
        <div style="max-width:400px; margin:40px auto; text-align:left;">
            <h2 style="color:var(--primary)">Console Settings</h2>
            <div class="config-row"><span>Audio Engine Active</span><input type="checkbox" checked onchange="setAudioReactive(this.checked)" style="width:25px; height:25px;"></div>
            <hr style="border:0; border-top:1px solid #222;">
            <div class="config-row"><span>Panel 1 DMX:</span><input type="number" value="10" onchange="updateAddr('panel1', this.value)"></div>
            <div class="config-row"><span>Panel 2 DMX:</span><input type="number" value="20" onchange="updateAddr('panel2', this.value)"></div>
            <div class="config-row"><span>Party Bar DMX:</span><input type="number" value="30" onchange="updateAddr('party_bar', this.value)"></div>
            <p style="font-size:10px; color:#333; margin-top:50px;">LIGHTWEIGHT VJ PRO - V1.5.0</p>
        </div>
    </div>

    <script>
        let lastPreset = 'techno_red';
        function setPreset(name, btn) {
            if(name !== 'strobe_white') lastPreset = name;
            fetch('/set_preset?name=' + name);
            if(btn) {
                document.querySelectorAll('.btn').forEach(b => b.classList.remove('active-mode'));
                btn.classList.add('active-mode');
            }
        }
        function startStrobe() { fetch('/set_preset?name=strobe_white'); }
        function stopStrobe() { fetch('/set_preset?name=' + lastPreset); }
        function setAudioReactive(e) { fetch('/set_audio_reactive?enabled=' + e); }
        function updateAddr(f, a) { fetch('/set_address?fixture=' + f + '&addr=' + a); }
        function toggleSettings() { 
            const s = document.getElementById('settings');
            s.style.display = s.style.display === 'block' ? 'none' : 'block';
        }

        setInterval(() => {
            fetch('/get_status').then(r => r.json()).then(data => {
                const bpm = parseFloat(data.bpm);
                document.getElementById('bpm-val').innerText = bpm > 0 ? Math.round(bpm) : '--';
                const dot = document.getElementById('beat-dot');
                if (data.last_beat_age < 0.08) dot.classList.add('active');
                else dot.classList.remove('active');
            });
        }, 80);
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/get_status")
def get_status():
    import time
    last_beat = controller.last_visual_beat_time if controller else 0
    return jsonify({
        "last_beat_age": float(time.time() - last_beat),
        "bpm": float(controller.bpm) if controller else 0.0
    })

@app.route("/set_preset")
def set_preset():
    name = request.args.get("name")
    if controller: controller.set_preset(name)
    return "OK"

@app.route("/set_audio_reactive")
def set_audio_reactive():
    enabled = request.args.get("enabled") == "true"
    if controller: controller.audio_reactive = enabled
    return "OK"

@app.route("/set_address")
def set_address():
    f = request.args.get("fixture"); a = request.args.get("addr")
    if controller: controller.set_address(f, a)
    return "OK"

def start_web_server(lighting_controller, analyzer=None):
    global controller, audio_analyzer
    controller = lighting_controller
    audio_analyzer = analyzer
    thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5005, debug=False, use_reloader=False),
        daemon=True
    )
    thread.start()
    print("Web Control available at http://localhost:5005")

def stop_web_server():
    pass
