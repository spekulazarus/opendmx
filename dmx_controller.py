#!/usr/bin/env python3
"""
Open DMX Controller for FTDI-based devices on macOS
Implements DMX512 protocol with proper Break/MAB timing using pyserial
"""

import serial
import serial.tools.list_ports
import threading
import time
import logging
from typing import Optional, List, Union


class DMXController:
    """
    DMX512 controller for FTDI-based Open DMX interfaces.

    Features:
    - Proper Break signal generation (88μs minimum)
    - Mark After Break (MAB) timing (8μs minimum)
    - 30-40Hz output rate in separate thread
    - 513 bytes: Start code (0x00) + 512 DMX channels
    - Serial config: 250,000 baud, 8N2
    """

    # DMX Protocol Constants
    DMX_BAUD_RATE = 250000
    DMX_BREAK_TIME = 0.000176  # 176μs (>88μs minimum) for better compatibility
    DMX_MAB_TIME = 0.000016  # 16μs (>8μs minimum)
    DMX_FRAME_RATE = 30  # Hz - conservative rate to avoid flickering
    DMX_UNIVERSE_SIZE = 512  # Standard DMX universe size

    # FTDI Device Detection
    FTDI_VID = 0x0403  # FTDI Vendor ID
    FTDI_PIDS = [0x6001, 0x6010, 0x6011, 0x6014, 0x6015]  # Common FTDI PIDs

    def __init__(self, port: Optional[str] = None, auto_detect: bool = True):
        """
        Initialize DMX controller.

        Args:
            port: Serial port path (e.g., '/dev/cu.usbserial-A1234567')
            auto_detect: Automatically detect FTDI devices if port not specified
        """
        self.logger = self._setup_logging()

        # DMX data buffer: [start_code, channel1, channel2, ..., channel512]
        self.dmx_data = bytearray([0] * (self.DMX_UNIVERSE_SIZE + 1))

        # Threading control
        self._running = False
        self._thread = None
        self._data_lock = threading.Lock()

        # Serial connection
        self.serial_port = None
        self.port_name = None

        # Initialize port
        if port:
            self.port_name = port
        elif auto_detect:
            self.port_name = self._auto_detect_ftdi()

        if not self.port_name:
            raise ValueError("No DMX interface found. Please specify port manually.")

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the DMX controller."""
        logger = logging.getLogger("DMXController")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def _auto_detect_ftdi(self) -> Optional[str]:
        """
        Auto-detect FTDI devices on macOS.

        Returns:
            Port path if found, None otherwise
        """
        self.logger.info("Scanning for FTDI devices...")

        ports = serial.tools.list_ports.comports()
        ftdi_ports = []

        for port in ports:
            # Check for FTDI vendor ID and common product IDs
            if port.vid == self.FTDI_VID and port.pid in self.FTDI_PIDS:
                ftdi_ports.append(port)
                self.logger.info(
                    f"Found FTDI device: {port.device} ({port.description})"
                )

            # Also check for common macOS FTDI device paths
            elif "/dev/cu.usbserial" in port.device:
                ftdi_ports.append(port)
                self.logger.info(f"Found potential FTDI device: {port.device}")

        if not ftdi_ports:
            self.logger.error("No FTDI devices found")
            return None

        if len(ftdi_ports) > 1:
            self.logger.warning(
                f"Multiple FTDI devices found, using first: {ftdi_ports[0].device}"
            )

        return ftdi_ports[0].device

    def connect(self) -> bool:
        """
        Connect to the DMX interface.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.logger.info(f"Connecting to DMX interface: {self.port_name}")

            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.DMX_BAUD_RATE,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_TWO,  # 8N2 configuration
                timeout=1.0,
                xonoff=False,
                rtscts=False,
                dsrdtr=False,
            )

            # Verify connection
            if not self.serial_port.is_open:
                self.logger.error("Failed to open serial port")
                return False

            self.logger.info("DMX interface connected successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to connect to DMX interface: {e}")
            return False

    def disconnect(self):
        """Disconnect from the DMX interface."""
        self.stop()

        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
            self.logger.info("DMX interface disconnected")

    def start(self) -> bool:
        """
        Start the DMX output thread.

        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            self.logger.warning("DMX output already running")
            return True

        if not self.serial_port or not self.serial_port.is_open:
            if not self.connect():
                return False

        self._running = True
        self._thread = threading.Thread(target=self._dmx_thread, daemon=True)
        self._thread.start()

        self.logger.info(f"DMX output started at {self.DMX_FRAME_RATE}Hz")
        return True

    def stop(self):
        """Stop the DMX output thread."""
        if self._running:
            self._running = False
            if self._thread:
                self._thread.join(timeout=2.0)
            self.logger.info("DMX output stopped")

    def _dmx_thread(self):
        """
        Main DMX output thread.

        Continuously sends DMX frames at the specified rate with proper timing:
        1. Break signal (176μs)
        2. Mark After Break (16μs)
        3. 513 data bytes (start code + 512 channels)
        """
        frame_interval = 1.0 / self.DMX_FRAME_RATE

        self.logger.info("DMX thread started")

        while self._running:
            frame_start = time.time()

            try:
                self._send_dmx_frame()
            except Exception as e:
                self.logger.error(f"Error sending DMX frame: {e}")
                time.sleep(0.1)  # Brief pause before retry
                continue

            # Maintain consistent frame rate
            elapsed = time.time() - frame_start
            sleep_time = frame_interval - elapsed

            if sleep_time > 0:
                time.sleep(sleep_time)
            elif sleep_time < -0.001:  # Warn if significantly behind
                self.logger.warning(
                    f"DMX frame took {elapsed * 1000:.1f}ms (target: {frame_interval * 1000:.1f}ms)"
                )

        self.logger.info("DMX thread stopped")

    def _send_dmx_frame(self):
        """
        Send a complete DMX frame with proper timing.

        Frame structure:
        1. Break condition (176μs)
        2. Mark After Break (16μs)
        3. Start code (0x00)
        4. 512 channel bytes
        """
        if not self.serial_port or not self.serial_port.is_open:
            raise RuntimeError("Serial port not open")

        # Step 1: Generate Break signal
        # Set break condition (line LOW)
        self.serial_port.break_condition = True
        time.sleep(self.DMX_BREAK_TIME)

        # Step 2: Mark After Break
        # Clear break condition (line HIGH)
        self.serial_port.break_condition = False
        time.sleep(self.DMX_MAB_TIME)

        # Step 3: Send data frame
        # Acquire lock and copy current DMX data
        with self._data_lock:
            data_to_send = bytes(self.dmx_data)

        # Send the complete frame
        self.serial_port.write(data_to_send)
        self.serial_port.flush()  # Ensure data is transmitted

    def set_channel(self, channel: int, value: int):
        """
        Set a single DMX channel value.

        Args:
            channel: DMX channel number (1-512)
            value: Channel value (0-255)
        """
        if not 1 <= channel <= self.DMX_UNIVERSE_SIZE:
            raise ValueError(f"Channel must be between 1 and {self.DMX_UNIVERSE_SIZE}")

        if not 0 <= value <= 255:
            raise ValueError("Value must be between 0 and 255")

        with self._data_lock:
            self.dmx_data[channel] = value  # channel index offset by start code

    def set_channels(self, channels: dict):
        """
        Set multiple DMX channel values.

        Args:
            channels: Dictionary of {channel: value} pairs
        """
        with self._data_lock:
            for channel, value in channels.items():
                if not 1 <= channel <= self.DMX_UNIVERSE_SIZE:
                    raise ValueError(
                        f"Channel {channel} must be between 1 and {self.DMX_UNIVERSE_SIZE}"
                    )

                if not 0 <= value <= 255:
                    raise ValueError(
                        f"Value {value} for channel {channel} must be between 0 and 255"
                    )

                self.dmx_data[channel] = value

    def get_channel(self, channel: int) -> int:
        """
        Get current value of a DMX channel.

        Args:
            channel: DMX channel number (1-512)

        Returns:
            Current channel value (0-255)
        """
        if not 1 <= channel <= self.DMX_UNIVERSE_SIZE:
            raise ValueError(f"Channel must be between 1 and {self.DMX_UNIVERSE_SIZE}")

        with self._data_lock:
            return self.dmx_data[channel]

    def blackout(self):
        """Set all DMX channels to 0 (blackout)."""
        with self._data_lock:
            # Keep start code at 0, set all channels to 0
            for i in range(1, len(self.dmx_data)):
                self.dmx_data[i] = 0

        self.logger.info("Blackout applied")

    def set_all_channels(self, value: int):
        """
        Set all DMX channels to the same value.

        Args:
            value: Value to set all channels to (0-255)
        """
        if not 0 <= value <= 255:
            raise ValueError("Value must be between 0 and 255")

        with self._data_lock:
            # Keep start code at 0, set all channels to value
            for i in range(1, len(self.dmx_data)):
                self.dmx_data[i] = value

        self.logger.info(f"All channels set to {value}")

    def get_universe_data(self) -> List[int]:
        """
        Get current state of entire DMX universe.

        Returns:
            List of 512 channel values (excluding start code)
        """
        with self._data_lock:
            return list(self.dmx_data[1:])  # Exclude start code

    def is_running(self) -> bool:
        """Check if DMX output is currently running."""
        return self._running

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()


# Example usage and testing functions
def main():
    """Example usage of the DMX controller."""
    logging.basicConfig(level=logging.INFO)

    try:
        # Create DMX controller (auto-detect FTDI device)
        dmx = DMXController()

        # Connect and start DMX output
        if not dmx.start():
            print("Failed to start DMX controller")
            return

        print("DMX Controller started. Running test sequence...")
        print("Press Ctrl+C to stop")

        try:
            # Test sequence
            while True:
                # Fade channels 1-3 up and down
                for brightness in range(0, 256, 5):
                    dmx.set_channels({1: brightness, 2: brightness, 3: brightness})
                    time.sleep(0.05)

                for brightness in range(255, -1, -5):
                    dmx.set_channels({1: brightness, 2: brightness, 3: brightness})
                    time.sleep(0.05)

        except KeyboardInterrupt:
            print("\nStopping DMX controller...")

    except Exception as e:
        print(f"Error: {e}")

    finally:
        dmx.disconnect()
        print("DMX controller stopped")


if __name__ == "__main__":
    main()
