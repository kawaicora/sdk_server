# -*- coding: utf-8 -*-
from app.route import bp
from flask import jsonify, request, current_app
from app.extensions import socketio
from flask_socketio import emit, join_room, leave_room 
from app.settings import DefaultConfig
from app.sql_class.Tables import Users,Usermeta
from app.utils.CommonUtils import *
from app.route.socketio_common_services import add_user_to_room, get_room_users, get_user_by_sid, is_user_in_room,get_room_by_sid,get_room_by_uid, remove_user_from_room, user_sessions,rooms


def get_ice_servers():
    import requests

    # 请求URL
    url = "https://rtc.live.cloudflare.com/v1/turn/keys/3b16904f090cf0daabf42ce82d33b672/credentials/generate-ice-servers"

    # 请求头
    headers = {
        "Authorization": f"Bearer {DefaultConfig.CLOUDFLARE_TURN_TOKEN}",
        "Content-Type": "application/json"
    }

    # 请求体数据
    data = {
        "ttl": 86400  # 凭证有效期（秒），这里设置为24小时*7天
    }
    response = requests.post(url, json=data, headers=headers)
    if (response.status_code != 200 and response.status_code != 201):
        logger.error(f"Failed to get ICE servers config from Cloudflare: {response.status_code} - {response.text}")
        return DefaultConfig.ICE_SERVERS
    return response.json()


@bp.route("/api/ice_servers_config",methods=['GET','POST'])
def handle_ice_servers_config():
    
    return CommonUtils.json_response(get_ice_servers(),status=200)
        
    
# ---------------------- WebRTC 信令处理（保持逻辑，适配分离后的数据结构） ----------------------
@socketio.on('offer')
def handle_offer(data):
    sid = request.sid
    sender = get_user_by_sid(sid)
    if not sender:
        current_app.logger.warning("sender is None")
        return
    
    target_sid = data.get('target')
    room_id = data.get('room_id')
    offer = data.get('offer')
    
    # 检查目标用户是否存在且在同一房间
    target = get_user_by_sid(target_sid)
    if not target or not is_user_in_room(target["user_id"], room_id):
        current_app.logger.warning("target is None or not in room")
        return
    
    # 转发 offer 给目标用户
    emit('offer', {
        "from_sid": sid,
        "from_uid": sender["user_id"],
        "from_username": sender["display_name"],
        "offer": offer,
        "room_id": room_id
    }, room=target_sid)


@socketio.on('answer')
def handle_answer(data):
    sid = request.sid
    sender = get_user_by_sid(sid)
    if not sender:
        current_app.logger.warning("sender is None")
        return
    
    target_sid = data.get('target')
    room_id = data.get('room_id')
    answer = data.get('answer')
    
    target = get_user_by_sid(target_sid)
    if not target or not is_user_in_room(target["user_id"], room_id):
        current_app.logger.warning("target is None or not in room")
        return
    
    # 转发 answer 给目标用户
    emit('answer', {
        "from_sid": sid,
        "from_uid": sender["user_id"],
        "from_username": sender["display_name"],
        "answer": answer,
        "room_id": room_id
    }, room=target_sid)


@socketio.on('ice-candidate')
def handle_ice_candidate(data):
    sid = request.sid
    sender = get_user_by_sid(sid)
    if not sender:
        return
    
    target_sid = data.get('target')
    room_id = data.get('room_id')
    candidate = data.get('candidate')
    
    target = get_user_by_sid(target_sid)
    if not target or not is_user_in_room(target["user_id"], room_id):
        return
    
    # 转发 ice-candidate 给目标用户
    emit('ice-candidate', {
        "from_sid": sid,
        "from_uid": sender["user_id"],
        "candidate": candidate,
        "room_id": room_id
    }, room=target_sid)


@socketio.on('on-connection-state-change')
def handle_on_connection_state_change(data):
    sid = request.sid
    user = get_user_by_sid(sid)
    target_sid = data.get('target')
    target_user = get_user_by_sid(target_sid) 
    target_room = get_room_by_sid(target_sid)
    if(user is None or target_user is None):
        current_app.logger.warning("user or target_user is None")
        return
    current_app.logger.info(f"------- 用户:{user.get('display_name')} SID:{sid} 报告 ,目标用户:{target_user.get('display_name')} SID:{target_sid} 连接状态: {data.get('state')} -------")
    if (data.get('state') == 'disconnected' or data.get('state') == 'failed'  or data.get('state') == 'closed') and target_room:
        current_app.logger.info(f"------- 用户:{user.get('display_name')} SID:{sid} 报告 ,目标用户:{target_user.get('display_name')} SID:{target_sid} 连接异常 -------")
        
        socketio.emit('error',{
            'event':'on-connection-state-change',
            'msg':f"------- 用户:{user.get('display_name')} SID:{sid} 报告 ,目标用户:{target_user.get('display_name')} SID:{target_sid} 连接异常 -------"
        })
