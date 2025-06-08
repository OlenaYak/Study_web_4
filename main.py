import urllib.parse
import mimetypes
import pathlib
import threading
import socket
import json
import datetime
from time import sleep
from http.server import HTTPServer, BaseHTTPRequestHandler


HOST = '127.0.0.1'
PORT = 5000

# Створення каталогу та файлу, якщо їх немає
storage_dir = pathlib.Path('storage')
storage_dir.mkdir(exist_ok=True)

data_file = storage_dir / 'data.json'
if not data_file.exists():
    with open(data_file, 'w', encoding='utf-8') as f:
        json.dump({}, f)

class HttpHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/message':
            self.send_html_file('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        file_path = pathlib.Path().joinpath(self.path[1:]) 
        if file_path.exists():
            with open(file_path, 'rb') as file:
                self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        data_parse = urllib.parse.unquote_plus(data.decode())
        print(data_parse)
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        print(data_dict)
                
        try: # Відправлення даних на UDP сервер
            udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            msg_json = json.dumps(data_dict)
            udp_sock.sendto(msg_json.encode('utf-8'), (HOST, PORT))
            udp_sock.close()
        except Exception as e:
            print("Не вдалося надіслати UDP:", e)

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

def udp_server(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    print(f"UDP сервер працює на {host}:{port}")

    while True:
        data, _ = sock.recvfrom(1024)
        if data:
            try:
                decoded = data.decode('utf-8')
                msg = json.loads(decoded)
                now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
                
                # Створюємо/оновлюємо JSON-файл
                pathlib.Path('storage').mkdir(exist_ok=True)
                file_path = pathlib.Path('storage/data.json')

                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        all_data = json.load(f)
                else:
                    all_data = {}

                all_data[now] = msg

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(all_data, f, ensure_ascii=False, indent=2)
                    
                print(f"[{now}]Збережено повідомлення від {msg['username']}")
            except Exception as e:
                print("Помилка обробки:", e)


server = threading.Thread(target=udp_server, args=(HOST, PORT))
server.start()


def run(server_class=HTTPServer, handler_class=HttpHandler):
    server_address = ('0.0.0.0', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()




if __name__ == '__main__':
    http_server = threading.Thread(target=run)
    http_server.start()
    http_server.join()

