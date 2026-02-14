#!/usr/bin/env python3
"""
Test suite for DMX Controller
"""

import time
import logging
from dmx_controller import DMXController


def test_basic_functionality():
    print("=== Testing Basic Functionality ===")

    try:
        dmx = DMXController()
        print(f"✓ DMX Controller created, detected port: {dmx.port_name}")

        if not dmx.start():
            print("✗ Failed to start DMX controller")
            return False

        print("✓ DMX controller started")

        dmx.set_channel(1, 128)
        assert dmx.get_channel(1) == 128
        print("✓ Single channel set/get works")

        test_channels = {1: 255, 2: 128, 3: 64}
        dmx.set_channels(test_channels)

        for channel, expected_value in test_channels.items():
            assert dmx.get_channel(channel) == expected_value
        print("✓ Multiple channels set/get works")

        dmx.blackout()
        for i in range(1, 10):
            assert dmx.get_channel(i) == 0
        print("✓ Blackout works")

        dmx.set_all_channels(100)
        for i in range(1, 10):
            assert dmx.get_channel(i) == 100
        print("✓ Set all channels works")

        dmx.disconnect()
        print("✓ DMX controller stopped")

        return True

    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def test_boundary_conditions():
    print("\n=== Testing Boundary Conditions ===")

    try:
        dmx = DMXController()

        try:
            dmx.set_channel(0, 128)
            print("✗ Should have failed for channel 0")
            return False
        except ValueError:
            print("✓ Correctly rejected channel 0")

        try:
            dmx.set_channel(513, 128)
            print("✗ Should have failed for channel 513")
            return False
        except ValueError:
            print("✓ Correctly rejected channel 513")

        try:
            dmx.set_channel(1, -1)
            print("✗ Should have failed for value -1")
            return False
        except ValueError:
            print("✓ Correctly rejected negative value")

        try:
            dmx.set_channel(1, 256)
            print("✗ Should have failed for value 256")
            return False
        except ValueError:
            print("✓ Correctly rejected value > 255")

        dmx.set_channel(1, 0)
        assert dmx.get_channel(1) == 0
        print("✓ Channel value 0 works")

        dmx.set_channel(512, 255)
        assert dmx.get_channel(512) == 255
        print("✓ Channel 512 value 255 works")

        return True

    except Exception as e:
        print(f"✗ Boundary test failed: {e}")
        return False


def test_threading_stability():
    print("\n=== Testing Threading Stability ===")

    try:
        dmx = DMXController()

        if not dmx.start():
            print("✗ Failed to start DMX controller")
            return False

        print("DMX output running, testing for 5 seconds...")

        start_time = time.time()
        test_duration = 5.0

        while time.time() - start_time < test_duration:
            for i in range(1, 11):
                value = int((time.time() * 100) % 256)
                dmx.set_channel(i, value)

            time.sleep(0.01)

        print(f"✓ Threading stable for {test_duration} seconds")

        dmx.disconnect()
        return True

    except Exception as e:
        print(f"✗ Threading test failed: {e}")
        return False


def test_performance():
    print("\n=== Testing Performance ===")

    try:
        dmx = DMXController()

        if not dmx.start():
            print("✗ Failed to start DMX controller")
            return False

        start_time = time.time()
        iterations = 1000

        for i in range(iterations):
            dmx.set_channel(1, i % 256)

        elapsed = time.time() - start_time
        updates_per_second = iterations / elapsed

        print(f"✓ Channel updates: {updates_per_second:.0f} ops/sec")

        test_data = {i: (i * 37) % 256 for i in range(1, 513)}

        start_time = time.time()
        bulk_iterations = 100

        for _ in range(bulk_iterations):
            dmx.set_channels(test_data)

        elapsed = time.time() - start_time
        bulk_updates_per_second = bulk_iterations / elapsed

        print(f"✓ Bulk updates (512 channels): {bulk_updates_per_second:.1f} ops/sec")

        dmx.disconnect()
        return True

    except Exception as e:
        print(f"✗ Performance test failed: {e}")
        return False


def run_visual_test():
    print("\n=== Running Visual Test ===")
    print("This test will run a light sequence if you have DMX lights connected.")
    print("Press Ctrl+C to stop at any time.")

    try:
        dmx = DMXController()

        if not dmx.start():
            print("✗ Failed to start DMX controller")
            return False

        print("\n1. Testing individual channels (1-8)...")
        for channel in range(1, 9):
            print(f"   Channel {channel} on")
            dmx.set_channel(channel, 255)
            time.sleep(0.5)
            dmx.set_channel(channel, 0)
            time.sleep(0.1)

        print("\n2. Fade test on first 4 channels...")
        for brightness in range(0, 256, 5):
            dmx.set_channels(
                {1: brightness, 2: brightness, 3: brightness, 4: brightness}
            )
            time.sleep(0.02)

        for brightness in range(255, -1, -5):
            dmx.set_channels(
                {1: brightness, 2: brightness, 3: brightness, 4: brightness}
            )
            time.sleep(0.02)

        print("\n3. Chase pattern...")
        for _ in range(3):
            for i in range(1, 9):
                dmx.blackout()
                dmx.set_channel(i, 255)
                time.sleep(0.2)

        print("\n4. Final blackout...")
        dmx.blackout()
        time.sleep(1)

        dmx.disconnect()
        print("✓ Visual test completed")
        return True

    except KeyboardInterrupt:
        dmx.disconnect()
        print("\n✓ Visual test interrupted by user")
        return True
    except Exception as e:
        print(f"✗ Visual test failed: {e}")
        return False

        print("\n1. Testing individual channels (1-8)...")
        for channel in range(1, 9):
            print(f"   Channel {channel} on")
            dmx.set_channel(channel, 255)
            time.sleep(0.5)
            dmx.set_channel(channel, 0)
            time.sleep(0.1)

        print("\n2. Fade test on first 4 channels...")
        for brightness in range(0, 256, 5):
            dmx.set_channels(
                {1: brightness, 2: brightness, 3: brightness, 4: brightness}
            )
            time.sleep(0.02)

        for brightness in range(255, -1, -5):
            dmx.set_channels(
                {1: brightness, 2: brightness, 3: brightness, 4: brightness}
            )
            time.sleep(0.02)

        print("\n3. Chase pattern...")
        for _ in range(3):
            for i in range(1, 9):
                dmx.blackout()
                dmx.set_channel(i, 255)
                time.sleep(0.2)

        print("\n4. Final blackout...")
        dmx.blackout()
        time.sleep(1)

        dmx.disconnect()
        print("✓ Visual test completed")
        return True

    except KeyboardInterrupt:
        dmx.disconnect()
        print("\n✓ Visual test interrupted by user")
        return True
    except Exception as e:
        print(f"✗ Visual test failed: {e}")
        return False


def main():
    logging.basicConfig(level=logging.WARNING)

    print("DMX Controller Test Suite")
    print("=" * 40)

    tests = [
        test_basic_functionality,
        test_boundary_conditions,
        test_threading_stability,
        test_performance,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        else:
            print(f"Test {test.__name__} failed!")

    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("✓ All tests passed!")

        try:
            response = (
                input("\nRun visual test with connected lights? (y/N): ")
                .strip()
                .lower()
            )
            if response == "y":
                run_visual_test()
        except KeyboardInterrupt:
            print("\nExiting...")
    else:
        print("✗ Some tests failed!")
        return False

    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
