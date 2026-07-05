# -*- coding: utf-8 -*-

from email.utils import formataddr
import hashlib
import asyncio
import os
import re
import string
import time
from typing import Any, Optional, Type, TypeVar, Coroutine
import base64
import secrets
from datetime import datetime
import hashlib
import json
from urllib.parse import quote, quote_plus,unquote,unquote_plus
import random
import bcrypt
import hmac
import smtplib
import uuid
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
from typing import Union, List
import math
from cryptography.hazmat.primitives.asymmetric import rsa,padding
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from app.utils.LoggerManager import logger
from jinja2 import Environment, FileSystemLoader
import rarfile
import zipfile
T = TypeVar("T")
class CommonUtils:
    @staticmethod
    def generate_uuid(is_upper=False):
        """生成全大写的UUID字符串（格式：8-4-4-4-12）"""
        # 生成随机UUID对象（UUID4是最常用的随机UUID类型）
        uuid_object = uuid.uuid4()
        # 转换为字符串并将所有字母转为大写
        if is_upper:
            upper_uuid = str(uuid_object).upper()
        return upper_uuid

    @staticmethod 
    def gen_ticket(info:str = ""):
        a = secrets.token_hex(8).encode()
        b = info.encode()
        c =  str(datetime.timestamp(datetime.now()) ).encode()
        d = a + b+c
        e = base64.b16encode(d).decode().lower()
       
        return e
    @staticmethod
    def gen_order_no():
        n = "JAF"
        for i in range(28):
            
            n=n+ str(random.randint(0,9))
        return n

    @staticmethod
    def get_suffix_by_mimetype(mimetype: str) -> str:
        # MIME 类型到文件扩展名的映射
        mimetype_to_extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/bmp": ".bmp",
            "image/webp": ".webp",
            "image/tiff": ".tiff",
            "image/vnd.microsoft.icon": ".ico",
            "image/svg+xml": ".svg",
        }
        # 返回对应的扩展名，如果未找到则返回空字符串
        return mimetype_to_extension.get(mimetype.lower(), "")
    @staticmethod
    def create_directory(path):
        """
        递归创建文件夹，如果文件夹已存在则不会报错。
        """
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            return False
    @staticmethod
    def calculate_md5(input_data, encoding='utf-8'):
        # 如果输入是字符串，则先编码为字节
        if isinstance(input_data, str):
            input_data = input_data.encode(encoding)
        
        # 使用Python的hashlib库计算MD5哈希
        md5_hash = hashlib.md5()
        md5_hash.update(input_data)
        
        # 返回十六进制表示的哈希值
        return md5_hash.hexdigest()
    @staticmethod
    def random_number(len=19):
        out = ""
        for i in range(len):
            out += str(random.randint(0,9))
        return out

    @staticmethod
    def sort_para_to_str(para:str|list,split_suffix = '&',ignore_empty_value:bool = True):
        if isinstance(para,str):
            para:dict = CommonUtils.para_to_dict(para,ignore_empty_value)
        tmp =  []
        for k,v in para.items():
            if (ignore_empty_value):
                if v != '':
                    tmp.append(f'{k}={quote(str(v))}')
            else:
                tmp.append(f'{k}={v}')

        a = sorted(tmp,reverse=False)

        return split_suffix.join(a)
    
    @staticmethod
    def random_string(len=64):
        chat_set = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ''.join(random.choices(chat_set, k=len))
    
    @staticmethod
    def para_to_dict(para:str,ignore_empty_value:bool = True):
        tmp = {}
        para_kv_list = para.split("&")
        for item in para_kv_list:
            if ignore_empty_value :
                if(item.split('=')[1] != ''):
                    tmp[item.split('=')[0]] = item.split('=')[1]
            else:
                tmp[item.split('=')[0]] = item.split('=')[1]
        return tmp
    @staticmethod
    def dict_to_params(data):
        """
        把字典转换为URL查询字符串格式，并且进行URL编码
        :param data: 原始字典
        :return: 转换后的URL查询字符串
        """
        # 用于存储转换后的键值对
        param_list = []
        # 遍历字典中的每个键值对
        for key, value in data.items():
            # 如果值是字典或者列表，就先转成JSON字符串
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            # 把键和值进行URL编码，然后添加到列表中
            param_list.append(f"{quote(str(key))}={quote(str(value))}")
        # 用&符号连接所有键值对
        return '&'.join(param_list)
    @staticmethod
    def cookies_str_to_dict (cookies_str:str)->dict:
        # 将cookies字符串分割成独立的键值对
        cookie_pairs = cookies_str.split(';')

        # 创建一个字典来存储cookies
        cookies_dict = {}
        for pair in cookie_pairs:
            # 去除空格并分割键和值
            key, value = pair.strip().split('=', 1)
            # 如果值是URL编码的，则进行解码
            value = unquote(value)
            # 将键值对添加到字典中
            cookies_dict[key] = value

        return cookies_dict
    @staticmethod
    def cookies_dict_to_str (cookies_dict:dict)->str:
        kv_list = []
        for key,value in cookies_dict.items():
            kv = []
            if not value:
                value = ""
            if isinstance(value, bool):
                value = str(value).lower()
            if isinstance(value, int):
                value = str(value)
            kv.append(key)
            kv.append(value)
            kv_list.append("=".join(kv)) 
        kv_str = ";".join(kv_list)
        return kv_str
    



    # 辅助函数
    @staticmethod
    def quote_special_chars(s):
        # 简化的urlencode实现
        return s.replace(' ', '+').replace('&', '%26').replace('=', '%3D')
    @staticmethod
    def generate_random_id(prefix):
        # 生成随机字符串，类似Lua的randDataID
        characters = string.ascii_letters + string.digits
        random_part = ''.join(random.choice(characters) for i in range(10))
        return f"{prefix}{random_part}"
    @staticmethod
    def calc_cloud_sign_suffix(origin_data, secret_key, urlencode=False):
        # 按key排序
        sorted_data = sorted(origin_data, key=lambda x: x['key'])
        
        # 拼接参数
        origin = ""
        value_str = ""
        for item in sorted_data:
            if item and 'key' in item and 'value' in item and \
            len(item['key']) > 0 and len(item['value']) > 0:
                key = item['key']
                value = item['value']
                if urlencode:
                    # 简化的urlencode实现，实际使用中建议用urllib.parse.quote
                    value = CommonUtils.quote_special_chars(value)
                origin += f"{key}={value}&"
                value_str += value
        
        # 移除最后一个&
        if origin.endswith('&'):
            origin = origin[:-1]
        
        rqtime = int(time.time())
        rqrandom = CommonUtils.generate_random_id("Box")
        value_str += f"{secret_key}{rqtime}{rqrandom}"
        logger.info(f"isCloudLogin : RequestIsCloudLogin {value_str}")
        
        # 计算MD5签名
        sign_md5 = hashlib.md5(value_str.encode('utf-8')).hexdigest()
        
        # 构建结果字典
        result = {item['key']: item['value'] for item in origin_data}
        result.update({
            'rqtime': rqtime,
            'rqrandom': rqrandom,
            'sign': sign_md5
        })
        return result
    @staticmethod
    def verify_cloud_sign(params, secret_key):
        # 提取签名和动态参数
        if 'sign' not in params or 'rqtime' not in params or 'rqrandom' not in params:
            return False
        
        original_sign = params.pop('sign')
        rqtime = params.pop('rqtime')
        rqrandom = params.pop('rqrandom')
        
        # 排序参数
        sorted_params = sorted(params.items(), key=lambda x: x[0])
        
        # 拼接值字符串
        value_str = ''.join([str(value) for _, value in sorted_params])
        value_str += f"{secret_key}{rqtime}{rqrandom}"
        
        # 计算验证签名
        expected_sign = hashlib.md5(value_str.encode('utf-8')).hexdigest()
        
        return original_sign == expected_sign


    @staticmethod 
    def process_json_only_string(input):
        # 使用列表推导式来遍历列表中的每个字典，并转换布尔值为字符串
        contents_as_strings = [
            {key: str(value).lower() if isinstance(value, bool) else str(value) for key, value in item.items()}
            for item in input
        ]

        # 打印结果
        return contents_as_strings
    def unzip_file(file_path, extract_path):
        try:
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_path)
                logger.info(f"成功解压 {file_path} 到 {extract_path}")
            elif file_path.endswith('.rar'):
                rf = rarfile.RarFile(file_path)
                rf.extractall(extract_path)
                logger.info(f"成功解压 {file_path} 到 {extract_path}")
            else:
                logger.info("不支持的压缩文件格式，请使用 ZIP 或 RAR 格式。")
        except Exception as e:
            logger.error(f"解压过程中出现错误: {e}")
    @staticmethod
    def get_time_of_day() -> str:
        # 获取当前时间
        current_time = datetime.now()
        # 获取当前小时数
        hour = current_time.hour

        # 根据小时数判断时间段
        if 5 <= hour < 10:
            return '早上'
        elif 10 <= hour < 12:
            return '上午'
        elif 12 < hour < 18:
            return '下午'
        elif 12 == hour:
            return '中午'
        else:
            return '晚上'   
    @staticmethod
    def format_json(json_data,ensure_ascii=False) ->str:
        """
        格式化JSON
        返回 展开的JSON字符串
        """
        return json.dumps(json_data, indent=2,ensure_ascii=ensure_ascii)
    @staticmethod
    def format_json_log(callback ,json_data:dict) ->None:
        """
        使用传入的方法打印展开的JSON
        """
        callback(CommonUtils.format_json(json_data))
    @staticmethod
    def hex_dump(callback,data, width=16) ->None:
        """
        打印16进制数据 类似于go的hex.dump
        """
        msg = ""
        for i in range(0, len(data), width):
            chunk = data[i:i + width]
            hex_str = ' '.join(f"{byte:02X}" for byte in chunk)
            printable = ''.join(chr(byte) if 32 <= byte < 127 else '.' for byte in chunk)
            # 计算需要的填充空格数量
            padding = ' ' * ((width - len(chunk)) * 3)
            msg += f"{hex_str} {padding} | {printable}\n"
        callback(f"\n\n{msg}\n\n")

    @staticmethod
    def gen_verify_code(len:int=6)->int:
        """
        生成指定长度的验证码
        """
        return ''.join(random.choices('0123456789', k=len))
    def send_verify_code(email:str,verify_url:str = ''):
        from app.settings import DefaultConfig
        # 创建 Jinja2 环境
        env = Environment(loader=FileSystemLoader("."))
 
        # 生成验证码
        verify_code = CommonUtils.gen_verify_code()
        # 加载模板文件
        template = env.get_template('templates/verify_code.html')
        # 定义要替换的变量
        data = {
            'verify_url': verify_url,
            'verify_code': verify_code
        }

        # 渲染模板
        output = template.render(data)

      
        CommonUtils.send_mail_exa(email,output)
        return data
    
    ##############################################################################################################
    @staticmethod 
    def send_mail_exa(receiver,html):
        from app.settings import DefaultConfig

        import resend
        
        resend.api_key = DefaultConfig.RESEND_API_KEY

        params: resend.Emails.SendParams = {
        "from": DefaultConfig.RESEND_MAIL,
        "to": [receiver],
        "subject": '这是你的验证码',
        "html": html
        }

        email = resend.Emails.send(params)
        
    @staticmethod
    def send_mail(
        smtp_server: str,
        port: int,
        username: str,
        password: str,
        sender: str,
        receiver: Union[str, List[str]],
        subject: str,
        body: str,
        subtype: str = "plain",
        encoding: str = "utf-8",
        cc: Union[str, List[str], None] = None,
        bcc: Union[str, List[str], None] = None,
        display_name: str = None,
        reply_to: str = None,
    ):
        """
        通用邮件发送方法，支持：
        - 单个或多个收件人
        - 抄送（cc）和密送（bcc）
        - 自定义显示名、Reply-To
        - HTML / 纯文本内容
        """
        COMMASPACE = "\\r\\n"
        # 1️⃣ 标准化收件人字段
        def normalize(addr):
            if not addr:
                return []
            if isinstance(addr, str):
                return [addr.strip()]
            return [a.strip() for a in addr if a]

        to_addrs = normalize(receiver)
        cc_addrs = normalize(cc)
        bcc_addrs = normalize(bcc)
        all_recipients = to_addrs + cc_addrs + bcc_addrs

        if not all_recipients:
            raise ValueError("收件人不能为空")

        # 2️⃣ 创建邮件对象（使用MIMEMultipart支持HTML）
        message = MIMEMultipart()
        message.attach(MIMEText(body, subtype, encoding))

        # 3️⃣ 基本头部
        display_from = (
            formataddr((str(Header(display_name, encoding)), sender))
            if display_name
            else sender
        )
        message["From"] = display_from
        message["To"] = COMMASPACE.join(to_addrs)
        if cc_addrs:
            message["Cc"] = COMMASPACE.join(cc_addrs)
        if reply_to:
            message.add_header("Reply-To", reply_to)
        message["Subject"] = Header(subject, encoding)

        # 4️⃣ 建立SMTP连接
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(smtp_server, port)
            else:
                server = smtplib.SMTP(smtp_server, port)
                if port == 587:
                    server.starttls()

            server.login(username, password)

            # 5️⃣ 发送邮件
            server.sendmail(sender, all_recipients, message.as_string())
        except smtplib.SMTPException as e:
            raise RuntimeError(f"邮件发送失败: {e}")
        finally:
            server.quit()
        
    ######################################################异步方法#############################################
    @staticmethod

    def __ensure_event_loop() -> None:
        try:
            asyncio.get_event_loop()

        except:
            asyncio.set_event_loop(asyncio.new_event_loop())

    @staticmethod
    def sync(coroutine: Coroutine[Any, Any, T]) -> T:
        """
        同步执行异步函数，使用可参考 [同步执行异步代码](https://nemo2011.github.io/bilibili-api/#/sync-executor)

        Args:
            coroutine (Coroutine): 异步函数

        Returns:
            该异步函数的返回值
        """
        CommonUtils.__ensure_event_loop()
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coroutine)
    ######################################################密码与验证#############################################
    @staticmethod
    def create_sha_passwd(string: str, mode: str = "$6$", salt: str = "96PyRRDpr81m794z") -> str:
        """
        生成安全的密码哈希（底层替换为 bcrypt，保持接口兼容）
        注：原有 mode/salt 参数仅为兼容旧调用，实际使用 bcrypt 自动生成盐值和可调难度
        :param string: 明文密码
        :param mode: 兼容旧参数（无实际作用）
        :param salt: 兼容旧参数（无实际作用）
        :return: bcrypt 格式的哈希字符串（utf-8 解码）
        """
        # 1. 转换明文密码为字节流（bcrypt 必需）
        password_bytes = string.encode("utf-8")
        
        # 2. 自动生成安全盐值 + 哈希（默认 12 轮迭代，可调难度）
        # bcrypt.gensalt()：自动生成盐值，可传入 rounds 参数调整难度（如 rounds=14）
        # 推荐 rounds=12-16，数字越大耗时越长，抗破解能力越强
        salt_bytes = bcrypt.gensalt(rounds=12)  # 自动生成盐值，无需手动配置
        hashed_bytes = bcrypt.hashpw(password_bytes, salt_bytes)
        
        # 3. 转换为字符串返回（兼容原有函数的返回值类型）
        return hashed_bytes.decode("utf-8")
    
    @staticmethod
    def verify_sha_passwd(plain: str, hashed: str) -> bool:
        """
        验证明文密码是否匹配哈希（底层替换为 bcrypt，安全高效）
        """
        try:
            # 1. 转换明文密码和哈希为字节流（bcrypt 必需）
            plain_bytes = plain.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")
            
            # 2. bcrypt 内置验证（自动提取哈希中的盐值，无需手动处理）
            # 核心逻辑：用哈希中存储的盐值重新计算明文哈希，对比是否一致
            return bcrypt.checkpw(plain_bytes, hashed_bytes)
        except Exception as e:
            # 哈希格式非法时返回 False，避免程序崩溃
            logger.error(f"密码验证失败：{e}")
            return False
    



    @staticmethod
    def wp_hash_password(password: str) -> str:
        """
        完全复刻 WordPress 6.8.0+ 的 wp_hash_password 函数逻辑
        :param password: 原始明文密码
        :return: WordPress 格式的密码哈希（带 $wp$ 前缀）
        """
        # Step 1: 去除密码首尾空格（WordPress 核心逻辑）
        trimmed_password = password.strip()
        
        # Step 2: 计算 HMAC-SHA384 二进制摘要（key=wp-sha384）
        hmac_key = b'wp-sha384'
        password_bytes = trimmed_password.encode('utf-8')
        hmac_digest = hmac.new(hmac_key, password_bytes, hashlib.sha384).digest()
        
        # Step 3: 对二进制摘要做 base64 编码（WordPress 核心步骤）
        password_to_hash = base64.b64encode(hmac_digest).decode('utf-8')
        
        # Step 4: 生成 bcrypt 哈希（cost=12，前缀 2y，兼容 WordPress）
        # Python bcrypt 不支持 2y，先以 2b 生成，再替换为 2y
        salt = bcrypt.gensalt(rounds=12, prefix=b'2b')
        bcrypt_hash = bcrypt.hashpw(password_to_hash.encode('utf-8'), salt).decode('utf-8')
        bcrypt_hash = bcrypt_hash.replace('$2b$', '$2y$')
        
        # Step 5: 添加 WordPress 特有的 $wp 前缀
        wp_hash = f'$wp{bcrypt_hash}'
        
        return wp_hash
    @staticmethod
    def wp_verify_password(password: str, wp_hash: str) -> bool:
        """
        完全复刻 WordPress 密码校验逻辑
        :param password: 原始明文密码
        :param wp_hash: WordPress 生成的哈希值
        :return: 匹配返回 True，否则返回 False
        """
        try:
            # Step 1: 移除 $wp 前缀，还原 bcrypt 哈希
            bcrypt_hash = wp_hash.replace('$wp', '')
            # 替换 2y 为 2b（Python bcrypt 兼容）
            bcrypt_hash = bcrypt_hash.replace('$2y$', '$2b$')
            bcrypt_hash_bytes = bcrypt_hash.encode('utf-8')
            
            # Step 2: 对原始密码执行和哈希时相同的预处理
            trimmed_password = password.strip()
            hmac_key = b'wp-sha384'
            password_bytes = trimmed_password.encode('utf-8')
            hmac_digest = hmac.new(hmac_key, password_bytes, hashlib.sha384).digest()
            password_to_verify = base64.b64encode(hmac_digest).decode('utf-8')
            password_to_verify_bytes = password_to_verify.encode('utf-8')
            
            # Step 3: 校验 bcrypt 哈希
            return bcrypt.checkpw(password_to_verify_bytes, bcrypt_hash_bytes)
        except (ValueError, TypeError, IndexError):
            # 哈希格式错误/空值时返回不匹配
            return False

    @staticmethod    
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
            
            logger.warning("无法解析session_tokens数据")
            return None
            
        except Exception as e:
            logger.error(f"解析 session_tokens 失败: {str(e)}", exc_info=True)
            return None
    @staticmethod
    def set_php_session_tokens(session_tokens):
        """
        生成PHP序列化格式的session_tokens字符串（与parse函数反向兼容）
        :param session_tokens: 字典，格式如 {
            "64位token字符串": {
                "expiration": 时间戳整数,
                "ip": IP字符串,
                "ua": 用户代理字符串,
                "login": 登录状态整数(1/0)
            }
        }
        :return: PHP序列化字符串 | None（失败时）
        """
        try:
            # 入参校验
            if not isinstance(session_tokens, dict) or len(session_tokens) == 0:
                logger.warning("session_tokens入参为空或非字典类型")
                return None
            
            serialized_parts = []
            # 遍历每个token，生成对应序列化片段
            for token, data in session_tokens.items():
                # 校验token格式（64位十六进制）
                if not re.match(r'^[a-f0-9]{64}$', token, re.I):
                    logger.warning(f"无效的token格式: {token}，需为64位十六进制字符串")
                    continue
                
                # 校验必要字段
                required_fields = ['expiration', 'ip', 'ua', 'login']
                for field in required_fields:
                    if field not in data:
                        logger.warning(f"token {token} 缺少必要字段: {field}")
                        break
                else:  # 所有必要字段都存在时执行
                    # 生成IP字段的PHP序列化格式（s:长度:"值"）
                    ip_len = len(data['ip'])
                    ip_serialized = f's:2:"ip";s:{ip_len}:"{data["ip"]}";'
                    
                    # 生成UA字段的PHP序列化格式
                    ua_len = len(data['ua'])
                    ua_serialized = f's:2:"ua";s:{ua_len}:"{data["ua"]}";'
                    
                    # 生成expiration/login字段（整数类型：i:值;）
                    exp_serialized = f's:10:"expiration";i:{data["expiration"]};'
                    login_serialized = f's:5:"login";i:{data["login"]};'
                    
                    # 拼接数组内容（固定4个字段，与parse的pattern1匹配）
                    array_content = f'{exp_serialized}{ip_serialized}{ua_serialized}{login_serialized}'
                    # 拼接完整的token片段（s:64:"token";a:4:{数组内容};）
                    token_serialized = f's:64:"{token}";a:4:{{{array_content}}}'
                    serialized_parts.append(token_serialized)
            
            # 拼接所有token片段，返回最终序列化字符串
            if serialized_parts:
                return ''.join(serialized_parts)
            else:
                logger.warning("无有效token数据生成序列化字符串")
                return None
            
        except Exception as e:
            logger.error(f"生成PHP session_tokens失败: {str(e)}", exc_info=True)
            return None    
    
    @staticmethod
    def parse_php_serialize(serialized_str):
        """
        解析PHP序列化字符串为Python字典/列表
        :param serialized_str: PHP序列化字符串（如你的示例）
        :return: 解析后的Python数据（字典/列表）| None（失败）
        """
        try:
            # 去除首尾空白，保证解析准确性
            serialized_str = serialized_str.strip()
            if not serialized_str:
                logger.warning("空的序列化字符串，解析失败")
                return None
            
            # 递归解析核心函数
            def _parse(data, pos):
                # 跳过空白字符
                while pos < len(data) and data[pos].isspace():
                    pos += 1
                if pos >= len(data):
                    return None, pos
                
                # 匹配类型标识（a/s/b/i/d）
                type_match = re.match(r'([asbid]):', data[pos:])
                if not type_match:
                    logger.error(f"不支持的类型标识，位置{pos}：{data[pos:pos+10]}")
                    return None, pos
                data_type = type_match.group(1)
                pos += len(type_match.group(0))

                if data_type == 'a':  # 解析数组
                    # 匹配数组长度：a:3:{ → 提取3
                    len_match = re.match(r'(\d+):\{', data[pos:])
                    if not len_match:
                        logger.error(f"数组格式错误，位置{pos}：{data[pos:pos+10]}")
                        return None, pos
                    arr_len = int(len_match.group(1))
                    pos += len(len_match.group(0))
                    
                    arr = {} if arr_len > 0 else []
                    for _ in range(arr_len):
                        # 解析键
                        key, pos = _parse(data, pos)
                        if key is None:
                            break
                        # 解析值
                        value, pos = _parse(data, pos)
                        if value is None:
                            break
                        arr[key] = value
                    
                    # 跳过数组结束符 }
                    while pos < len(data) and data[pos] != '}':
                        pos += 1
                    pos += 1
                    return arr, pos

                elif data_type == 's':  # 解析字符串
                    # 匹配字符串长度：s:4:"core"; → 提取4
                    len_match = re.match(r'(\d+):"', data[pos:])
                    if not len_match:
                        logger.error(f"字符串格式错误，位置{pos}：{data[pos:pos+10]}")
                        return None, pos
                    str_len = int(len_match.group(1))
                    pos += len(len_match.group(0))
                    
                    # 提取字符串内容（长度为str_len）
                    str_val = data[pos:pos+str_len]
                    pos += str_len
                    # 跳过结束符 ";
                    if pos < len(data) and data[pos:pos+2] == '";':
                        pos += 2
                    return str_val, pos

                elif data_type == 'b':  # 解析布尔值
                    # 匹配布尔值：b:1; → 提取1/0
                    bool_match = re.match(r'([01]);', data[pos:])
                    if not bool_match:
                        logger.error(f"布尔值格式错误，位置{pos}：{data[pos:pos+10]}")
                        return None, pos
                    bool_val = bool(int(bool_match.group(1)))
                    pos += len(bool_match.group(0))
                    return bool_val, pos

                elif data_type == 'i':  # 解析整数
                    # 匹配整数：i:123; → 提取123
                    int_match = re.match(r'(-?\d+);', data[pos:])
                    if not int_match:
                        logger.error(f"整数格式错误，位置{pos}：{data[pos:pos+10]}")
                        return None, pos
                    int_val = int(int_match.group(1))
                    pos += len(int_match.group(0))
                    return int_val, pos

                elif data_type == 'd':  # 解析浮点数
                    # 匹配浮点数：d:3.14; → 提取3.14
                    float_match = re.match(r'(-?\d+\.?\d*);', data[pos:])
                    if not float_match:
                        logger.error(f"浮点数格式错误，位置{pos}：{data[pos:pos+10]}")
                        return None, pos
                    float_val = float(float_match.group(1))
                    pos += len(float_match.group(0))
                    return float_val, pos

                else:
                    logger.error(f"未实现的类型：{data_type}")
                    return None, pos

            # 启动递归解析
            result, _ = _parse(serialized_str, 0)
            return result

        except Exception as e:
            logger.error(f"解析PHP序列化数据失败：{str(e)}", exc_info=True)
            return None

    @staticmethod
    def build_php_serialize(python_data):
        """
        将Python字典/列表/基本类型转为PHP序列化字符串
        :param python_data: Python数据（字典/列表/字符串/布尔/整数等）
        :return: PHP序列化字符串 | None（失败）
        """
        try:
            # 递归构建核心函数
            def _build(data):
                if isinstance(data, dict):  # 构建数组（关联数组）
                    arr_items = []
                    for key, value in data.items():
                        # 键必须是字符串/整数（PHP数组键规则）
                        key_str = _build(key) if isinstance(key, (str, int, bool)) else _build(str(key))
                        val_str = _build(value)
                        arr_items.append(f"{key_str}{val_str}")
                    arr_content = ''.join(arr_items)
                    return f"a:{len(arr_items)}:{{{arr_content}}}"

                elif isinstance(data, list):  # 构建索引数组
                    arr_items = []
                    for idx, value in enumerate(data):
                        key_str = _build(idx)
                        val_str = _build(value)
                        arr_items.append(f"{key_str}{val_str}")
                    arr_content = ''.join(arr_items)
                    return f"a:{len(arr_items)}:{{{arr_content}}}"

                elif isinstance(data, str):  # 构建字符串
                    str_len = len(data)
                    return f"s:{str_len}:\"{data}\";"

                elif isinstance(data, bool):  # 构建布尔值
                    bool_val = 1 if data else 0
                    return f"b:{bool_val};"

                elif isinstance(data, int):  # 构建整数
                    return f"i:{data};"

                elif isinstance(data, float):  # 构建浮点数
                    return f"d:{data};"

                else:
                    logger.warning(f"不支持的类型：{type(data)}，转为字符串处理")
                    return _build(str(data))

            # 启动递归构建
            result = _build(python_data)
            return result

        except Exception as e:
            logger.error(f"构建PHP序列化数据失败：{str(e)}", exc_info=True)
            return None
    @staticmethod
    def remove_key_recursive(obj, target_key):
        if isinstance(obj, dict):
            # 删除当前层级的键
            if target_key in obj:
                del obj[target_key]
            # 递归处理所有值
            for key in list(obj.keys()):  # 转换为list避免字典改变导致的遍历错误
                CommonUtils.remove_key_recursive(obj[key], target_key)
        elif isinstance(obj, list):
            # 递归处理列表中的每个元素
            for item in obj:
                CommonUtils.remove_key_recursive(item, target_key)

    @staticmethod
    def json_response(json_data,status=200,cookies=None,headers=None):
        """
        返回json格式的响应
        """
        from flask import Response
        response = Response(json.dumps(json_data), status=status,content_type='application/json',headers=headers)
        if cookies:
            for key, value in cookies.items():
                response.set_cookie(key, value)
        return response
        

    ##########################################################################################
    @staticmethod
    def create_rsa_key(key_size=2048,public_exponent=65537):
        """
        创建RSA密钥
        返回 私钥,公钥
        """
        # 生成 RSA 私钥
        private_key = rsa.generate_private_key(
            public_exponent=65537,  # 公共指数，通常使用 65537
            key_size=2048,  # 密钥长度，建议使用 2048 或更高
            backend=default_backend()
        )

        # 从私钥中提取公钥
        public_key = private_key.public_key()

        # 将私钥序列化为 PEM 格式
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption()
        )

        # 将公钥序列化为 PEM 格式
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return private_pem,public_pem
    @staticmethod 
    def get_exist_rsa_key(pem_path:str = None,create_new:bool = True):
        """
        从已有的私钥和公钥中加载RSA密钥
        返回 私钥,公钥
        """
        
        from app.settings import DefaultConfig 

        if pem_path is None:
            pem_path = DefaultConfig.PASSWORD_PRIVATE_KEY_FILE

        if os.path.exists(pem_path) :
            with open(pem_path, "rb") as f:
                private_pem = f.read()
                private_key = CommonUtils.load_private_key(private_pem)
                # 从私钥中提取公钥
                public_key = private_key.public_key()
                # 将公钥序列化为 PEM 格式
                public_pem = public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                return private_pem,public_pem
        else:
            if(create_new):
                private_pem,public_pem = CommonUtils.create_rsa_key()
                with open(pem_path, "wb") as f:
                    f.write(private_pem)
                return private_pem,public_pem

        
    @staticmethod
    def load_private_key(private_pem: str | bytes,password:bytes = None):
        # 判断 private_pem 的类型
        if isinstance(private_pem, str):
            private_pem = private_pem.encode()
        # 加载 PEM 格式私钥文本到私钥对象
        try:
            private_key = serialization.load_pem_private_key(
                private_pem,
                password=password,
                backend=default_backend()
            )
            return private_key
        except Exception as e:
            return None
        
    @staticmethod
    def load_public_key(public_pem: str | bytes):
        # 判断 private_pem 的类型
        if isinstance(public_pem, str):
            public_pem = public_pem.encode()
        # 加载 PEM 格式私钥文本到私钥对象
        try:
            public_key = serialization.load_pem_public_key(
                public_pem,
                backend=default_backend()
            )
            return public_key
        except Exception as e:
            return None
    @staticmethod
    def aes_encrypt_large_data(data, key):
        """
        加密大数据
        :param data: 待加密的数据（bytes 类型）
        :param key: 加密密钥（bytes 类型，长度可以是 16、24 或 32 字节）
        :return: 加密后的数据（bytes 类型）和初始化向量（IV）
        """
        # 生成一个随机的初始化向量（IV），AES 在 CBC 模式下需要 IV
        iv = os.urandom(16)
        # 创建 AES 加密器，使用 CBC 模式
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        # 对数据进行填充，使其长度为 16 字节的倍数
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padded_data = data + bytes([padding_length]) * padding_length

        encrypted_chunks = []
        # 分块加密数据
        for i in range(0, len(padded_data), block_size):
            chunk = padded_data[i:i + block_size]
            encrypted_chunk = encryptor.update(chunk)
            encrypted_chunks.append(encrypted_chunk)

        # 完成加密过程
        final_chunk = encryptor.finalize()
        encrypted_chunks.append(final_chunk)

        encrypted_data = b''.join(encrypted_chunks)
        return encrypted_data, iv
    @staticmethod
    def aes_decrypt_large_data(encrypted_data, key, iv):
        """
        解密大数据
        :param encrypted_data: 加密后的数据（bytes 类型）
        :param key: 解密密钥（bytes 类型，与加密时的密钥相同）
        :param iv: 初始化向量（IV，bytes 类型）
        :return: 解密后的数据（bytes 类型）
        """
        # 创建 AES 解密器，使用 CBC 模式
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()
        decrypted_chunks = []
        block_size = 16
        # 分块解密数据
        for i in range(0, len(encrypted_data), block_size):
            chunk = encrypted_data[i:i + block_size]
            decrypted_chunk = decryptor.update(chunk)
            decrypted_chunks.append(decrypted_chunk)

        # 完成解密过程
        final_chunk = decryptor.finalize()
        decrypted_chunks.append(final_chunk)

        decrypted_data = b''.join(decrypted_chunks)
        # 去除填充数据
        padding_length = decrypted_data[-1]
        decrypted_data = decrypted_data[:-padding_length]
        return decrypted_data
    

    @staticmethod
    # 获取RSA加密块的最大大小，考虑填充方式
    def get_max_chunk_size(key_size: int, padding_scheme: str = "PKCS1v15"):
        key_bytes = key_size // 8
        if padding_scheme == "OAEP":
            # OAEP 填充需要额外的字节，SHA-256 的 hash_size 是 32 字节
            hash_size = 32
            padding_overhead = 2 * hash_size + 2
        else:  # 默认使用 PKCS#1 v1.5 填充
            padding_overhead = 11  # PKCS#1 v1.5 填充的标准字节大小为 11 字节
        
        # 最大数据块大小：RSA密钥大小减去填充的大小
        max_chunk_size = key_bytes - padding_overhead
        return max_chunk_size

    @staticmethod
    # RSA 分块加密，支持选择填充方式
    def rsa_encrypt_chunks(data: bytes, public_key, padding_scheme: str = "PKCS1v15"):
        key_size = public_key.key_size
        max_chunk_size = CommonUtils.get_max_chunk_size(key_size, padding_scheme)
        encrypted_chunks = []

        for i in range(0, len(data), max_chunk_size):
            chunk = data[i:i + max_chunk_size]

            if padding_scheme == "OAEP":
                encrypted_chunk = public_key.encrypt(
                    chunk,
                    padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
            else:  # 默认使用 PKCS#1 v1.5 填充
                encrypted_chunk = public_key.encrypt(
                    chunk,
                    padding.PKCS1v15()
                )

            encrypted_chunks.append(encrypted_chunk)

        return b''.join(encrypted_chunks)

    @staticmethod
    # RSA 分块解密，支持选择填充方式
    def rsa_decrypt_chunks(encrypted_data: bytes, private_key, padding_scheme: str = "PKCS1v15"):
        key_size = private_key.key_size
        chunk_size = key_size // 8  # 这应该等于RSA密钥的字节大小
        decrypted_chunks = []

        for i in range(0, len(encrypted_data), chunk_size):
            chunk = encrypted_data[i:i + chunk_size]
            if padding_scheme.upper() == "OAEP":
                decrypted_chunk = private_key.decrypt(
                    ciphertext=chunk,
                    padding=padding.OAEP(
                        mgf=padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
            else:  # 默认使用 PKCS#1 v1.5 填充
                decrypted_chunk = private_key.decrypt(
                    chunk,
                    padding.PKCS1v15()
                )

            decrypted_chunks.append(decrypted_chunk)

        return b''.join(decrypted_chunks)
    

    @staticmethod
    # RSA 加密，支持选择填充方式，所有关键参数可配置（含默认值）
    def rsa_encrypt(
        data: bytes,
        public_key,
        padding_scheme: str = "PKCS1v15",
        # OAEP 专属可配置参数（默认值沿用原有逻辑）
        oaep_hash_alg: Type[hashes.HashAlgorithm] = hashes.SHA256,
        oaep_mgf: Type[padding.MGF] = padding.MGF1,
        oaep_mgf_hash_alg: Type[hashes.HashAlgorithm] = hashes.SHA256,
        oaep_label: Optional[bytes] = None
    ):
        """
        RSA 单段加密（无分段逻辑）
        :param data: 待加密字节数据（需满足对应填充的长度限制）
        :param public_key: 公钥对象（cryptography 库的 RSAPublicKey 类型）
        :param padding_scheme: 填充方案，可选 "PKCS1v15" 或 "OAEP"（默认 PKCS1v15）
        :param oaep_hash_alg: OAEP 填充的哈希算法（默认 SHA256），需传入 hashes 类的算法（如 hashes.SHA1）
        :param oaep_mgf: OAEP 掩码生成函数（默认 MGF1），需传入 padding 类的 MGF（如 padding.MGF1）
        :param oaep_mgf_hash_alg: MGF 函数的哈希算法（默认 SHA256），需传入 hashes 类的算法
        :param oaep_label: OAEP 可选标签（默认 None，加密端和解密端需一致）
        :return: 加密后的字节数据
        """
        if padding_scheme.upper() == "OAEP":
            # OAEP 填充（参数可配置）
            return public_key.encrypt(
                data,
                padding.OAEP(
                    mgf=oaep_mgf(algorithm=oaep_mgf_hash_alg()),
                    algorithm=oaep_hash_alg(),
                    label=oaep_label
                )
            )
        else:
            # PKCS1v15 填充（默认）
            return public_key.encrypt(
                data,
                padding.PKCS1v15()
            )

    @staticmethod
    # RSA 解密，支持选择填充方式，所有关键参数可配置（含默认值）
    def rsa_decrypt(
        encrypted_data: bytes,
        private_key,
        padding_scheme: str = "PKCS1v15",
        # OAEP 专属可配置参数（默认值沿用原有逻辑，需与加密端一致）
        oaep_hash_alg: Type[hashes.HashAlgorithm] = hashes.SHA256,
        oaep_mgf: Type[padding.MGF] = padding.MGF1,
        oaep_mgf_hash_alg: Type[hashes.HashAlgorithm] = hashes.SHA256,
        oaep_label: Optional[bytes] = None
    ):
        """
        RSA 单段解密（无分段逻辑）
        :param encrypted_data: 加密后的字节数据（单段，长度=密钥字节数）
        :param private_key: 私钥对象（cryptography 库的 RSAPrivateKey 类型）
        :param padding_scheme: 填充方案，可选 "PKCS1v15" 或 "OAEP"（默认 PKCS1v15）
        :param oaep_hash_alg: OAEP 填充的哈希算法（默认 SHA256），需与加密端一致
        :param oaep_mgf: OAEP 掩码生成函数（默认 MGF1），需与加密端一致
        :param oaep_mgf_hash_alg: MGF 函数的哈希算法（默认 SHA256），需与加密端一致
        :param oaep_label: OAEP 可选标签（默认 None），需与加密端一致
        :return: 解密后的原始字节数据
        """
        if padding_scheme.upper() == "OAEP":
            # OAEP 填充解密（参数可配置）
            return private_key.decrypt(
                ciphertext=encrypted_data,
                padding=padding.OAEP(
                    mgf=oaep_mgf(algorithm=oaep_mgf_hash_alg()),
                    algorithm=oaep_hash_alg(),
                    label=oaep_label
                )
            )
        else:
            # PKCS1v15 填充解密（默认）
            return private_key.decrypt(
                encrypted_data,
                padding.PKCS1v15()
            )
    


    @staticmethod
    # 对数据进行哈希计算
    def hash_data(data):
        digest = hashes.Hash(hashes.SHA256(), backend=default_backend())
        if isinstance(data, bytes):
            digest.update(data)
        elif isinstance(data, str):
            digest.update(data.encode())
        return digest.finalize()

    @staticmethod
    # RSA 签名
    def rsa_sign(private_key, data):
        hash_value = CommonUtils.hash_data(data)
        signature = private_key.sign(
            hash_value,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return signature

    @staticmethod
    # RSA 验证签名
    def rsa_verify(public_key, data, signature):
        hash_value = CommonUtils.hash_data(data)
        try:
            public_key.verify(
                signature,
                hash_value,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            return True
        except Exception:
            return False
    @staticmethod
    def paypal_create_product(paypal_request_id:str,data):
        import requests

        headers = {
            'Authorization': 'Bearer access_token6V7rbVwmlM1gFZKW_8QtzWXqpcwQ6T5vhEGYNJDAAdn3paCgRpdeMdVYmWzgbKSsECednupJ3Zx5Xd-g',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'PayPal-Request-Id': paypal_request_id,
            'Prefer': 'return=representation',
        }

        data = json.dumps(data)

        response = requests.post('https://api-m.sandbox.paypal.com/v1/catalogs/products', headers=headers, data=data)
        return response.json()