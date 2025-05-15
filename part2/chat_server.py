import socket
import select
import sys
import traceback
import sqlite3
import re
import time
import json

regex = r'\[([^\[\]]+(?:\[[^\[\]]*\])?[^\[\]]*)\]'


db_conn = sqlite3.connect('chatbot.db')
cursor = db_conn.cursor()

def append_history(socket, username, last_scene, first_time):
    messages_dir[socket] = []
    if not first_time:
        sql = 'SELECT username, \"message\" FROM chats WHERE send_time >= ? ORDER BY send_time LIMIT 37'
        try:
            cursor.execute(sql, (last_scene,))
            rows = cursor.fetchall()
            for r in rows:
                data = '[' + r[0] + ": " + r[1] + ']'
                messages_dir[socket].append(data.encode())
        except Exception as e:
            traceback.print_exc()
            
    else:
        sql = 'SELECT username, \"message\" FROM chats ORDER BY send_time DESC LIMIT 37'
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            for r in rows:
                data = '[' + r[0] + ": " + r[1] + ']'
                messages_dir[socket].append(data.encode())
        except Exception as e:
            traceback.print_exc()
    
    if socket not in outputs:
        outputs.append(socket)
    
def process_userjoin(username):
    sql = 'INSERT INTO users values (?, ?)'
    last_scene = int(time.time())
    first_time = True
    try:
        cursor.execute(sql, (username, last_scene))
        db_conn.commit()
        
    except sqlite3.IntegrityError as ie:
        first_time = False
        sql = 'SELECT * FROM users WHERE username = ?'
        cursor.execute(sql, (username,))
        row = cursor.fetchone()
        last_scene = row[1]
    
    return first_time, last_scene

def process_data_recv(socket, data):
    # data = data.decode('UTF-8')
    print(data)
    messages = re.findall(regex, data)
    
    for m in messages:
        input = m.split(':')
        msg_key = input[0].strip()
        username = input[1].strip()
        if msg_key == 'userjoin':
            first_time, last_scene = process_userjoin(username)
            username_dir[socket] = username
            append_history(socket, username, last_scene, first_time)
        elif msg_key == 'msg':
            sql = 'INSERT INTO chats (username, message, send_time) values (?, ?, ?)'
            msg = input[2].strip()
            try:
                cursor.execute(sql, (username, msg, int(time.time())))
                db_conn.commit()
            except Exception as e:
                print(e)
            append_send_message(('[' + username + ': ' + msg + ']').encode())
                
def process_client_disconnect(username):
    sql = 'UPDATE users SET last_scene = ? WHERE username = ?'
    try:
        cursor.execute(sql, (int(time.time()), username))
        db_conn.commit()
    except Exception as e:
        print(e)

a1_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
a1_server.setblocking(False)

# bind the socket to a public host, and a well-known port
hostname = socket.gethostname()
# This accepts a tuple...
a1_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
a1_server.bind(('', 8640))
a1_server.listen()
# print("listening on interface ", hostname , server.getsockname(), "\n\texcept localhost/127.0.0.1")
print("listening on interface ", hostname , a1_server.getsockname())

web_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
web_server.setblocking(False)
web_server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
web_server.bind(('', 8641))
web_server.listen()
# also listen on local
local = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# non-blocking, so that select can deal with the multiplexing
local.setblocking(False)
# This accepts a tuple...
local.bind(('127.0.0.1', 50013))

# inputs will have client sockets as well
inputs = [a1_server, web_server]
outputs = [] # None

a1_clients = []
web_clients = []


messages_dir = {}
username_dir = {}

def append_send_message(send_message):
    for s in messages_dir:
        messages_dir[s].append(send_message)
        
        if s not in outputs:
            outputs.append(s)
            
def get_history(first_time, last_scene):
    msg_arr = []
    
    if not first_time:
        sql = 'SELECT id, username, \"message\", send_time FROM chats WHERE send_time > ? ORDER BY send_time DESC LIMIT 37'
        try:
            cursor.execute(sql, (last_scene,))
            rows = cursor.fetchall()
            for r in reversed(rows):
                data_dir = {
                    "msg_id": int(r[0]),
                    "username": r[1],
                    "msg": r[2],
                    "send_time": int(r[3])
                }
                msg_arr.append(data_dir)
        except Exception as e:
            traceback.print_exc()
            msg_arr = []
            
    else:
        sql = 'SELECT id, username, \"message\", send_time FROM chats ORDER BY send_time DESC LIMIT 37'
        try:
            cursor.execute(sql)
            rows = cursor.fetchall()
            for r in reversed(rows):
                data_dir = {
                    "msg_id": int(r[0]),
                    "username": r[1],
                    "msg": r[2],
                    "send_time": int(r[3])
                }
                msg_arr.append(data_dir)
        except Exception as e:
            traceback.print_exc()
            msg_arr = []
    return msg_arr
    
def process_web_client_recv(socket, data):
    print(data)
    messages = re.findall(regex, data)
    for m in messages:
        input = m.split(':')
        msg_key = input[0].strip()
        username = input[1].strip()
        
        try:
            if msg_key == 'userjoin':
                first_time, last_scene = process_userjoin(username)
                socket.sendall(f'{{"username": "{username}", "first_time": {str(first_time).lower()}, "last_scene": {last_scene}}}'.encode())
            elif msg_key == 'msg-post':
                sql = 'INSERT INTO chats (username, message, send_time) values (?, ?, ?)'
                msg = input[2].strip()
                try:
                    cursor.execute(sql, (username, msg, int(time.time())))
                    db_conn.commit()
                except Exception as e:
                    print(e)
                socket.sendall('msg-post-201-created'.encode())
                append_send_message(('[' + username + ': ' + msg + ']').encode())
            elif msg_key == 'msg':
                # [msg:username:first_time:last_scene]
                first_time = input[2] == "True"
                last_scene = int(input[3])
                msg_arr = get_history(first_time, last_scene)
                send_data = json.dumps(msg_arr)
                socket.sendall(send_data.encode())
            elif msg_key == 'msgt':
                # [msg:username:time]
                msg_time = int(input[2])
                msg_arr = get_history(False, msg_time)
                send_data = json.dumps(msg_arr)
                socket.sendall(send_data.encode())
                
            elif msg_key == 'lo':
                process_client_disconnect(username)
                socket.sendall('lo-200-okay'.encode())
        except:
            traceback.print_exc()
            socket.sendall('chat-server-500-error'.encode())

        
    
    
while True:
    try:
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        
        for source in readable:
            # select listned someone getting connected to server,
            # so add the client socket to the input list
            if source is a1_server:
                conn, addr = source.accept()
                print("Heard Externally")
                print("New terminal client connected", conn.getpeername())
                conn.setblocking(False)
                a1_clients.append(conn)
                inputs.append(conn)
                        
            elif source is web_server:
                # Handle webserver which have different protocal
                conn, addr = source.accept()
                print("Hear Externally")
                print("New web server connection", conn.getpeername())
                web_clients.append(conn)
                inputs.append(conn)
            
            else:
                print("Heard Externally")
                data_recv = source.recv(1024)
                data = data_recv
                while(len(data_recv) >= 1024):
                    data_recv = source.recv(1024)
                    data += data_recv
                
                if data:
                    if source in a1_clients:
                        process_data_recv(source, data.decode('UTF-8'))
                    elif source in web_clients:
                        process_web_client_recv(source, data.decode('UTF-8'))
                        
                else:
                    # Client has disconected
                    if source in username_dir:
                        process_client_disconnect(username_dir[source])
                        username_dir[source] = ''
                        del messages_dir[source]
                    
                    print('Client disconnected', source.getpeername())
                    inputs.remove(source)
                    source.close()    
        
        for source in writable:
            try:
                # send the messages once the client is back online
                # and remove all the messages from the dictionary
                if source in messages_dir:    
                    while messages_dir[source]:
                        data = messages_dir[source].pop(0)
                        print(data.decode('UTF-8'))
                        print(len(data.decode('UTF-8')))
                        # print('sending:', data)
                        source.send(data)
                outputs.remove(source)
            except BlockingIOError:
                continue
                
    except KeyboardInterrupt:
        print(" I guess I'll just die")
        a1_server.close()
        local.close()
        cursor.close()
        db_conn.close()
        sys.exit(0)
    
    except Exception as e:
        print("SOMETHING IS BAD")
        print(e)
        traceback.print_exc()
        sys.exit(0)
