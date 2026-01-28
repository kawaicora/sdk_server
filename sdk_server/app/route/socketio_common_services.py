
import threading
from app.route import bp
from flask import Request, jsonify, request, current_app
from app.extensions import socketio
from app.route.account_service import get_userinfo_by_sdk_token
from app.sql_class.Tables import GameAccount, Usermeta,Users
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


def write_user_sessions():
    global user_sessions
    with open("data/user_sessions.json","w",encoding='utf-8') as fp:
        json.dump(user_sessions,fp,ensure_ascii=False,indent=4)
def read_user_sessions():
    global user_sessions
    with open("data/user_sessions.json","r",encoding='utf-8') as fp:
        try:
            user_sessions = json.load(fp)
        except Exception as e:
            user_sessions = []
def write_rooms():
    global rooms
    with open("data/rooms.json","w",encoding='utf-8') as fp:
        json.dump(rooms,fp,ensure_ascii=False,indent=4)
def read_rooms():
    global rooms
    with open("data/rooms.json","r",encoding='utf-8') as fp:
        try:
            rooms = json.load(fp)
        except Exception as e:
            rooms = []


guest_counter = 900000000
# read_user_sessions()
# read_rooms()

def write_conf_loop():
    while True:
        time.sleep(5)
        write_rooms()
        write_user_sessions()
        


# ---------------------- 工具函数（用户相关） ----------------------
def get_user_info(request:Request):
    """从 Cookie 中获取已登录用户信息（uid 和 username）"""
    
    result = get_userinfo_by_sdk_token(request.cookies.get('sdk_token'))

    
    if result != None:
        return result.get("user_id"), result.get("display_name"),result.get("avatar")
    else:
        return gen_guest_user()
def gen_guest_user(uid = None):
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
    return uid,username,""


def sid_exists(sid):
    """检查 sid 是否存在于 user_sessions 中"""
    return any(session["sid"] == sid for session in user_sessions)


def get_user_by_sid(sid):
    """根据 sid 获取完整的用户会话信息"""
    for session in user_sessions:
        if session["sid"] == sid:
            return session
    return None


def get_user_by_uid(uid):
    """根据 uid 获取用户会话信息（可能有多个 sid，返回第一个）"""
    for session in user_sessions:
        if session["uid"] == uid:
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
        if session["uid"] == uid:
            session["sid"] = sid
            break  # 找到用户后立即退出循环

def get_room_by_uid(uid):
    for room in rooms:
        for t_user in room.get("users"):
            if t_user.get('uid') == uid:
                return room
    return None

def get_room_by_sid(sid):
    for room in rooms:
        for t_user in room.get("users"):
            c_user = get_user_by_uid(t_user.get('uid')) 
            if c_user.get('sid') == sid:
                return room
    return None



# ---------------------- 工具函数（房间相关） ----------------------
def get_room_by_id(room_id):
    """根据 room_id 获取房间完整信息"""
    for room in rooms:
        if room["room_id"] == room_id:
            return room
    return None


def room_exists(room_id):
    """检查房间是否存在"""
    return get_room_by_id(room_id) is not None


def is_user_in_room(uid, room_id):
    """检查用户是否在指定房间内"""
    room = get_room_by_id(room_id)
    if not room:
        return False
    return any(user["uid"] == uid for user in room["users"])


def add_user_to_room(uid, room_id):
    """将用户添加到房间的 users 列表（记录加入时间）"""
    room = get_room_by_id(room_id)
    if not room:
        return False
    # 避免重复添加
    if is_user_in_room(uid, room_id):
        return True
    room["users"].append({
        "uid": uid,
        "join_time": int(datetime.now().timestamp()) # 假设存在获取当前时间戳的工具函数
    })
    return True

def remove_user_from_room(room_id, uid=None, sid=None):
    """将用户从房间的 users 列表中移除"""
    # 参数校验
    if uid is None and sid is None:
        raise ValueError("至少需要提供 uid 或 sid 其中一个参数")
    if uid is not None and sid is not None:
        raise ValueError("只能提供 uid 或 sid 其中一个参数")
    
    room = get_room_by_id(room_id)
    if not room:
        return False
    
    if uid is not None:
        room["users"] = [user for user in room["users"] if user["uid"] != uid]
    else:
        room["users"] = [user for user in room["users"] if user["sid"] != sid]
    
    return True



def remove_user_from_user_sessions( uid=None, sid=None):
    """将用户从user_sessions  列表中移除"""
    global user_sessions  # 声明使用全局变量
    # 参数校验
    if uid is None and sid is None:
        raise ValueError("至少需要提供 uid 或 sid 其中一个参数")
    if uid is not None and sid is not None:
        raise ValueError("只能提供 uid 或 sid 其中一个参数")
    
    
    if uid is not None:
        user_sessions = [user_session for user_session in user_sessions if user_session["uid"] != uid]
    else:
        user_sessions = [user_session for user_session in user_sessions if user_session["sid"] != sid]
    
    return True



def get_room_users(room_id):
    """获取房间内所有用户的详细信息（结合 user_sessions）"""
    room = get_room_by_id(room_id)
    if not room:
        return []
    # 从 user_sessions 中查询每个 uid 对应的用户详情
    room_user_details = []
    for user in room["users"]:
        user_session = get_user_by_uid(user["uid"])
        if user_session:
            room_user_details.append({
                "uid": user["uid"],
                "sid": user_session["sid"],
                "username": user_session["username"],
                "avatar": user_session.get("avatar", ""),
                "join_time": user["join_time"]
            })
    return room_user_details


def is_user_banned(uid, room_id):
    """检查用户是否被禁止进入房间"""
    room = get_room_by_id(room_id)
    if not room:
        return False
    return any(ban["uid"] == uid for ban in room["ban_users"])


def title_exists(title):
    """检查是否存在相同标题的房间（不区分大小写）"""
    return any(r["title"].lower() == title.lower() for r in rooms)

# ---------------------- Socket.IO 事件处理 ----------------------


@socketio.on('get-current-sid')
def handle_get_sid():
    """获取SID"""
    emit("current-sid",{'sid':request.sid})

@socketio.on('user-register')
def handle_register_user(*args):
    """用户注册（建立连接时初始化会话信息）"""
    global guest_counter
    global write_config_thread
    sid = request.sid
    
    # 若已注册则跳过（避免重复添加）
    if sid_exists(sid):
        return
    ########################################
    if not write_config_thread:
        write_config_thread = threading.Thread(target=write_conf_loop)
        write_config_thread.daemon = True
        write_config_thread.start()
    ######################################
    
    # 处理客户端传入的 username 参数（兼容无参数、None、空字符串）
    compulsory_username = ''
    if args:  # 简化判断：args 非空即表示有传入参数
        data = args[0]
        # 安全获取 username：仅当 data 是字典且 username 有效时赋值
        if isinstance(data, dict):
            # 正确逻辑：username 不为 None 且 不为空字符串（去空格后）
            uid = data.get('uid', '')  # 默认为空字符串
            token = data.get('token','')
            if uid == "" or uid == None or token == "" or token == None:
                current_app.logger.info("参数错误")
                emit('error', {"event": "user-register", "msg": "参数错误"}, sid=sid)
                return
            t_game_account = GameAccount.query.filter_by(ID=uid).first()
            if not t_game_account:
                current_app.logger.info("用户不存在")
                emit('error', {"event": "user-register", "msg": "用户不存在"}, sid=sid)
                return
            if t_game_account.token  != token:
                current_app.logger.info("TOKEN 错误")
                emit('error', {"event": "user-register", "msg": "TOKEN 错误"}, sid=sid)
                return
            
            user:Users = Users.query.filter_by(ID=uid).first()
            user_meta_list:Usermeta = Usermeta.query.filter_by(user_id=user.ID).all()
            user_meta = {}
            for meta in user_meta_list:
                
                user_meta[meta.meta_key] = meta.meta_value

            username = user.display_name
            avatar = user_meta.get('user_avatar', "")

    else :

        # 获取用户信息（已登录用户用真实 uid，游客生成临时 uid）
        uid, username,avatar = get_user_info(request)
        if compulsory_username:
            # 若客户端传入有效 username，直接使用
            username = compulsory_username

    t_user = get_room_by_uid(uid)
    current_app.logger.info(f"根据用户获取房间 - SID: {sid}, UID: {uid}, 用户名: {username}")
    if t_user:
        current_app.logger.info(f"用户存在,更新SID-UID关系- SID: {sid}, UID: {uid}, 用户名: {username}")
        update_sid_by_uid(uid,sid)
        current_app.logger.info(f"用户存在,退出房间- SID: {sid}, UID: {uid}, 用户名: {username}")
        remove_user_from_room(t_user.get("room_id"),uid=uid)
        
    else:
    # 添加到 user_sessions（仅存储用户自身信息，无房间字段）
        current_app.logger.info(f"没有找到,添加用户 - SID: {sid}, UID: {uid}, 用户名: {username}")
        user_sessions.append({
            "sid": sid,
            "uid": uid,
            "username": username,
            "avatar": avatar or ""  # 新增头像支持
        })
        
    # 通知客户端注册成功
    emit('user-registered', {
        "sid": sid,
        "uid": uid,
        "username": username,
        "avatar":avatar or ""
    })
    emit('room-list-updated', get_room_list(), broadcast=True)
    current_app.logger.info(f"用户注册 - SID: {sid}, UID: {uid}, 用户名: {username}")



    
@socketio.on('user-unregister')
def handle_unregister_user():
    """用户断开连接（清理会话信息）"""
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user:
        return
    
    uid = user["uid"]
    username = user["username"]
    current_app.logger.info(f"用户断开连接 - SID: {sid}, UID: {uid}, 用户名: {username}")
    
    # 从所有房间中移除该用户
    for room in rooms:
        if is_user_in_room(uid, room["room_id"]):
            remove_user_from_room(uid = uid,room_id= room["room_id"])
            # 通知房间内其他用户该用户离开
            emit('user-left-room', {
                "sid": sid,
                "uid": uid,
                "username": username,
                "room_id": room["room_id"]
            }, room=room["room_id"])
            # 刷新房间用户列表
            emit('room-users-updated', {
                "room_id": room["room_id"],
                "users": get_room_users(room["room_id"])
            }, room=room["room_id"])
    
    # 从 user_sessions 中移除该用户
    global user_sessions
    user_sessions = [s for s in user_sessions if s["sid"]!= sid]
    
    # 刷新房间列表（若房间为空则删除）
    emit('room-list-updated', get_room_list())

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
        emit('error', {"event": "create-room", "msg": "用户未注册"}, sid=sid)
        return
    
    uid = user["uid"]
    username = user["username"]
    room_id = data.get("room_id")

    room = get_room_by_id(room_id=room_id)
    if not room:
        current_app.logger.info(f"删除房间失败:房间{room_id}不存在")
        return
    
    for t_user in room.get("users"):
        c_user = get_user_by_uid(t_user.get('uid'))
        emit('user-left-room', {
            "sid": c_user.get('sid'),
            "uid": c_user.get('uid'),
            "username": c_user.get('username'),
            "room_id": room["room_id"]
        }, room=room["room_id"])

    rooms.remove(room)
    # 通知客户端创建成功
    emit('room-deleted', {
        "room_id": room_id,
        "title": room.get('title'),
        "sid":sid,
        "uid":uid,
        "username":username
    }, sid=sid)
    
    # 广播房间列表更新
    emit('room-list-updated', get_room_list(), broadcast=True)
    current_app.logger.info(f"房间删除 - 房间ID: {room_id}, 标题: {room.get('title')}")




@socketio.on('create-room')
def handle_create_room(data):
    """创建房间"""
    sid = request.sid
    user = get_user_by_sid(sid)
    if not user:
        emit('error', {"event": "create-room", "msg": "用户未注册"}, sid=sid)
        return
    
    uid = user["uid"]
    room_id = data.get("room_id")
    title = data.get("title", "未命名房间")
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
    
    # 创建新房间
    new_room = {
        "room_id": room_id,
        "title": title,
        "desc": desc,
        "create_time": int(datetime.now().timestamp()),
        "updated_time": None,
        "deleted_time": None,
        "cover": cover,
        "users": [],
        "ban_users": [],
        "creator": uid,
        "room_type":room_type
    }
    rooms.append(new_room)
    
    # 通知客户端创建成功
    emit('room-created', {
        "room_id": room_id,
        "room_info": new_room,
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
        return
    
    uid = user["uid"]
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
        "username": user["username"],
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
        "username": user["username"]
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
        return
    
    uid = user["uid"]
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
        "username": user["username"],
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
    return [
        {
            "room_id": room["room_id"],
            "title": room["title"],
            "cover": room["cover"],
            "room_type":room["room_type"],
            "user_count": len(room["users"]),  # 房间人数
            "create_time": room["create_time"]

        } for room in rooms
    ]


@socketio.on('disconnect')
def handle_disconnect():
    global user_sessions
    sid = request.sid
    
    # 查找该 sid 对应的 uid（如果存在）
    user = get_user_by_sid(sid)
    if not user:
        return  # 未找到关联会话，可能是无效连接
    
    uid = user.get("uid")
    username = user.get("username")
    room = get_room_by_uid(uid)
    current_app.logger.info(f"用户断开连接 SID: {sid} UID: {uid}")
    if room :
        success = remove_user_from_room(uid = uid,room_id=room.get("room_id"))
        
        if success == False:
            current_app.logger.warnning(f"从 房间{str(room.get('room_id'))} 移除用户: {uid} SID: {user.get("sid")} USERNAME: {username} 失败  ")
        # 通知房间内其他用户该用户离开
        emit('user-left-room', {
            "sid":sid,
            "uid": uid,
            "username": username,
            "room_id": room["room_id"]
        }, room=room["room_id"])
        
        # 刷新房间用户列表
        emit('room-users-updated', {
            "room_id": room["room_id"],
            "users": get_room_users(room["room_id"])
        }, room=room["room_id"])
    
    # 发送断开连接通知
    emit('user-disconnect', {
        "sid":sid,
        "uid": uid,
        "username": username
    }, broadcast = True)
    # 从 user_sessions 中移除该用户会话

    remove_user_from_user_sessions(uid)
    
