from flask import Flask, render_template_string, request, jsonify
import threading

app = Flask(__name__)
controller = None

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>LIGHTWEIGHT VJ PRO</title>
    <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=0">
    <style>
        :root { --bg: #0a0a0a; --surface: #1a1a1a; --primary: #f00; --text: #eee; }
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 10px; overflow-x: hidden; touch-action: manipulation; }
        
        .header { display: flex; justify-content: space-between; align-items: center; padding: 10px; }
        .bpm-display { font-size: 32px; font-weight: 900; font-variant-numeric: tabular-nums; color: var(--primary); }
        .beat-dot { width: 20px; height: 20px; border-radius: 50%; background: #222; border: 2px solid #333; }
        .beat-dot.active { background: var(--primary); box-shadow: 0 0 15px var(--primary); border-color: #fff; }

        .vj-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; }
        
        .btn { 
            position: relative; padding: 25px 5px; font-size: 14px; font-weight: bold; border: none; border-radius: 12px;
            background: var(--surface); color: var(--text); text-transform: uppercase; transition: all 0.1s;
            box-shadow: inset 0 1px 0 rgba(255,255,255,0.1), 0 4px 0 #000;
        }
        .btn:active { transform: translateY(2px); box-shadow: none; filter: brightness(1.5); }
        .btn.active-mode { border: 2px solid #fff; box-shadow: 0 0 10px rgba(255,255,255,0.3); }

        /* Categorized Buttons */
        .btn-techno { border-left: 5px solid #d00; }
        .btn-house { border-left: 5px solid #f80; }
        .btn-pop { border-left: 5px solid #f0f; }
        .btn-fx { border-left: 5px solid #0f0; }

        .strobe-area { grid-column: span 2; margin-top: 5px; }
        .btn-strobe { 
            width: 100%; padding: 40px 0; background: #fff; color: #000; font-size: 24px; 
            box-shadow: 0 6px #ccc; border-radius: 15px; 
        }
        .btn-strobe:active { background: #ff0; box-shadow: 0 2px #888; }

        .btn-blackout { width: 100%; background: #333; color: #888; margin-top: 15px; padding: 15px; font-size: 12px; }

        .settings-overlay {
            position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.95);
            display: none; z-index: 100; padding: 20px; box-sizing: border-box;
        }
        .settings-content { max-width: 400px; margin: 0 auto; text-align: left; }
        .close-settings { float: right; font-size: 30px; padding: 10px; }
        
        .config-row { display: flex; justify-content: space-between; margin: 20px 0; align-items: center; }
        input[type=number] { width: 60px; padding: 8px; background: #222; color: #fff; border: 1px solid #444; }

        .vj-label { font-size: 10px; color: #555; text-align: left; margin: 15px 0 5px 5px; text-transform: uppercase; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="bpm-display" id="bpm-val">--</div>
        <div class="beat-dot" id="beat-dot"></div>
        <button onclick="toggleSettings()" style="background:none; border:none; color:#444; font-size:24px;">⚙️</button>
    </div>

    <div class="vj-label">Techno / Dark</div>
    <div class="vj-grid">
        <button class="btn btn-techno" onclick="setPreset('techno_red', this)">Red Pulse</button>
        <button class="btn btn-techno" onclick="setPreset('acid_green', this)">Acid Green</button>
        <button class="btn btn-techno" onclick="setPreset('industrial_amber', this)">Amber Breath</button>
        <button class="btn btn-techno" onclick="setPreset('berlin_white', this)">White Kick</button>
    </div>

    <div class="vj-label">House / Shuffle</div>
    <div class="vj-grid">
        <button class="btn btn-house" onclick="setPreset('house_shuffle', this)">House Shuffle</button>
        <button class="btn btn-house" onclick="setPreset('dance_rg', this)">R/G Dance</button>
        <button class="btn btn-house" onclick="setPreset('alternating_kick', this)">Alt Kick</button>
        <button class="btn btn-house" onclick="setPreset('minimal_glitch', this)">Minimal Glitch</button>
    </div>

    <div class="vj-label">Pop / Party</div>
    <div class="vj-grid">
        <button class="btn btn-pop" onclick="setPreset('barbie_party', this)">Barbie Party</button>
        <button class="btn btn-pop" onclick="setPreset('vivid_pop', this)">Rainbow Flow</button>
        <button class="btn btn-pop" onclick="setPreset('sunset_slow', this)">Sunset Slow</button>
        <button class="btn btn-pop" onclick="setPreset('pastel_dream', this)">Pastel Dream</button>
    </div>

    <div class="strobe-area">
        <button class="btn btn-strobe" id="strobe-btn" 
            onmousedown="startStrobe()" onmouseup="stopStrobe()" 
            ontouchstart="startStrobe()" ontouchend="stopStrobe()">STROBE</button>
    </div>

    <button class="btn btn-blackout" onclick="setPreset('blackout', this)">MASTER BLACKOUT</button>

    <div id="settings" class="settings-overlay">
        <div class="close-settings" onclick="toggleSettings()">×</div>
        <div class="settings-content">
            <h2>Settings</h2>
            <div class="config-row">
                <span>Audio Engine Sync</span>
                <input type="checkbox" checked onchange="setAudioReactive(this.checked)" style="width:25px; height:25px;">
            </div>
            <hr style="border:0; border-top:1px solid #333;">
            <div class="config-row"><span>Panel 1 DMX Addr:</span><input type="number" value="10" onchange="updateAddr('panel1', this.value)"></div>
            <div class="config-row"><span>Panel 2 DMX Addr:</span><input type="number" value="20" onchange="updateAddr('panel2', this.value)"></div>
            <div class="config-row"><span>Party Bar DMX Addr:</span><input type="number" value="30" onchange="updateAddr('party_bar', this.value)"></div>
            <p style="font-size:10px; color:#555; margin-top:40px;">LIGHTWEIGHT VJ PRO - Tomorrow Edition</p>
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
                document.getElementById('bpm-val').innerText = Math.round(data.bpm) || '--';
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
    global controller
    controller = lighting_controller
    thread = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=5005, debug=False, use_reloader=False),
        daemon=True
    )
    thread.start()
