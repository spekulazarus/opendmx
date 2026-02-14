import serial
import time
import threading

class DMXSender:
    def __init__(self, port="/dev/cu.usbserial-BG03LVHM", baudrate=250000):
        self.port = port
        self.baudrate = baudrate
        # Optimization: Only send 64 channels to reduce load on wireless transmitter
        self.num_channels = 64 
        self.dmx_data = bytearray([0] * self.num_channels)
        self.running = False
        self.thread = None
        self.ser = None

    def start(self):
        try:
            self.ser = serial.Serial(
                self.port, 
                baudrate=self.baudrate, 
                stopbits=serial.STOPBITS_TWO, 
                bytesize=serial.EIGHTBITS,
                timeout=0
            )
            print(f"DMXSender started on {self.port} (Turbo Mode: {self.num_channels} Channels)")
        except Exception as e:
            print(f"Warning: Entering Virtual Mode ({e})")
            self.ser = None
        
        self.running = True
        self.thread = threading.Thread(target=self._send_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread: self.thread.join()
        if self.ser: self.ser.close()

    def set_channel(self, channel, value):
        # Only set if channel is within our reduced range
        if 1 <= channel <= self.num_channels:
            self.dmx_data[channel - 1] = max(0, min(255, int(value)))

    def _send_loop(self):
        while self.running:
            try:
                if self.ser:
                    # 1. DROP BAUD RATE FOR BREAK (Most stable on macOS for OpenDMX)
                    self.ser.baudrate = 9600
                    self.ser.write(b'\x00')
                    
                    # 2. RESTORE DMX BAUD RATE
                    self.ser.baudrate = 250000
                    
                    # 3. DATA (Reduced Universe)
                    self.ser.write(bytearray([0x00]) + self.dmx_data)
                    
                    # 4. STABILIZE FRAME (Approx 35Hz)
                    # Reduced universe takes much less time to write
                    time.sleep(0.025) 
                else:
                    time.sleep(0.05)
            except Exception as e:
                print(f"DMX Error: {e}")
                time.sleep(1)
