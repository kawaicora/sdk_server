# -*- coding: utf-8 -*-
import threading
from app.bots.TelegramBot import TelegramBot

from gameservice.lua_engine import *
from proto.define_pb2 import *
from app.settings import DefaultConfig
import socket
from app.utils.CommonUtils import *




class GameServer(threading.Thread):
    
    def __init__(self):
        super(GameServer,self).__init__()
        logging.info("gameserver instence!")
        self.session = []
        self.telegram_bot = TelegramBot()
        logging.info("🛠️ 游戏服务器初始化完成")


    def run(self):
        logging.info("🎮 游戏服务器线程运行中")
        lua_engine = LuaEngine()
        lua_engine.load_all_lua_scripts()
        logging.info("lua init success!")
        self.game_tcp_thread = threading.Thread(target=self.tcp_socket)
        self.game_tcp_thread.setDaemon(False)
        self.game_tcp_thread.start()
        logging.info(f"gameserver listen on {DefaultConfig.GAMESERVER_LISTEN_IP}:{str(DefaultConfig.GAMESERVER_LISTEN_PORT)}")
    def tcp_socket(self):
        # 创建 TCP 套接字
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # 设置套接字选项，允许地址重用
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # 绑定主机和端口
        self.server_socket.bind((DefaultConfig.GAMESERVER_LISTEN_IP, DefaultConfig.GAMESERVER_LISTEN_PORT))

        # 开始监听
        self.server_socket.listen()
    
        try:
            while True:
                
                # 接受客户端连接
                client_socket, client_address = self.server_socket.accept()
                # 为每个客户端连接创建一个新的线程来处理
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, client_address))
                client_thread.start()
                tmp_session_info = {
                    'socket':client_socket,
                    'adderss':client_address,
                    'thread':client_thread,
                    'uid':-1
                }
                self.session.append(tmp_session_info)
        except KeyboardInterrupt:
            print("Server shutting down...")
        finally:
            # 关闭服务器套接字
            self.server_socket.close()
        

    # 处理客户端连接的函数
    def handle_client(self,client_socket, client_address):
        logging.info(f"Accepted connection from {client_address}")
        try:
            is_packet = False
            while True:

                # 接收客户端发送的数据
                data = client_socket.recv(1024)
                if not data:
                    break
                # 将接收到的数据解码为字符串
                data = self.parse_http_header(data)
                if data != None:
                    header,body = data
                    logging.info(f"\n\n\n{str(header)}\n\n\n")
                    logging.info(f"\n\n\n{str(body)}\n\n\n")
                    client_socket.send("Server: AppleServer_12.0\r\ncontent-type:text/plan; charset=utf-8\r\n\r\n你好".encode())
                continue
                    

                logging.info(f"Received from {client_address}")
                CommonUtils.hex_dump(logging.info,data)

        except Exception as e:
            logging.info(f"Error handling client {client_address}: {e}")
        finally:
            # 关闭客户端连接
            client_socket.close()
            logging.info(f"Connection with {client_address} closed")

    def parse_http_header(self,data):
        header_end = data.find(b'\r\n\r\n')
        if header_end == -1:
            # 头部不完整，需要继续读取
            return None
        header = data[:header_end]
        body = data[header_end + 4:]  # 跳过 \r\n\r\n
        return header, body
