"""Shared timeline for the ESP32 + OLED (I2C) short (24 fps, 384 frames = 16 s)."""
FPS, N = 24, 384
#        hook  board  wires  scan  packet demo  end
SHOTS = [0, 48, 96, 150, 210, 270, 324]
BOOT = 6                  # OLED wakes up in the hook
SCAN = (156, 186)         # address scan 0x00..0x7F, stops at 0x3C
FOUND = 186
PACKET = ["START", "ADDR", "ACK", "DATA", "STOP"]
PKT0, PKT_STEP = 216, 10  # packet field i is highlighted from PKT0 + i*PKT_STEP
ADDR = 0x3C


def ease(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def busy(f):
    """True while data is moving on the bus (pulses on SDA/SCL)."""
    return BOOT <= f < 40 or 96 <= f < 150 or SCAN[0] <= f < FOUND + 6 or PKT0 <= f < PKT0 + 5 * PKT_STEP + 4 or 276 <= f < 324


def scan_addr(f):
    if f < SCAN[0]:
        return 0
    u = ease((f - SCAN[0]) / (SCAN[1] - SCAN[0]))
    return min(ADDR, int(u * ADDR))


def packet_step(f):
    return max(-1, min(len(PACKET) - 1, (f - PKT0) // PKT_STEP)) if f >= PKT0 else -1
