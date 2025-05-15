import socket
import threading
import re
import traceback
import select
import os
import uuid
import json

HOST = ''  # Symbolic name meaning all available interfaces
PORT = 8642  # Arbitrary non-privileged port

SERVER_HOST_IP = 'eagle.cs.umanitoba.ca'
SERVER_HOST_PORT = 8641

FILE_PATH_DIC = {
    'loginscript.js': 'website/login/loginscript.js',
    'loginstyle.css': 'website/login/loginstyle.css',
    'homepage.html': 'website/homepage/homepage.html',
    'homepage.css': 'website/homepage/homepage.css',
    'homepage.js': 'website/homepage/homepage.js',
    'chatbot.ico': 'chatbot.ico',
    'favicon.ico': 'chatbot.ico',
    'loginpage.html': 'website/login/loginpage.html'
}

# session -> [username, first_time, last_scene]
CACHE_DIC = {
    "test-id": ['bot', False, 1731065196]
}

VALID_PATH = ('/api/messages', '/api/login')

post_header_template = """HTTP/1.1 201 Created
Content-Type: text/{}
Connection: close
Content-Length: {}

"""

login_lo_header = """HTTP/1.1 200 OK
Content-Type: text/html
Content-Length: {}
Set-Cookie: session_id={}; HttpOnly
Connection: close

"""

http_error = """HTTP/1.1 {}
Content-Type: text/html
Connection: close
Content-Length: 0

"""

http_get_request = """HTTP/1.1 200 OK
Content-Type: {}
Connection: close
Content-Length: {}

"""

http_get_request = """HTTP/1.1 200 OK
Content-Type: {}
Connection: close
Content-Length: {}

"""

def read_file(file_path, read_mode):
    with open(file_path, read_mode) as f:
        return f.read()
    
def parse_http_req(raw_request):
    if 'GET' not in raw_request:
        print(raw_request)
    pattern = r'(\w+)\s+([^\s]+)\s+HTTP/(\d\.\d)'
    match = re.match(pattern, raw_request)
    
    if match:
        method, path_with_query, _ = match.groups()
        
        path, query_string = (path_with_query.split('?', 1) + [''])[:2]
        
        # Parse query parameters
        query_params = dict(re.findall(r'([^&=]+)=([^&]*)', query_string))
        
        body_dic = {}
        content_len = 0
        cookies_dir = {}
        # if method == 'POST':
        req_split = raw_request.split('\n')
        read_body = False
        
        for s in req_split:
            if read_body and content_len != 0:
                body_dic = json.loads(s)
            elif 'Cookie' in s:
                cookie_line = s.split(':')
                cookie_value = cookie_line[1].split(';')
                for c in cookie_value:
                    cookie_key_value = c.split('=')
                    cookies_dir[cookie_key_value[0].strip()] = cookie_key_value[1].strip()
                    
            elif 'Content-Length' in s:
                content_len = int(s.split(':')[1].strip())
            elif s == '\r':
                read_body = True
        # else:
            # content_len = 0
            # body_dic['msg'] = ''
        
        return method, path, query_params, cookies_dir, content_len, body_dic

def handle_all_message(server, session_id, time, all_message):
    response = ''
    try:
        if all_message:    
            server.sendall(f'[msg:{CACHE_DIC[session_id][0]}:{CACHE_DIC[session_id][1]}:{CACHE_DIC[session_id][2]}]'.encode())
        else:
            server.sendall(f'[msgt:{CACHE_DIC[session_id][0]}:{time}]'.encode())
            
        body_recv = server.recv(1024)
        body = body_recv
        while len(body_recv) >= 1024:
            body_recv = server.recv(1024)
            body += body_recv
        
        if body == 'chat-server-500-error':
            raise Exception('Internal Server Error - 500')
        else:
            response = http_get_request.format('application/json', len(body))
            response += body.decode('utf-8')
    except:
        traceback.print_exc()
        response = http_error.format(500)
        
    # msg_arr = json.loads(data)
    return response

def handle_api_get_req(server, path, query_parms, session_id):
    
    response = ''
    
    try:
        
        if authenticate_user(session_id):
            if 'time' in query_parms:
                # code to get messages from server and return it
                # print('work in progress')
                response = handle_all_message(server, session_id, int(query_parms['time']), False)
                # response = http_get_request.format('application/json', len(body))
                
            elif '/message' in path:
                # code to get messsages from server and return it
                # print('work in progress')
                response = handle_all_message(server, session_id, 0, True)
                
            else:
                response = http_error.format(404)
        else:
            response = http_error.format(401)
    except:
        traceback.print_exc()
        response = http_error.format(500)
            
    # print(response)
    return response
        
def handle_file_get_req(path):
    response = ''
    content_type = ''
    
    path_split = path.split('/')
    
    if len(path_split) <= 2:    
        file_name = path.split('/')[1].strip()
        file_ext = file_name.split('.')[1].strip()
        if file_ext == '.js':
            content_type = 'text/javascript'
        else:
            content_type = f'text/{file_ext}'
        
        if file_name in FILE_PATH_DIC and FILE_PATH_DIC[file_name]:
            if file_ext == 'ico':
                # file_content = read_file(FILE_PATH_DIC[file_name], 'rb')
                response = """HTTP/1.1 200 OK
Content-Type: text/text
Content-Length: 0
Connection: close

"""
            else:
                file_content = read_file(FILE_PATH_DIC[file_name], 'r')
                response = http_get_request.format(content_type, len(file_content))
                response += file_content
        else:
            response = http_error.format(404)
                
    else:
        response = http_error.format(404)
    
    return response
        

def handle_get_req(server, path, query_parms, cookie_dir):
    response = ''
    if path == '/': # first request to connect, return loginpage.html
        file_content = read_file('website/login/loginpage.html', 'r')
        response = http_get_request.format('text/html', len(file_content))
        response += file_content
    elif '/api' in path:
        response = handle_api_get_req(server, path, query_parms, cookie_dir['session_id'])
    elif path.endswith('.html') or path.endswith('.css') or path.endswith('.js') or path.endswith('.ico'):
        response = handle_file_get_req(path)
    else:
        response = http_error.format(404)


    return response


def generate_session_id(username):
    session_id = str(uuid.uuid4())
    CACHE_DIC[session_id] = [username]
    return session_id

# return sessionid
def process_login(server, username):
    message = f'[userjoin:{username}]'
    response = ''
    try:
        server.sendall(message.encode())
        data = server.recv(1024).decode('utf-8')
        data_dic = json.loads(data)
        
#         response_header = """HTTP/1.1 200 OK
# Content-Type: text/html
# Content-Length: {}
# Set-Cookie: session_id={}; HttpOnly
# Connection: close

# """
        session_id = generate_session_id(username)
        content = read_file('website/homepage/homepage.html', 'r')
        content = content.format(username)
        response = login_lo_header.format(len(content), session_id)
        response += content
        CACHE_DIC[session_id] = CACHE_DIC[session_id] + [data_dic['first_time'], data_dic['last_scene']]

    except Exception as e:
        traceback.print_exc()
        response = http_error.format(500)
        
    return response
        
def authenticate_user(session_id):
    valid = False
    
    if session_id in CACHE_DIC:
        valid = True
    
    return valid
        
def process_post_message(server, body_dir, session_id):
    response = ''
    
    if authenticate_user(session_id):
        if body_dir:
            username = CACHE_DIC[session_id][0]
            post_message = body_dir['msg']
            server_msg = f'[msg-post:{username}:{post_message}]'
            server.sendall(server_msg.encode())
            
            chat_server_response = ''
            while not chat_server_response:
                chat_server_response = server.recv(1024).decode('utf-8')
                
            if chat_server_response == 'msg-post-201-created':
                response = post_header_template.format('plain', 0)
            else:
                response = http_error.format(500)
        else:
            response = http_error.format(400)
    return response
     
        
def handle_post_req(server, path, query_parms, cookie_dir, content_len, body_dic):
    response = ''
    
    
    if 'api/message' in path:
        # print('POST: message in progress')
        if authenticate_user(cookie_dir['session_id']):
            response = process_post_message(server, body_dic, cookie_dir['session_id'])
        else:
            response = http_error.format(401)
    elif 'api/login' in path:
        response = process_login(server, query_parms['username'])
    else:
        response = http_error.format(404)
    return response

def process_logout(server, session_id):
    response = ''
    try:
        server.sendall(f'[lo:{CACHE_DIC[session_id][0]}]'.encode())
        server_response = server.recv(1024).decode('utf-8')
        if server_response == 'lo-200-okay':
            body = read_file('website/login/loginpage.html', 'r')
            response = login_lo_header.format(len(body), '')
            response += body
        else:
            raise Exception('Internal Server Error')
    except:
        traceback.print_exc()
        response = http_error.format(500)
    
    return response
        
def handle_del_req(server, path, cookie_dir):
    response = ''
    
    if 'api/login' in path:
        if authenticate_user(cookie_dir['session_id']):
            response = process_logout(server, cookie_dir['session_id'])        
        else:
            response = http_error.format(401)
    else:
        response = http_error.format(404)
    
    return response
    

def handle_http_req(server, raw_request):
    method, path, query_parms, cookie_dir, content_len, body_dic = parse_http_req(raw_request)
    
    # TODO: Implement sessionid check
    
    if method == 'GET':
        return handle_get_req(server, path, query_parms, cookie_dir)
    elif method == 'POST':
        return handle_post_req(server, path, query_parms, cookie_dir, content_len, body_dic)
    elif method == 'DELETE':
        return handle_del_req(server, path, cookie_dir)
    else:
        return http_error.format(405)

def handle_client(conn, addr):
    print('Connected by', addr)
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.connect((SERVER_HOST_IP, 8641))
    # server.setblocking(False)
    
    try:
        raw_request = conn.recv(1024).decode('utf-8')
        if not raw_request:
            # break  # Break if request is empty
            print(f'Disconnected from server {server.getsockname()}')

        else:
            response = handle_http_req(server, raw_request)
            # print(response)
            conn.sendall(response.encode())

    except Exception as e:
        print("Error handling request from", addr)
        traceback.print_exc()
    finally:
        server.close()
        conn.close()
        print("Connection closed with", addr)
        
# Main server code
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', PORT))
    s.listen(5)  # Allow a queue of 5 pending connections
    print(f"Server running on port {PORT}...")

    while True:
        try:
            conn, addr = s.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()  # Start a new thread for each connection
        except KeyboardInterrupt:
            print("Server shutting down.")
            break
        except Exception as e:
            print("Error accepting connections.")
            traceback.print_exc()
