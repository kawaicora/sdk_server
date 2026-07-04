
import asyncio
import secrets
import aiohttp
from flask import Response, request, current_app
import os
from datetime import datetime
import requests
from flask_socketio import emit
from app.extensions import socketio, db
from datetime import datetime
from app.settings import DefaultConfig
from app.sql_class.Tables import Message
from app.utils.ErrorCode import *
from app.route import bp
from app.route.socketio_common_services import get_user_by_sid, get_user_by_uid, get_room_by_sid, get_room_by_uid
from app.route.account_service import get_userinfo_by_uid
from app.sql_class.Tables import  Usermeta,Users




@socketio.on('get-room-message-history')
def handle_room_messages(data):
    sid = request.sid
    c_user = get_user_by_sid(sid)
    if not c_user:
        current_app.logger.info(f"Error in handle_room_messages: 用户不存在 - SID: {sid}")
        return
    uid = c_user.get("user_id")
    c_room = get_room_by_uid(c_user.get('user_id'))
    if not c_room:
        current_app.logger.info(f"Error in handle_room_messages: 用户没有匹配的房间 - SID: {sid}")
        return
    room_id = c_room.get('room_id')

    messages = Message.query.filter_by(room=room_id).all()
    
    for message in messages:
        t_sender_user_info = get_user_by_uid(message.sender_uid)
        if not t_sender_user_info:
            t_sender_user_info = get_userinfo_by_uid(message.sender_uid)
        if not t_sender_user_info:
            user:Users = Users.query.filter_by(ID=message.sender_uid).first()
            if user:
                user_meta_list:Usermeta = Usermeta.query.filter_by(user_id=message.sender_uid).all()
                user_meta = {}
                for meta in user_meta_list:
                    
                    user_meta[meta.meta_key] = meta.meta_value

                username = user.display_name
                client_ip = request.remote_addr
                client_ua = request.user_agent.string
                t_sender_user_info = {
                    "sid":sid,
                    "user_id": user.ID,
                    "user_login": user.user_login,
                    "user_email": user.user_email,
                    "display_name": user.display_name,
                    "user_url": user.user_url,
                    "user_registered": user.user_registered.strftime("%Y-%m-%d %H:%M:%S"),
                    "nickname": user_meta.get('nickname', user.display_name),
                    "avatar": user_meta.get('user_avatar', ""),
                    "last_login_time": user_meta.get('last_login_time', "未知"),
                    "last_login_ip": user_meta.get('last_login_ip', "未知"),
                    "current_ip": client_ip,
                    "user_agent": client_ua
                }
            else:
                t_sender_user_info = {
                   
                    "avatar": "/static/img/default_avatar.gif",
                    
                }
        sender_avatar = t_sender_user_info.get("avatar")
        emit('chat-message', {
            "sender_sid": message.sender_sid,
            "sender_uid": message.sender_uid,
            "sender_avatar" : sender_avatar,
            "sender_username": message.sender_username,
            "message": message.message,
            "type":message.type,
            "timestamp": message.timestamp.isoformat()
        })


@socketio.on('chat-message')
def handle_chat_message(data):
    sid = request.sid
    c_user = get_user_by_sid(sid)
        
    message_text = data.get('message')
    message_type = data.get('type')

    if not c_user:
        if (message_type != 'text' and message_type != 'html'):
            if message_text[0] == '/':
                file_path = message_text[1:]
            if os.path.exists(file_path):
                os.remove(file_path)
        current_app.logger.info(f"Error in handle_chat_message: 用户不存在 - SID: {sid}")
        return
    
    sender_uid = c_user.get('user_id')
    sender_username = c_user.get('display_name')
    sender_avatar = c_user.get('avatar')
    room = get_room_by_sid(sid)
    if not room or not message_text:
        return
    
    
    current_app.logger.info(f"收到消息 - 用户名: {sender_username}, UID: {sender_uid}, SID: {sid}, 房间: {room}, 消息: {message_text}")
    
    result:str = message_text
    if result.startswith(" "):
        emit("error",{"event":"chat-message","msg":"消息第一个字符不能是空格"})
        current_app.logger.debug("消息第一个字符不能是空格")
        return
    if result.endswith(" "):
        emit("error",{"event":"chat-message","msg":"消息最后一个字符不能是空格"})
        current_app.logger.debug("消息最后一个字符不能是空格")
        return
    if "script" in result and ">" in result and "<" in result and "/" in result:
        emit("error",{"event":"chat-message","msg":"消息不能为<script> 相关的HTML代码"})
        current_app.logger.debug("消息不能为HTML Javascript代码 跳过")
        return

    # 保存消息到数据库
    new_message = Message(
        sender_sid=sid,
        sender_uid=sender_uid,
        sender_username= sender_username,
        message=message_text,
        type=message_type,
        room=room.get('room_id'),
        timestamp=datetime.now()
    )
    db.session.add(new_message)
    db.session.commit()
    
    # 广播消息给房间内所有用户
    emit('chat-message', {
        "sender_sid": sid,
        "sender_uid": sender_uid,
        "sender_username": sender_username,
        "sender_avatar": sender_avatar,
        "message": message_text,
        "type":message_type,
        "timestamp": new_message.timestamp.isoformat()
    }, room=room.get('room_id'))




@bp.route('/api/tags', methods=['GET', 'POST'])
def api_tags():
    req_url = f'{DefaultConfig.OLLAMA_API}/api/tags'
    headers = dict(request.headers)

    def sync_stream():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.get(req_url, headers=headers) as response:
                    try:
                        while True:
                            chunk = await response.content.read(1)  # 每次读取 1 字节
                            if not chunk:
                                break
                            yield chunk
                    except Exception as e:
                        print(f"Streaming error: {e}")
                    finally:
                        await response.release()

        try:
            async_gen = make_request()
            while True:
                try:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
        except Exception as e:
            print(f"Error in sync generator: {e}")
        finally:
            loop.close()

    resp_headers = {}
    return Response(sync_stream(), status=200, headers=resp_headers)





@bp.route('/api/generate', methods=['GET', 'POST'])
def api_generate():
    req_url = f'{DefaultConfig.OLLAMA_API}/api/generate'
    headers = dict(request.headers)
    data = request.get_data()
    def sync_stream():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def make_request():
            async with aiohttp.ClientSession() as session:
                async with session.post(req_url,data= data, headers=headers) as response:
                    try:
                        while True:
                            chunk = await response.content.read(1)  # 每次读取 1 字节
                            if not chunk:
                                break
                            yield chunk
                    except Exception as e:
                        print(f"Streaming error: {e}")
                    finally:
                        await response.release()

        try:
            async_gen = make_request()
            while True:
                try:
                    chunk = loop.run_until_complete(async_gen.__anext__())
                    yield chunk
                except StopAsyncIteration:
                    break
        except Exception as e:
            print(f"Error in sync generator: {e}")
        finally:
            loop.close()

    resp_headers = {}
    return Response(sync_stream(), status=200, headers=resp_headers)



