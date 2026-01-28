import urllib
from datetime import datetime
import time
import json
import threading
from flask import Response, request, current_app
import requests
from app.extensions import set_cookies
from app.sql_class.Tables import Users
from app.sql_class.Tables import Usermeta

from app.utils.CommonUtils import CommonUtils
from app.utils.ErrorCode import *
from app.extensions import db
from app.route import bp
from app.settings import DefaultConfig
import urllib3
import hmac
import hashlib
from datetime import datetime
from flask import Response, request, current_app,Request
from app.sql_class.Tables import Users, Usermeta, Options,GameAccount
from app.utils.ErrorCode import *  # 假设已定义错误码
import re
import base64


# 禁用警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
ticket_cache_data = {}
userinfo = {}
# 用于存储已使用的UID
used_uids = set()

def generate_unique_uid():
    """生成唯一的UID"""
    while True:
        # 生成8位随机数字UID
        uid = CommonUtils.gen_random_str(8, number_only=True)
        # 检查是否已存在于数据库
        if not Users.query.filter_by(ID=uid).first() and uid not in used_uids:
            used_uids.add(uid)
            return uid

def ticker_cache_data_auto_clear():
    while True:
        try:
            for k,v in ticket_cache_data.items():
                if v["time_sec"] <= 0:
                    data = ticket_cache_data.pop(k)
                    # current_app.logger.info(f"clear ticket:{k} data:{data}")
                else:
                    v["time_sec"] -= 1
        except Exception as e:
            pass
        time.sleep(1)

threading.Thread(target=ticker_cache_data_auto_clear).start()













def get_wordpress_logged_in_cookie_key():
    """
    动态获取 WordPress 登录 Cookie 键名（对齐 wp_cookie_constants 逻辑）
    键名格式：wordpress_logged_in_<COOKIEHASH>，COOKIEHASH = md5(siteurl)
    """
    try:
        # 从 moe_options 表查询 siteurl（WordPress 核心配置）
        siteurl_option = Options.query.filter_by(option_name='siteurl').first()
        if not siteurl_option or not siteurl_option.option_value:
            current_app.logger.error("WordPress siteurl 配置缺失（moe_options 表无 siteurl 记录）")
            return None
        
        siteurl = siteurl_option.option_value.strip()
        cookie_hash = hashlib.md5(siteurl.encode('utf-8')).hexdigest()
        return f'wordpress_logged_in_{cookie_hash}'
    
    except Exception as e:
        current_app.logger.error(f"获取登录 Cookie 键名失败: {str(e)}")
        return None


def extract_pass_frag(user_pass):
    """
    提取用户密码哈希片段（对齐 wp_generate_auth_cookie 逻辑）
    :param user_pass: 数据库中存储的用户密码哈希（如 $wp$2y$12$...）
    :return: 4位密码片段
    """
    if user_pass.startswith(('$P$', '$2y$')):
        # 对应 PHP：substr($user->user_pass, 8, 4)
        # $P$: phpass 哈希；$2y$: bcrypt 哈希
        return user_pass[8:12]  # Python 切片 [8:12] 对应 PHP substr(8,4)
    else:
        # 对应 PHP：substr($user->user_pass, -4)
        return user_pass[-4:]


def wp_salt(scheme='logged_in'):
    """
    实现 WordPress wp_salt 函数逻辑（返回对应 scheme 的盐值）
    参考：wp-includes/pluggable.php -> wp_salt()
    """
    if scheme == 'logged_in':
        return DefaultConfig.LOGGED_IN_SALT_COMBINED  # LOGGED_IN_KEY + LOGGED_IN_SALT
    # 其他 scheme 可扩展（如 'auth'/'secure_auth'），此处仅需登录验证的 'logged_in'
    return ''

def parse_php_session_tokens(php_serialized_str):
    """
    健壮的PHP序列化解析函数
    """
    try:
        session_tokens = {}
        
        # 方法1：精确匹配（针对您提供的格式）
        pattern1 = r's:64:"([a-f0-9]{64})";a:4:\{s:10:"expiration";i:(\d+);s:2:"ip";s:\d+:"([^"]*)";s:2:"ua";s:\d+:"([^"]*)";s:5:"login";i:(\d+);\}'
        matches1 = re.findall(pattern1, php_serialized_str)
        
        if matches1:

            for token, expiration, ip, ua, login in matches1:
                session_tokens[token] = {
                    'expiration': int(expiration),
                    'ip': ip,
                    'ua': ua,
                    'login': int(login)
                }
            return session_tokens
        
        # 方法2：更通用的匹配（如果格式有微小变化）
        pattern2 = r's:64:"([a-f0-9]{64})";a:\d+:\{(.*?)\}'
        matches2 = re.findall(pattern2, php_serialized_str)
        
        if matches2:
            for token, content in matches2:
                session_data = {}
                
                # 提取各个字段
                exp_match = re.search(r's:10:"expiration";i:(\d+);', content)
                ip_match = re.search(r's:2:"ip";s:\d+:"([^"]*)";', content)
                ua_match = re.search(r's:2:"ua";s:\d+:"([^"]*)";', content)
                login_match = re.search(r's:5:"login";i:(\d+);', content)
                
                if exp_match:
                    session_data['expiration'] = int(exp_match.group(1))
                if ip_match:
                    session_data['ip'] = ip_match.group(1)
                if ua_match:
                    session_data['ua'] = ua_match.group(1)
                if login_match:
                    session_data['login'] = int(login_match.group(1))
                
                session_tokens[token] = session_data
            
            return session_tokens
        
        current_app.logger.warning("无法解析session_tokens数据")
        return None
        
    except Exception as e:
        current_app.logger.error(f"解析 session_tokens 失败: {str(e)}", exc_info=True)
        return None



def get_userinfo_by_sdk_token(sdk_token:str):
    return userinfo.get(sdk_token )

# 第三方验证登录

def third_login(data):
    req_data = {
        "app_id":data.get('app_id'),
        "token":DefaultConfig.SAKURAXY_OAUTH_TOKEN,
        "login_token":data.get("decrypted_login_token")
    }
    try:
        
        rsp = requests.post(DefaultConfig.SAKURAXY_OAUTH_API,data=req_data)
        if rsp.status_code != 200:
            current_app.logger.warning(f"请求第三方API获取用户信息失败! 请求失败{str(rsp.status_code)}")
            return get_response_json(code = -1,msg=f"请求第三方API获取用户信息失败! 请求失败{str(rsp.status_code)}")
        response_json = rsp.json()
        if response_json.get("retcode") != 0:
            current_app.logger.warning(f"请求第三方API返回错误! {json.dumps(response_json,indent=4,ensure_ascii=False)}")
            return get_response_json(code = -1,msg=f"请求第三方API返回错误! {json.dumps(response_json,indent=4,ensure_ascii=False)}")
    except Exception as e:
        current_app.logger.warning(f"请求第三方API返回错误! 非json格式内容:{str(e)}")
        return get_response_json(code = -1,msg=f"请求第三方API返回错误! 非json格式内容:{str(e)}")
    
    
    return response_json

# 本站登录
def site_login(cookies,verify_siteurl=True):
    #利用cookies验证用户登陆情况
    try:
        # --------------------------
        # 1. 动态获取 WordPress 登录 Cookie 键名
        # --------------------------
        logged_in_cookie_key = get_wordpress_logged_in_cookie_key()
        if not logged_in_cookie_key:
            return get_response_json(
                    code=-5000
                )

        # --------------------------
        # 2. 提取并解析登录 Cookie（核心修正：对齐 wp_parse_auth_cookie 逻辑）
        # --------------------------
       
        if not verify_siteurl :
            logged_in_cookie_key = "wordpress_logged_"
            for cookie_key in cookies.keys():
                if cookie_key.startswith(logged_in_cookie_key):
                    logged_in_cookie_key = cookie_key  # 赋值完整的Cookie键
                    break  # 找到第一个即退出（如果有多个，取第一个）
          
        if logged_in_cookie_key not in cookies:
            return get_response_json(
                code=-3041
            )
        scheme_key = logged_in_cookie_key[logged_in_cookie_key.find("_",0)+1:]
        scheme_key = scheme_key[:scheme_key.rfind("_")]
        # 解析 Cookie 值：格式为 "username|expiration|token|hmac"（4部分，|分割）
        cookie_value = cookies[logged_in_cookie_key]
        cookie_value = cookie_value.replace("%7C","|")
        cookie_elements = cookie_value.split('|')
        if len(cookie_elements) != 4:
            current_app.logger.warning(f"Cookie格式错误：{cookie_value}")
            return get_response_json(
                code=-3040
            )
        # 正确顺序：username | expiration | token | hmac（对应 wp_parse_auth_cookie 返回值）
        username = cookie_elements[0].strip()
        expiration_str = cookie_elements[1].strip()
        cookie_token = cookie_elements[2].strip()
        cookie_hmac = cookie_elements[3].strip()

        # 校验 expiration 为数字
        if not expiration_str.isdigit():
            return get_response_json(
                code=-3040
            )
        expiration = int(expiration_str)
        current_ts = int(time.time())

        # --------------------------
        # 3. 检查 Cookie 是否过期（含 POST/AJAX 宽限期）
        # --------------------------
        expired = expiration
        # 对应 PHP：if (wp_doing_ajax() || 'POST' === $_SERVER['REQUEST_METHOD']) $expired += HOUR_IN_SECONDS;
        if request.method == 'POST' or 'ajax' in request.path.lower():
            expired += 3600  # 宽限期 1 小时（3600 秒）
        
        if expired < current_ts:
            current_app.logger.warning(f"Cookie已过期：用户{username}，过期时间{datetime.fromtimestamp(expiration)}")
            return get_response_json(
                code=-3020
            )

        # --------------------------
        # 4. 查询用户信息及密码哈希（用于生成签名密钥）
        # --------------------------
        user = Users.query.filter_by(user_login=username).first()
        if not user:
            current_app.logger.warning(f"Cookie中的用户不存在：{username}")
            return get_response_json(
                code=-3010
            )
        user_id = user.ID
        user_pass = user.user_pass  # 数据库中的密码哈希（如 $wp$2y$12$...）

        # --------------------------
        # 5. 生成 HMAC 签名并验证（核心修正：对齐 wp_validate_auth_cookie 逻辑）
        # --------------------------
        # 步骤1：提取密码片段 pass_frag（对应 PHP $pass_frag 变量）
        pass_frag = extract_pass_frag(user_pass)
        if not pass_frag:
            current_app.logger.error(f"提取用户密码片段失败：用户{username}，密码哈希{user_pass}")
            return get_response_json(
                code=-3055
            )

        # 步骤2：生成中间密钥 key（对应 PHP $key = wp_hash(...)）
        # 格式：username|pass_frag|expiration|token
        wp_hash_data = f"{username}|{pass_frag}|{expiration}|{cookie_token}"

        key = hmac.new(wp_salt(scheme_key).encode('utf-8'), wp_hash_data.encode('utf-8'), 'md5').hexdigest()   # 用 logged_in  scheme 的盐值
        if not key:
            current_app.logger.error(f"生成 wp_hash 密钥失败：{wp_hash_data}")
            return get_response_json(
                code=-3090
            )

        # 步骤3：生成 HMAC 签名（对应 PHP $hash = hash_hmac(...)）
        # 格式：username|expiration|token
        hmac_data = f"{username}|{expiration}|{cookie_token}"
        valid_hmac = hmac.new(
            key.encode('utf-8'),
            hmac_data.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # 步骤4：校验签名（对应 PHP hash_equals($hash, $hmac)）
        if not hmac.compare_digest(valid_hmac, cookie_hmac):
            current_app.logger.warning(
                f"Cookie签名校验失败：用户{username}，IP{request.remote_addr}，"
                f"预期HMAC{valid_hmac[:10]}...，实际HMAC{cookie_hmac[:10]}..."
            )
            return get_response_json(
                code=-3005
            )

        # --------------------------
        # 6. 校验会话 Token 有效性（数据库层面，对应 WP_Session_Tokens::verify）
        # --------------------------
        session_meta = Usermeta.query.filter_by(
            user_id=user_id,
            meta_key='session_tokens'
        ).first()
        if not session_meta or not session_meta.meta_value:
            return get_response_json(
                code=-3017
            )
        # 进行HMAC-SHA256哈希
     
        hashed_token = hashlib.sha256(cookie_token.encode('utf-8')).hexdigest()
        
        current_app.logger.debug(f"Token验证哈希: {cookie_token} -> {hashed_token}")
        
        current_app.logger.debug(f"Token转换: {cookie_token} -> {hashed_token}")
        # 解析 session_tokens（PHP 序列化格式）
        session_tokens = parse_php_session_tokens(session_meta.meta_value)
        # 在token验证失败的部分添加：
        if not session_tokens or hashed_token not in session_tokens:
            current_app.logger.warning(
                f"会话Token不存在：用户{username}，Token{cookie_token[:10]},hashed_token:{hashed_token}...，"
                f"可用Tokens: {list(session_tokens.keys())[:3] if session_tokens else '无'}"
            )
            
            # 调试：打印session_tokens的结构
            if session_tokens:
                current_app.logger.debug(f"Session tokens结构: {str(session_tokens)[:500]}")
            
            return get_response_json(
                code=-3019
            )

        # 校验数据库中的会话是否过期（双重校验）
        session_data = session_tokens[hashed_token]
        if session_data.get('expiration', 0) < current_ts:
            current_app.logger.warning(f"数据库会话已过期：用户{username}")
            return get_response_json(
                code=-3016
            )
        # --------------------------
        # 7. （可选）增强校验：IP + 用户代理（UA）匹配（防会话劫持）
        # --------------------------
        client_ip = request.remote_addr
        client_ua = request.user_agent.string
     

        # --------------------------
        # 8. 获取用户扩展元数据（昵称、头像等）
        # --------------------------
        user_meta_list = Usermeta.query.filter_by(user_id=user_id).all()
        user_meta = {}
        for meta in user_meta_list:
            
            user_meta[meta.meta_key] = meta.meta_value

        # --------------------------
        # 9. 构造最终响应数据
        # --------------------------
        user_data = {
            "user_id": user_id,
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
        return get_response_json(
            code=0,
            data=user_data
        )

    except Exception as e:
        current_app.logger.error(f"获取用户信息异常: {str(e)}", exc_info=True)
        return get_response_json(
            code=-1
        )



def verify_login(request:Request,verify_siteurl=True):
    cookies = request.cookies
    try:
        request_json = request.get_json()
        encrypted_login_token = request_json.get("encrypted_login_token" or None)
        app_id = request_json.get("app_id" or None)
    except Exception as e:
        result_site = site_login(cookies=cookies,verify_siteurl=verify_siteurl) 
        return result_site
    if encrypted_login_token != None and encrypted_login_token != '':
        from cryptography.hazmat.primitives import serialization, hashes
        decrypted_login_token =  CommonUtils.rsa_decrypt(base64.b64decode(encrypted_login_token),CommonUtils.load_private_key(DefaultConfig.SAKURAXY_LOGIN_PRIVATE_KEY),padding_scheme='OAEP',oaep_hash_alg=hashes.SHA1,  # 匹配加密端的哈希算法（优先试 SHA-1）
        oaep_mgf_hash_alg=hashes.SHA1  ).decode()

        data = {'app_id':app_id,'decrypted_login_token':decrypted_login_token}
        result_third = third_login(data)
        return result_third
    else:
        result_site = site_login(cookies=cookies,verify_siteurl=verify_siteurl) 
        return result_site


################################   ROUTE   ###########################################



@bp.route("/api/send_verify_code",methods=["POST"])
def api_send_verify_code():
    ticket = CommonUtils.gen_ticket("send_verify_code")

    email = request.json.get("email")
    if not email:
        return Response(json.dumps({"retcode": -3023,"msg":ErrorCode[-3023]}),status=200,content_type="application/json")
    verify_data = CommonUtils.send_verify_code(email)
    verify_data["time_sec"] = 1800
    verify_data["email"]    = email
    ticket_cache_data[ticket] = verify_data
    if not verify_data['verify_code']:
        return Response(json.dumps({"retcode": -3023,"msg":ErrorCode[-3023]}),status=200,content_type="application/json")
    
    CommonUtils.format_json_log(current_app.logger.info,verify_data)
    ticket_cache_data[ticket] = verify_data
    response = Response(json.dumps({"retcode":0,"msg":"验证码发送成功有效时间30分钟!"}),status=200,content_type="application/json")
    response.headers["X-Ticket"] = ticket
    return response

# @bp.route("/api/register",methods=["POST"])

# def api_register():
#     account = request.json.get("account")
#     password = request.json.get("password")
#     avatar_url = request.json.get("avatar_url")
#     username = request.json.get("username")
#     phone_number = request.json.get("phone_number")
#     verify_code = request.json.get("verify_code")
#     ticket = request.headers.get("X-Ticket")
#     ticket_data = ticket_cache_data.get(ticket)
#     if not ticket_data:
#         return Response(get_response_string(-3026),status=200,content_type="application/json")
#     if not account or not password or not verify_code:
#         return Response(get_response_string(-3002),status=200,content_type="application/json")

#     isencrypted = request.json.get("is_encrypt")
#     if isencrypted == True:
#         private_pem,public_pem = CommonUtils.get_exist_rsa_key()
#         private_key = CommonUtils.load_private_key(private_pem)
#         if not private_key:
#             return Response(get_response_string(-3005),status=400,content_type="application/json")
#         # password = private_key.decrypt(base64.b64decode(password),padding.PKCS1v15()).decode()
#         try:
#             password = CommonUtils.rsa_decrypt_chunks(base64.b64decode(password),private_key).decode()
#         except Exception as e:
#             return Response(get_response_string(-3001),status=400,content_type="application/json")
#     else:
#         password = password

#     user = Account.query.filter_by(account=account).first()
#     if user: 
#         # 用户已存在
#         return Response(get_response_string(-3011),status=200,content_type="application/json")
#     user = Account.query.filter_by(username=username).first()
    
#     if user:
#         return Response(get_response_string(-3011,"用户名重复!"),status=200,content_type="application/json")
    
#     if verify_code != ticket_data["verify_code"]: 
#         # 验证码错误
#         return Response(get_response_string(-3024),status=200,content_type="application/json")
    

#     token = CommonUtils.random_string()

#     # 生成用户
#     try:
#         user = Account(
#             account=account,
#             password_hash=CommonUtils.create_sha_passwd(password),
#             username=username,
#             avatar=avatar_url,
#             phone_number=phone_number,
#             email=ticket_data["email"],
#             login_token=token,
#             created_at=datetime.now(),
#             updated_at=datetime.now()
#         )
#         db.session.add(user)
#         db.session.commit()
#     except Exception as e:
#         current_app.logger.error(f"register error:{e}")
#         return Response(get_response_string(-3003),status=200,content_type="application/json")
#     # 注册成功
#     user = Account.query.filter_by(account=account).first()
#     cookies = {
#         # "uid":user.id,
#         # "token": user.login_token
#     }
#     headers = {
#         'X-Organization': 'Nintendo'
#     }
#     ticket_cache_data.pop(ticket)
#     return set_cookies(Response(get_response_string(0), status=200, content_type="application/json",headers=headers),cookies )

@bp.route("/api/login",methods=["POST"])
def api_login():
    account = request.json.get("account")
    password = request.json.get("password")
    isencrypted = request.json.get("is_encrypt")
    if not account or not password:
        return Response(get_response_string(-3002),status=200,content_type="application/json")
    if isencrypted == True:
        private_pem,public_pem = CommonUtils.get_exist_rsa_key()
        private_key = CommonUtils.load_private_key(private_pem)
        if not private_key:
            return Response(get_response_string(-3001),status=400,content_type="application/json")
        try:
            password = CommonUtils.rsa_decrypt_chunks(base64.b64decode(password),private_key).decode()
        except Exception as e:
            return Response(get_response_string(-3001),status=400,content_type="application/json")
    user = Users.query.filter_by(user_login=account).first()
    if not user:
        current_app.logger.warning(f"Cookie中的用户不存在：{account}")
        return get_response_json(
            code=-3010
        )
  
    if not CommonUtils.wp_verify_password(password,user.user_pass):
        return Response(get_response_string(-3012),status=200,content_type="application/json")
    token = CommonUtils.random_string()
    t_game_account = GameAccount.query.filter_by(ID=user.ID).first()
    if not t_game_account:
        t_game_account = GameAccount(
            ID = user.ID,
            token = token
        )
        db.session.add(t_game_account)
    else:
        t_game_account.token = token
    db.session.commit()

    cookies = {
        "token": t_game_account.token,
    }
    headers = {
        'X-Organization': 'Nintendo'
    }
    user_meta_list = Usermeta.query.filter_by(user_id=user.ID).all()
    user_meta = {}
    for meta in user_meta_list:
        
        user_meta[meta.meta_key] = meta.meta_value

    # --------------------------
    # 9. 构造最终响应数据
    # --------------------------
    user_data = {
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
        "current_ip": "",
        "user_agent": ""
    }

    # 创建响应对象
    response = Response(get_response_string(code=0,data=user_data), status=200, content_type="application/json", headers=headers)

    # 设置持久化 cookie（30 天后过期）
    for key, value in cookies.items():
        response.set_cookie(
            key, 
            value=str(value),
            max_age=30 * 24 * 60 * 60,  # 30 天（秒）
            httponly=True,  # 防止 XSS
            secure=True,    # 仅通过 HTTPS 传输
            samesite='Lax'  # 防止 CSRF
        )

    return response
        
third_cookies = {}

@bp.route("/api/get_user_info", methods=["GET"])
def api_get_user_info():
    
    ticket = request.cookies.get("ticket")
    if not ticket or ticket not in ticket_cache_data:
        return Response(json.dumps({"retcode": -3001, "msg": ErrorCode[-3001]}), 
                      status=200, content_type="application/json")
    
    cache_data = ticket_cache_data[ticket]
    return Response(json.dumps({
        "retcode": 0,
        "data": {
            "uid": cache_data["uid"],
            "email": cache_data["email"]
        }
    }), status=200, content_type="application/json")

# @bp.route("/api/forget_password",methods=["POST"])
# def api_forget_password():
#     ticket = request.headers.get("X-Ticket")
#     private_pem,public_pem = CommonUtils.get_exist_rsa_key()

#     private_key = CommonUtils.load_private_key(private_pem)

#     if not private_key:
#         return Response(get_response_string(-3005),status=400,content_type="application/json")

#     account = request.json.get("account")
#     password = request.json.get("password")
#     isencrypted = request.json.get("is_encrypt")

#     verify_code = request.json.get("verify_code")
#     ticket_data = ticket_cache_data.get(ticket)
#     if not verify_code or not ticket_data:
#         return Response(get_response_string(-3002),status=400,content_type="application/json")
#     if verify_code != ticket_data["verify_code"]: 
#         # 验证码错误
#         return Response(get_response_string(-3024),status=200,content_type="application/json")

#     if isencrypted == True:
#         password = CommonUtils.rsa_decrypt_chunks(base64.b64decode(password),private_key).decode()
        
#     else:
#         password = password

#     if not account or not password:
#         return Response(get_response_string(-3002),status=200,content_type="application/json")

#     headers = {
#         'X-Organization': 'Nintendo',
#         "X-Ticket":ticket
#     }
#     user = Account.query.filter_by(account=account).first()
#     user.password_hash = CommonUtils.verify_sha_passwd(password)
#     user.updated_at = datetime.now()
#     db.session.commit()

#     return Response(get_response_string(0),status=200,content_type="application/json",headers=headers)



@bp.route("/api/get_password_public_key")
def api_get_public_key():
    ticket = CommonUtils.gen_ticket("login")
    private_pem,public_pem = CommonUtils.get_exist_rsa_key()

    current_app.logger.info(f"get_public_key ticket:{ticket}")
    headers = {
        'X-Organization': 'Nintendo',
        "X-Ticket":ticket
    }
    return Response(public_pem.decode(), status=200, content_type="text/plan",headers=headers)  




@bp.route("/api/v3/get_user_info",methods=['GET','POST'])
def api_v3_get_userinfo():

    result = verify_login(request,verify_siteurl=False)
    
    headers = {
        'X-Organization': 'Nintendo',
        
    }
   
    response =  Response(json.dumps(result), status=200, content_type="application/json",headers=headers)  
    
    if result.get("retcode") == 0:
        sdk_token = CommonUtils.gen_ticket("userinfo")
        userinfo[sdk_token] = result.get("data")
        set_cookies(response=response,cookies={"sdk_token":sdk_token})
    return response