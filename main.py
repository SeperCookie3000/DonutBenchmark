import math
import time
import os
import sys
import ctypes
import ctypes.wintypes

# =========================
# НАСТРОЙКИ
# =========================
R1 = 1.0
R2 = 2.5
SPEED_A = 0.05
SPEED_B = 0.025
FPS = 60
CHARS = ' .,-~:;=!*#$@'

COLORS = [
    '\033[38;5;17m',
    '\033[38;5;18m',
    '\033[38;5;27m',
    '\033[38;5;33m',
    '\033[38;5;39m',
    '\033[38;5;51m',
    '\033[38;5;87m',
    '\033[38;5;123m',
    '\033[38;5;159m',
    '\033[38;5;195m',
    '\033[38;5;231m',
    '\033[38;5;255m',
]
RESET = '\033[0m'

COLORS_B  = [c.encode() for c in COLORS]
RESET_B   = RESET.encode()
SPACE_B   = b' '
NEWLINE_B = b'\n'
HOME_B    = b'\033[H'
# =========================

def enable_ansi():
    if sys.platform.startswith('win'):
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)

def set_title(title: str):
    if sys.platform.startswith('win'):
        ctypes.windll.kernel32.SetConsoleTitleW(title)

def hide_cursor():
    sys.stdout.buffer.write(b'\033[?25l')
    sys.stdout.buffer.flush()

def show_cursor():
    sys.stdout.buffer.write(b'\033[?25h')
    sys.stdout.buffer.flush()

def clear_screen():
    sys.stdout.buffer.write(b'\033[2J\033[H')
    sys.stdout.buffer.flush()

def get_size():
    try:
        size = os.get_terminal_size()
        w = max(size.columns - 1, 20)
        h = max(size.lines - 1, 10)
        return w, h
    except:
        return 80, 24

def compute_constants(W, H):
    K2 = 10.0
    K1 = W * K2 * 3 / (8 * (R1 + R2))
    return K1, K2

def clear_scrollback():
    """Очищает весь буфер прокрутки консоли Windows"""
    if sys.platform.startswith('win'):
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)

        coord_zero = ctypes.wintypes.DWORD(0)
        size       = ctypes.wintypes.DWORD(9999 * 300)
        written    = ctypes.wintypes.DWORD(0)

        kernel32.FillConsoleOutputCharacterW(
            handle,
            ctypes.c_wchar(' '),
            size,
            coord_zero,
            ctypes.byref(written)
        )
        kernel32.FillConsoleOutputAttribute(
            handle,
            ctypes.wintypes.WORD(7),
            size,
            coord_zero,
            ctypes.byref(written)
        )
        kernel32.SetConsoleCursorPosition(handle, coord_zero)


def render_frame(A, B, buf, fps, avg_fps, frame_count):
    W, H = get_size()
    K1, K2 = compute_constants(W, H)

    N = W * H
    output  = [0]     * N
    color   = [0]     * N
    filled  = [False] * N
    zbuffer = [0.0]   * N

    cA, sA = math.cos(A), math.sin(A)
    cB, sB = math.cos(B), math.sin(B)

    theta_step = max(0.02, 0.07 - W * 0.0002)
    phi_step   = max(0.01, 0.04 - W * 0.0001)

    theta = 0.0
    while theta < 6.28318:
        ct, st = math.cos(theta), math.sin(theta)
        phi = 0.0
        while phi < 6.28318:
            cp, sp = math.cos(phi), math.sin(phi)

            circleX = R2 + R1 * ct
            circleY = R1 * st

            x   = circleX * (cB * cp + sA * sB * sp) - circleY * cA * sB
            y   = circleX * (sB * cp - sA * cB * sp) + circleY * cA * cB
            z   = K2 + cA * circleX * sp + circleY * sA
            ooz = 1.0 / z

            xp = int(W / 2 + K1 * ooz * x)
            yp = int(H / 2 - K1 * ooz * y * 0.5)

            L = (cp * ct * cB
                 - cA * ct * sp
                 - sA * st
                 + cB * (cA * st - ct * sA * sp))

            if 0 <= xp < W and 0 <= yp < H:
                idx = xp + W * yp
                if ooz > zbuffer[idx]:
                    zbuffer[idx] = ooz
                    li = max(0, min(int(L * 8), len(CHARS) - 1))
                    output[idx]  = li
                    color[idx]   = max(0, min(int(L * 8), len(COLORS) - 1))
                    filled[idx]  = True

            phi += phi_step
        theta += theta_step

    if fps >= 50:
        fps_color = b'\033[38;5;46m'
        rating    = 'EXCELLENT'
    elif fps >= 30:
        fps_color = b'\033[38;5;226m'
        rating    = 'GOOD     '
    elif fps >= 15:
        fps_color = b'\033[38;5;208m'
        rating    = 'POOR     '
    else:
        fps_color = b'\033[38;5;196m'
        rating    = 'BAD      '

    status = (
        f"  DONUT BENCHMARK  |  "
        f"FPS: {fps:5.1f}  |  "
        f"AVG: {avg_fps:5.1f}  |  "
        f"SCORE: {rating}  |  "
        f"FRAMES: {frame_count:06d}  |  "
        f"Ctrl+C = exit"
    )

    set_title(f"Donut Benchmark | FPS: {fps:.1f} | AVG: {avg_fps:.1f} | {rating.strip()}")

    buf.clear()
    buf += HOME_B

    for j in range(H):
        cur_color = -1
        base = j * W

        if j == H - 1:
            buf += RESET_B
            buf += fps_color
            line = status[:W].ljust(W)
            buf += line.encode()
            buf += RESET_B
            break

        for i in range(W):
            idx = base + i
            if not filled[idx]:
                if cur_color != -1:
                    buf += RESET_B
                    cur_color = -1
                buf += SPACE_B
            else:
                ci = color[idx]
                if ci != cur_color:
                    buf += COLORS_B[ci]
                    cur_color = ci
                buf += CHARS[output[idx]].encode()
        if cur_color != -1:
            buf += RESET_B
        buf += NEWLINE_B

    sys.stdout.buffer.write(buf)
    sys.stdout.buffer.flush()


def show_results(frame_count, avg_fps):
    sys.stdout.buffer.flush()
    sys.stdout.flush()

    # Очищаем скроллбэк и экран
    clear_scrollback()
    sys.stdout.buffer.write(b'\033[2J\033[H')
    sys.stdout.buffer.flush()

    show_cursor()
    set_title("Donut Benchmark - Results")

    if avg_fps >= 50:
        rating = 'EXCELLENT'
        color  = '\033[38;5;46m'
    elif avg_fps >= 30:
        rating = 'GOOD'
        color  = '\033[38;5;226m'
    elif avg_fps >= 15:
        rating = 'POOR'
        color  = '\033[38;5;208m'
    else:
        rating = 'BAD'
        color  = '\033[38;5;196m'

    W, _ = get_size()
    line = '=' * W

    out = []
    out.append(RESET + '\n')
    out.append(line + '\n')
    out.append('\n')
    out.append('  DONUT BENCHMARK - RESULTS\n')
    out.append('\n')
    out.append(line + '\n')
    out.append('\n')
    out.append(f'  Total frames  : {frame_count}\n')
    out.append(f'  Average FPS   : {avg_fps:.1f}\n')
    out.append(f'  Score         : {color}{rating}{RESET}\n')
    out.append('\n')
    out.append(line + '\n')
    out.append('\n')

    if avg_fps >= 50:
        out.append('  Your CPU handles this benchmark with ease.\n')
    elif avg_fps >= 30:
        out.append('  Your CPU performs adequately.\n')
    elif avg_fps >= 15:
        out.append('  Your CPU is struggling with this benchmark.\n')
    else:
        out.append('  Your CPU is very slow for this benchmark.\n')

    out.append('\n')
    out.append(line + '\n')
    out.append('\n')
    out.append('  Press ENTER to exit...\n')

    sys.stdout.buffer.write(''.join(out).encode('utf-8'))
    sys.stdout.buffer.flush()

    input()


def main():
    if sys.platform.startswith('win'):
        os.system('chcp 65001 >nul 2>&1')
        enable_ansi()

    hide_cursor()
    clear_screen()
    set_title("Donut Benchmark")

    A = 0.0
    B = 0.0
    frame_time  = 1.0 / FPS
    buf         = bytearray()

    W, H        = get_size()
    prev_size   = (W, H)

    fps         = 0.0
    avg_fps     = 0.0
    frame_count = 0
    fps_acc     = 0.0

    try:
        while True:
            t0 = time.perf_counter()

            W, H = get_size()
            if (W, H) != prev_size:
                clear_screen()
                prev_size = (W, H)

            render_frame(A, B, buf, fps, avg_fps, frame_count)

            A += SPEED_A
            B += SPEED_B
            frame_count += 1

            elapsed = time.perf_counter() - t0

            if elapsed > 0:
                fps = 1.0 / elapsed
            else:
                fps = 999.0

            fps_acc += fps
            if frame_count % 60 == 0:
                avg_fps = fps_acc / 60.0
                fps_acc = 0.0

            wait = frame_time - elapsed
            if wait > 0:
                time.sleep(wait)

    except KeyboardInterrupt:
        show_results(frame_count, avg_fps)


if __name__ == "__main__":
    main()