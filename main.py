import http.server
import socketserver
import socket
import json
import threading
import urllib.parse
import pathlib
import mimetypes
from datetime import datetime
from time import sleep


HOST = '127.0.0.1'
PORT = 5000
PORT_HTTP = 3000
GLOBAL_BUFFER = {}


def simple_client(host, port, data):
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        server = host, port
        while True:
            try:
                client.connect((host, port))
                client.sendall(data.encode())
                # print(f'Send data: {data}')
                break
            except ConnectionRefusedError:
                sleep(0.5)

# Ваш код обробки HTTP запитів
class CustomHandler(http.server.SimpleHTTPRequestHandler):

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        # print(data) #1
        data_parse = urllib.parse.unquote_plus(data.decode())
        # print(data_parse)#2
        data_dict = {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}
        # print(data_dict)#3
        json_object = json.dumps(data_dict)
        GLOBAL_BUFFER = json_object #"test msg"#
        #socket communication
        # print('socket start sending!')
        client_thread = threading.Thread(target=simple_client, args=(HOST, PORT, GLOBAL_BUFFER))
        client_thread.start()
        # print('Done!')
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html_file('index.html')
        elif pr_url.path == '/contact':
            self.send_html_file('contact.html')
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
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

# HTTP server
def start_http_server():
    
    handler = CustomHandler
    with socketserver.TCPServer((HOST, PORT_HTTP), handler) as httpd:
        print(f"HTTP server started at port {PORT_HTTP}")
        httpd.serve_forever()


#socket server
def handle_socket_data():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.bind((HOST, PORT))
        print(f"Socket server started at port {PORT}")

        while True:
            data, address = server_socket.recvfrom(1024)
            try:
                # print(f"In server {data}")
                decoded_data = json.loads(data.decode())
                # print(f"Decoded data {decoded_data}")
                with open('storage/data.json', 'r') as file:
                    existing_data = json.load(file)
                # print(existing_data)
                existing_data[str(datetime.now())] = decoded_data

                with open('storage/data.json', 'w') as file:
                    json.dump(existing_data, file, indent=4)

            except json.JSONDecodeError:
                print("Error decoding JSON data")


if __name__ == "__main__":

    http_thread = threading.Thread(target=start_http_server)
    http_thread.daemon = True
    http_thread.start()

    socket_thread = threading.Thread(target=handle_socket_data)
    socket_thread.daemon = True
    socket_thread.start()

    while True:
        pass