#!/usr/bin/python
# (C) 2026 ghzserg https://github.com/ghzserg/zmod

import http.server
import socketserver
import time
import struct
import urllib.parse
import io
import os
import threading
from PIL import Image

PORT = 8010
TOUCH_DEV = '/dev/input/event2'
EVENT_FORMAT = 'LLHHl'

def write_event(f, sec, usec, type_, code, value):
    f.write(struct.pack(EVENT_FORMAT, sec, usec, type_, code, value))

def send_touch_action(action_type, x, y):
    try:
        t = time.time()
        sec = int(t)
        usec = int((t - sec) * 1000000)

        with open(TOUCH_DEV, 'wb') as f:
            if action_type == 'down':
                write_event(f, sec, usec, 1, 330, 1)  # BTN_TOUCH Down
                write_event(f, sec, usec, 3, 53, x)    # ABS_MT_POSITION_X
                write_event(f, sec, usec, 3, 54, y)    # ABS_MT_POSITION_Y
                write_event(f, sec, usec, 3, 48, 18)   # ABS_MT_TOUCH_MAJOR
                write_event(f, sec, usec, 3, 50, 18)   # ABS_MT_TOUCH_MINOR
                write_event(f, sec, usec, 3, 57, 0)    # ABS_MT_TRACKING_ID
                write_event(f, sec, usec, 0, 2, 0)     # SYN_MT_REPORT
                write_event(f, sec, usec, 0, 0, 0)     # SYN_REPORT

            elif action_type == 'move':
                write_event(f, sec, usec, 3, 53, x)    # ABS_MT_POSITION_X
                write_event(f, sec, usec, 3, 54, y)    # ABS_MT_POSITION_Y
                write_event(f, sec, usec, 0, 2, 0)     # SYN_MT_REPORT
                write_event(f, sec, usec, 0, 0, 0)     # SYN_REPORT

            elif action_type == 'up':
                write_event(f, sec, usec, 1, 330, 0)  # BTN_TOUCH Up
                write_event(f, sec, usec, 3, 57, -1)   # Сброс ID трекинга
                write_event(f, sec, usec, 0, 2, 0)     # SYN_MT_REPORT
                write_event(f, sec, usec, 0, 0, 0)     # SYN_REPORT

            f.flush()
    except Exception:
        pass

def emulate_wheel_scroll_safe(direction):
    """
    Эмуляция мощного вертикального свайпа строго в пустой зоне экрана.
    Координаты указаны с учетом системного разворота ROTATE_270.
    """
    x_touch_base = 200
    y_touch_base = 800 - 260 # 540

    send_touch_action('down', x_touch_base, y_touch_base)
    time.sleep(0.02)

    scroll_step = 200 if direction == 1 else -200
    x_touch_new = max(10, min(470, x_touch_base + scroll_step))

    send_touch_action('move', x_touch_new, y_touch_base)
    time.sleep(0.03)

    send_touch_action('up', x_touch_new, y_touch_base)

class StreamHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path in ['/', '/index.html', '/stream']:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    html, body {
                        margin: 0; padding: 0; width: 100%; height: 100%;
                        background: #1e1e24; overflow: hidden;
                        display: flex; justify-content: center; align-items: center;
                    }
                    .container {
                        position: relative; width: 100%; height: 100%;
                        display: flex; justify-content: center; align-items: center;
                    }
                    img {
                        width: 100%; height: 100%; object-fit: contain;
                        cursor: pointer; user-select: none; -webkit-user-drag: none;
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <img id="screen" src="/screen/streams" alt="Screen Stream">
                </div>
                <script>
                    const img = document.getElementById('screen');

                    function getTargetCoords(clientX, clientY) {
                        const rect = img.getBoundingClientRect();
                        const imgRatio = 800 / 480;
                        const containerRatio = rect.width / rect.height;

                        let actualWidth = rect.width;
                        let actualHeight = rect.height;
                        let offsetX = 0;
                        let offsetY = 0;

                        if (containerRatio > imgRatio) {
                            actualWidth = rect.height * imgRatio;
                            offsetX = (rect.width - actualWidth) / 2;
                        } else {
                            actualHeight = rect.width / imgRatio;
                            offsetY = (rect.height - actualHeight) / 2;
                        }

                        const clickX = clientX - rect.left - offsetX;
                        const clickY = clientY - rect.top - offsetY;

                        const x = Math.round(clickX * (800 / actualWidth));
                        const y = Math.round(clickY * (480 / actualHeight));
                        return { x, y };
                    }

                    img.addEventListener('mousedown', (e) => {
                        if (e.button !== 0) return;
                        const coords = getTargetCoords(e.clientX, e.clientY);
                        fetch(`/screen/click?action=down&x=${coords.x}&y=${coords.y}`, { keepalive: true });
                    });

                    img.addEventListener('mouseup', (e) => {
                        if (e.button !== 0) return;
                        const coords = getTargetCoords(e.clientX, e.clientY);
                        fetch(`/screen/click?action=up&x=${coords.x}&y=${coords.y}`, { keepalive: true });
                    });

                    img.addEventListener('wheel', (e) => {
                        e.preventDefault();
                        const dir = e.deltaY > 0 ? -1 : 1;
                        fetch(`/screen/click?action=wheel&dir=${dir}`, { keepalive: true });
                    }, { passive: false });
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return

        # 2. Роутер кликов и безопасного скролла
        elif self.path.startswith('/click'):
            parsed_url = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed_url.query)

            action = params.get('action', ['down'])[0]

            if action == 'wheel':
                direction = int(params.get('dir', ['1'])[0])
                # Вызываем скролл в полностью изолированной от кнопок координатной точке
                threading.Thread(target=emulate_wheel_scroll_safe, args=(direction,)).start()
            else:
                x_web = int(params.get('x', ['0'])[0])
                y_web = int(params.get('y', ['0'])[0])

                # Матричная ротация координат под физический экран принтера
                x_touch = y_web
                y_touch = 800 - x_web
                x_touch = max(0, min(480, x_touch))
                y_touch = max(0, min(800, y_touch))

                send_touch_action(action, x_touch, y_touch)

            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
            return

        # 3. Видеопоток экрана (Стабильный MJPEG)
        elif self.path == '/streams':
            self.send_response(200)
            self.send_header('Content-type', 'multipart/x-mixed-replace; boundary=frame')
            self.end_headers()
            try:
                last_fb = b''
                last_frame = b''

                memory_buffer = io.BytesIO()

                with open('/dev/fb0', 'rb') as fb_file:
                    while True:
                        fb_file.seek(0)
                        fb = fb_file.read()

                        if fb == last_fb and last_frame:
                            frame = last_frame
                        else:
                            img = Image.frombytes('RGBA', (480, 800), fb, 'raw', 'BGRA')
                            img = img.transpose(Image.ROTATE_270).convert('RGB')
                            memory_buffer.seek(0)
                            memory_buffer.truncate(0)

                            img.save(memory_buffer, format='JPEG', quality=60)
                            frame = memory_buffer.getvalue()

                            last_fb = fb
                            last_frame = frame

                        self.wfile.write(b'--frame\r\n')
                        self.send_header('Content-type', 'image/jpeg')
                        self.send_header('Content-length', str(len(frame)))
                        self.end_headers()
                        self.wfile.write(frame)
                        self.wfile.write(b'\r\n')

                        time.sleep(0.2) # ~5 FPS
            except Exception:
                pass
            return

        # 4. Одиночный Snapshot
        elif self.path == '/snapshot':
            self.send_response(200)
            self.send_header('Content-type', 'image/jpeg')
            self.end_headers()
            try:
                fb = open('/dev/fb0', 'rb').read()
                img = Image.frombytes('RGBA', (480, 800), fb, 'raw', 'BGRA').transpose(Image.ROTATE_270).convert('RGB')
                img.save(self.wfile, format='JPEG', quality=90)
            except Exception:
                pass
            return

        else:
            self.send_response(404)
            self.end_headers()

class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == '__main__':
    if not os.access(TOUCH_DEV, os.W_OK):
        os.system(f"chmod 666 {TOUCH_DEV}")

    server = ThreadedHTTPServer(('0.0.0.0', PORT), StreamHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
