# -*- coding: utf-8 -*-
import threading
from app.route import bp
from flask import Request, jsonify, request, current_app
from app.extensions import socketio, db
from app.route.account_service import get_userinfo_by_token, get_userinfo_by_token
from app.sql_class.Tables import AccountToken, Usermeta,Users,Room,RoomUser,RoomBanUser
from flask_socketio import emit, join_room, leave_room 
from app.utils.CommonUtils import *
import requests
from app.settings import DefaultConfig
write_config_thread = None
# ---------------------- 分离后的核心数据结构 ----------------------
# 用户会话信息：仅存储用户自身基础信息（与房间无关）
user_sessions = []
# [
#     {
#         "uid": 123,
#         "sid": "socket-123",  # Socket.IO 连接的唯一标识
#         "username": "报喜",
#         "avatar": "/static/upload/xxx.png"
#     },
#    ...
# ]

# 房间信息：独立存储房间属性及房间内用户关联
rooms = []
# [
#     {
#         "room_id": "room-1001",  # 房间唯一标识
#         "title": "测试房间",
#         "desc": "这是一个测试房间",
#         "create_time": 1718888888,  # 房间创建时间（时间戳）
#         "updated_time": None,
#         "deleted_time": None,
#         "cover": "/static/uploads/cover.jpg",  # 房间封面
#         "users": [  # 房间内的用户列表（仅存储 uid 和加入时间）
#             {
#                 "uid": 123,
#                 "join_time": 1718888890
#             },
#            ...
#         ],
#         "ban_users": [  # 被禁言/禁止进入的用户
#             {
#                 "uid": 456,
#                 "ban_time": 1718888900
#             },
#            ...
#         ],
#         "creator":uid
#         "room_type":room_type
#     },
#    ...
# ]




guest_counter = 900000000

# ---------------------- 工具函数（用户相关） ----------------------
def get_user_info(request:Request):
    """从 Cookie 中获取已登录用户信息（uid 和 username）"""
    if not request.cookies.get('token'):
        return gen_guest_user(request)
    result = get_userinfo_by_token(request.cookies.get('token'))

   
    if result != None:
        result['sid'] = request.sid
        return result
    else:
        
        return gen_guest_user(request)

    
def gen_guest_user(request:Request,uid = None):
    global guest_counter
    curren_counter = guest_counter #游客创建永远从guest_counter 开始
    if uid == None:
        uid = curren_counter
        
    while True: #用户已存在持续加 
        if not get_user_by_uid(uid):
            break
        curren_counter += 1
        uid = curren_counter
    username = f"游客_{uid}"

    user_data = {
        "sid":request.sid,
        "user_id": uid,
        "user_login": "",
        "user_email": "",
        "display_name": username,
        "user_url": "",
        "user_registered": "",
        "nickname": "",
        "avatar": "",
        "last_login_time": "",
        "last_login_ip": "",
        "current_ip": "",
        "user_agent": ""
    }
    return user_data


def sid_exists(sid):
    """检查 sid 是否存在于 user_sessions 中"""
    return any(session["sid"] == sid for session in user_sessions)

def get_user_by_sid(sid):
    """根据 sid 获取完整的用户会话信息"""
    for session in user_sessions:
        try:
            if session["sid"] == sid:
                return session
        except :
            return None
    return None


def get_user_by_uid(uid):
    """根据 uid 获取用户会话信息（可能有多个 sid，返回第一个）"""
    for session in user_sessions:
        if session["user_id"] == uid:
            return session
    return None


def update_sid_by_uid(uid,sid):
    """
    根据用户ID更新对应的sid。如果用户不存在，则不执行任何操作。
    
    Args:
        uid (int): 用户ID
        sid (str): 新的Socket.IO会话ID
    """
    for session in user_sessions:
        if session["user_id"] == uid:
            session["sid"] = sid
            break  # 找到用户后立即退出循环

def get_room_by_uid(uid):
    if db.session.query(RoomUser).filter_by(uid=uid).first():
        room_user = db.session.query(RoomUser).filter_by(uid=uid).first()
        room = db.session.query(Room).filter_by(room_id=room_user.room_id).first()
        return {
            "room_id": room.room_id,
            "title": room.title,
            "desc": room.desc,
            "create_time": room.create_time,
            "updated_time": room.updated_time,
            "deleted_time": room.deleted_time,
            "cover": room.cover,
            "creator": room.creator,
            "room_type": room.room_type
        }
    return None

def get_room_by_sid(sid):
    user = get_user_by_sid(sid)
    if user is None:
        return None
    room_user = db.session.query(RoomUser).filter_by(uid=user.get("user_id")).first()
    if room_user:
        return get_room_by_id(room_user.room_id)
    return None

def remove_user_from_user_sessions( uid=None, sid=None):
    """将用户从user_sessions  列表中移除"""
    global user_sessions  # 声明使用全局变量
    # 参数校验
    if uid is None and sid is None:
        raise ValueError("至少需要提供 uid 或 sid 其中一个参数")
    if uid is not None and sid is not None:
        raise ValueError("只能提供 uid 或 sid 其中一个参数")
    
    
    if uid is not None:
        user_sessions = [user_session for user_session in user_sessions if user_session["user_id"] != uid]
    else:
        user_sessions = [user_session for user_session in user_sessions if user_session["sid"] != sid]
    
    return True



# ---------------------- 工具函数（房间相关） ----------------------
def get_room_by_id(room_id) ->Room :
    """根据 room_id 获取房间完整信息"""
    room:Room = db.session.query(Room).filter_by(room_id=room_id).first()
    return {
        "room_id": room.room_id,
        "title": room.title,
        "desc": room.desc,
        "create_time": room.create_time,
        "updated_time": room.updated_time,
        "deleted_time": room.deleted_time,
        "cover": room.cover,
        "creator": room.creator,
        "room_type": room.room_type
    }
   


def room_exists(room_id) ->bool:
    """检查房间是否存在"""
    return db.session.query(Room).filter_by(room_id=room_id).first() is not None


def is_user_in_room(uid, room_id):
    """检查用户是否在指定房间内"""
    if db.session.query(RoomUser).filter_by(room_id=room_id,uid=uid).first():
        return True
    return False

def add_user_to_room(uid, room_id):
    """将用户添加到房间的 users 列表（记录加入时间）"""
    room:Room = db.session.query(Room).filter_by(room_id=room_id).first()
    if not room:
        return False
    # 避免重复添加
    if is_user_in_room(uid, room_id):
        return True
    room_user = RoomUser(uid=uid, room_id=room_id, join_time=int(datetime.now().timestamp()))
    db.session.add(room_user)
    db.session.commit()
    return True

def remove_user_from_room(room_id, uid=None):
    """将用户从房间的 users 列表中移除"""
    db.session.query(RoomUser).filter_by(room_id=room_id,uid=uid).delete()
    db.session.commit()
    return True



def is_user_banned(uid, room_id):
    """检查用户是否被禁止进入房间"""
    if db.session.query(RoomBanUser).filter_by(room_id=room_id,uid=uid).first():
        return True
    return False

def get_room_users(room_id):
    """获取房间内所有用户的详细信息（结合 user_sessions）"""
    # 从 user_sessions 中查询每个 uid 对应的用户详情
    room_user_details = []
    room_users = db.session.query(RoomUser).filter_by(room_id=room_id).all()
    if room_users is None:
        return []
    for user in room_users:
        user_session = get_user_by_uid(user.uid)
        if user_session:
            room_user_details.append({
                "uid": user.uid,
                "sid": user_session["sid"],
                "username": user_session["display_name"],
                "avatar": user_session.get("avatar", ""),
                "join_time": user.join_time
            })
    return room_user_details





def title_exists(title):
    """检查是否存在相同标题的房间（不区分大小写）"""
    if db.session.query(Room).filter(Room.title.ilike(title)).first():
        return True
    return False

# ---------------------- Socket.IO 事件处理 ----------------------


@socketio.on('get-current-sid')
def handle_get_sid():
    """获取SID"""
    emit("current-sid",{'sid':request.sid})

@socketio.on('connect')
def handle_user_connect(*args):
    """用户注册（建立连接时初始化会话信息）"""
    global guest_counter
    global write_config_thread
    sid = request.sid
    user_data = None
    # 若已注册则跳过（避免重复添加）
    if sid_exists(sid):
        return
   
    

    # 获取用户信息（已登录用户用真实 uid，游客生成临时 uid）
    user_data = get_user_info(request)
    if not user_data :
        return
    # 检查用户是否已经存在
    c_user =  get_user_by_uid(user_data.get("user_id"))
    if c_user:
        current_app.logger.info(f"用户存在,更新SID-UID关系- SID: {sid}, UID: {user_data.get("user_id")}, 用户名: {user_data.get("display_name")}")
        update_sid_by_uid(user_data.get("user_id"),sid)
    else:
        
        current_app.logger.info(f"没有找到,添加用户 - SID: {sid}, UID: {user_data.get("user_id")}, 用户名: {user_data.get("display_name")}")
        user_sessions.append(user_data)
        c_user = user_data

    rows = (
        db.session.query(RoomUser)
        .filter_by(uid=c_user.get("user_id"))
        .delete()
    )

    if rows:
        db.session.commit()

    # 通知客户端注册成功
    emit('connected', {
        "sid": sid,
        "uid": c_user.get("user_id"),
        "username": c_user.get("display_name"),
        "avatar":c_user.get("avatar") or ""
    })
    emit('room-list-updated', get_room_list(), broadcast=True)
    current_app.logger.info(f"用户注册 - SID: {sid}, UID: {c_user.get("user_id")}, 用户名: {user_data.get("display_name")}")

@socketio.on('is-in-room')

def handle_is_user_in_room(data):
    sid = request.sid
    c_room = get_room_by_sid(sid)
    if not c_room:
        emit('is_user_in_room',{'is_in_room':False},sid = sid)
    else:
        emit('is_user_in_room',{'is_in_room':True},sid = sid)




@socketio.on('room_users_update')
def handle_room_users_update(data):
    room_id = data.get('room_id')
    # 刷新房间用户列表
    emit('room-users-updated', {
        "room_id": room_id,
        "users": get_room_users(room_id)
    }, room=room_id)



@socketio.on('delete-room')
def handle_delete_room(data):
    """删除房间"""
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user:
        emit('error', {"event": "delete-room", "msg": "用户未注册"}, sid=sid)
        handle_user_connect()
    
    uid = user["user_id"]
    username = user["display_name"]
    room_id = data.get("room_id")
    room = db.session.query(Room).filter_by(room_id=room_id).first()
    users = db.session.query(RoomUser).filter_by(room_id=room_id).all()
    if users :
        for t_user in users:
            c_user = get_user_by_uid(t_user.user_id)
            emit('user-left-room', {
                "sid": c_user.get('sid'),
                "uid": c_user.get('uid'),
                "username": c_user.get('username'),
                "room_id":t_user.room_id
            }, room=t_user.room_id)

    db.session.query(RoomUser).filter_by(room_id=room_id).delete()
    db.session.commit()

    db.session.query(Room).filter_by(room_id=room_id).delete()
    db.session.commit()

    
    emit('room-deleted', {
        "room_id": room_id,
        "title": room.title,
        "sid":sid,
        "uid":uid,
        "username":username
    }, sid=sid)
    
    # 广播房间列表更新
    emit('room-list-updated', get_room_list(), broadcast=True)
    current_app.logger.info(f"房间删除 - 房间ID: {room_id}, 标题: {room.title}")




@socketio.on('create-room')
def handle_create_room(data):
    """创建房间"""
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user:
        emit('error', {"event": "delete-room", "msg": "用户未注册"}, sid=sid)
        handle_user_connect()
    
    uid = user["user_id"]
    room_id = data.get("room_id")
    title = data.get("title", "未命名房间")
    password = data.get("password", "")
    isencrypted = data.get("isencrypted", False)
    desc = data.get("desc", "")
    cover = data.get("cover", "")
    room_type = data.get('room_type') 
    # 检查房间ID是否已存在
    if room_exists(room_id):
        emit('error', {"event": "create-room", "msg": "房间ID已存在"}, sid=sid)
        return
    
    # 新增：检查房间标题是否已存在（不区分大小写）
    if title_exists(title):
        emit('error', {"event": "create-room", "msg": "房间标题已存在，请使用其他标题"}, sid=sid)
        return

    if isencrypted and password != "":
        password = CommonUtils.rsa_decrypt(password.encode('utf-8'))
    
    room = Room(
        room_id = room_id,
        title = title,
        desc = desc,
        create_time = int(datetime.now().timestamp()),
        updated_time = None,
        deleted_time = None,
        password = CommonUtils.create_sha_passwd(password) if password else "",
        cover = cover,
        creator = uid,
        room_type = room_type
    )
    db.session.add(room)
    db.session.commit()
    
    # 通知客户端创建成功
    emit('room-created', {
        "room_id": room_id,
        "room_info":{
            "room_id": room.room_id,
            "title": room.title,
            "desc": room.desc,
            "create_time": room.create_time,
            "updated_time": room.updated_time,
            "deleted_time": room.deleted_time,
            "cover": room.cover,
            "creator": room.creator,
            "room_type": room.room_type
        },
        "users": get_room_users(room_id)
    }, sid=sid)
    
    # 广播房间列表更新
    emit('room-list-updated', get_room_list(), broadcast=True)
    current_app.logger.info(f"房间创建 - 创建者 UID: {uid}, 房间ID: {room_id}, 标题: {title}")



@socketio.on('get—current-room')
def handle_get_room(data):
    sid = request.sid
    room = get_room_by_sid(sid=sid)
    emit('current-room',{'sid':sid,'room':room})

@socketio.on('join-room')
def handle_join_room(data):
    """加入房间"""
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user:
        emit('error', {"event": "join-room", "msg": "用户未注册"}, sid=sid)
        handle_user_connect()
    
    uid = user["user_id"]
    room_id = data.get("room_id")
    
    if not room_id:
        emit('error', {"event": "join-room", "msg": "房间ID不能为空"}, sid=sid)
        return
    
    # 检查房间是否存在
    room = get_room_by_id(room_id)
    if not room:
        emit('error', {"event": "join-room", "msg": "房间不存在"}, sid=sid)
        return
    
    # 检查是否被禁言
    if is_user_banned(uid, room_id):
        emit('error', {"event": "join-room", "msg": "您已被禁止进入该房间"}, sid=sid)
        return
    
    # 检查是否已在房间内
    if is_user_in_room(uid, room_id):
        emit('error', {"event": "join-room", "msg": "已在房间内"}, sid=sid)
        return
    
    # 添加用户到房间
    add_user_to_room(uid, room_id)
    join_room(room_id)  # Socket.IO 加入房间


    # 通知房间内其他用户
    emit('user-joined-room', {
        "sid":sid,
        "uid": uid,
        "username": user["display_name"],
        "room_id": room_id,
        "room_info": room
    }, room=room_id,include_self=False)
    
    # 通知当前用户加入成功
    emit('joined-room', {
        "room_id": room_id,
        "room_info": room,
        "users": get_room_users(room_id),
        "uid":uid,
        "sid":sid,
        "username": user["display_name"]
    }, sid=sid)   #
    
    # 刷新房间用户列表
    emit('room-users-updated', {
        "room_id": room_id,
        "users": get_room_users(room_id)
    }, room=room_id)
    current_app.logger.info(f"用户加入房间 - UID: {uid}, 房间ID: {room_id}")


@socketio.on('leave-room')
def handle_leave_room(data):
    """离开房间"""
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user:
        emit('error', {"event": "leave-room", "msg": "用户未注册"}, sid=sid)
        handle_user_connect()
    
    uid = user["user_id"]
    room_id = data.get("room_id")
    room = get_room_by_id(room_id)
    if not room:
        return
    
    # 从房间中移除用户
    remove_user_from_room(uid = uid,room_id= room_id)
        
        
    # 通知房间内其他用户
    emit('user-left-room', {
        "sid":sid,
        "uid": uid,
        "username": user["display_name"],
        "room_id": room_id
    }, room=room_id)
    leave_room(room_id)  # Socket.IO 离开房间
    # 刷新房间用户列表
    emit('room-users-updated', {
        "room_id": room_id,
        "users": get_room_users(room_id)
    }, room=room_id)
    
    # 若房间为空则删除
    # if not room["users"]:
    #     global rooms
    #     rooms = [r for r in rooms if r["room_id"]!= room_id]
    #     emit('room-list-updated', get_room_list(), broadcast=True)
        
    current_app.logger.info(f"用户离开房间 - UID: {uid}, 房间ID: {room_id}")



def get_room_list():
    """生成房间列表（简化版，仅包含基础信息）"""
    room_list:Room = db.session.query(Room).filter(Room.deleted_time == None).all()
    
    return [
        {
            "room_id": room.room_id,
            "title": room.title,
            "cover": room.cover,
            "room_type":room.room_type,
            "user_count": len(db.session.query(RoomUser).filter(RoomUser.room_id == room.room_id).all()),  # 房间人数
            "create_time": room.create_time

        } for room in room_list
    ]


@socketio.on('disconnect')
def handle_disconnect():
    global user_sessions
    sid = request.sid
    
    # 查找该 sid 对应的 uid（如果存在）
    user = get_user_by_sid(sid)
    if not user:
        emit('error', {"event": "disconnect", "msg": "用户未注册"}, sid=sid)
        return  # 未找到关联会话，可能是无效连接
    
    uid = user.get("user_id")
    username = user.get("username")
    room_users = db.session.query(RoomUser).filter_by(uid=uid).first()
    if room_users:
        db.session.query(RoomUser).filter_by(uid=uid).delete()
        db.session.commit()
        emit('user-left-room', {
            "sid":sid,
            "uid": uid,
            "username": username,
            "room_id": room_users.room_id
        }, room=room_users.room_id)
        
        # 刷新房间用户列表
        emit('room-users-updated', {
            "room_id": room_users.room_id,
            "users": get_room_users(room_users.room_id)
        }, room=room_users.room_id)

    current_app.logger.info(f"用户断开连接 SID: {sid} UID: {uid}")
   
    # 发送断开连接通知
    emit('user-disconnect', {
        "sid":sid,
        "uid": uid,
        "username": username
    }, broadcast = True)
    # 从 user_sessions 中移除该用户会话

    remove_user_from_user_sessions(uid)
    
