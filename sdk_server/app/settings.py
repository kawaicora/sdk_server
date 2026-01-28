# -*- coding:utf-8 -*-
from datetime import timedelta
import os
class DefaultConfig(object):
    # Flask Default Support 
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"  # 转换为布尔值（.env 中是字符串）
    USE_X_SENDFILE = False
    TRUSTED_HOSTS = None
    SERVER_NAME = os.getenv("SERVER_NAME")
    APPLICATION_ROOT = os.getenv("BASE_DIR", os.getcwd())  # 从 .env 读取，默认 os.getcwd()
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 4294967296))  # 转换为整数

    TEMPLATES_AUTO_RELOAD = os.getenv("TEMPLATES_AUTO_RELOAD", "True").lower() == "true"
    MAX_COOKIE_SIZE = int(os.getenv("MAX_COOKIE_SIZE", 4093))

    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")


    SQLALCHEMY_ECHO = os.getenv("SQLALCHEMY_ECHO", "False").lower() == "true"
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", "False").lower() == "true"

    ########################################################################################
    SOCKETIO_LOGGER = os.getenv("SOCKETIO_LOGGER", "False").lower() == "true"
    ENGINEIO_LOGGER = os.getenv("ENGINEIO_LOGGER", "False").lower() == "true"

    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    RESEND_MAIL = os.getenv("RESEND_MAIL")

    SAKURAXY_OAUTH_APP_ID = os.getenv("SAKURAXY_OAUTH_APP_ID")
    SAKURAXY_OAUTH_API = os.getenv("SAKURAXY_OAUTH_API")
    SAKURAXY_OAUTH_TOKEN = os.getenv("SAKURAXY_OAUTH_TOKEN")
    
    # 私钥：读取后还原 \n 为实际换行符
    SAKURAXY_LOGIN_PRIVATE_KEY = os.getenv("SAKURAXY_LOGIN_PRIVATE_KEY", "").replace("\\n", "\n")

    SDK_BASE_URL = os.getenv("SDK_BASE_URL")
    BASE_DIR = os.getenv("BASE_DIR", os.getcwd())
    STATIC_FOLDER = os.getenv("STATIC_FOLDER","static")
    TEMPLATES_FOLDER = os.getenv("TEMPLATES_FOLDER","templates")
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER","static/upload/")

    SUFFIX = os.getenv("SUFFIX")
    PASSWORD_PRIVATE_KEY_FILE = os.getenv("PASSWORD_PRIVATE_KEY_FILE")
    CLIENT_SECRET_KEY_FILE = os.getenv("CLIENT_SECRET_KEY_FILE")

    LOGGED_IN_KEY = os.getenv("LOGGED_IN_KEY")
    LOGGED_IN_SALT = os.getenv("LOGGED_IN_SALT")
    LOGGED_IN_SALT_COMBINED = LOGGED_IN_KEY + LOGGED_IN_SALT  # 保持原有逻辑

    CLOUDFLARE_TURN_TOKEN = os.getenv("CLOUDFLARE_TURN_TOKEN")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_BOT_CHAT_ID = int(os.getenv("TELEGRAM_BOT_CHAT_ID"))  # 转换为整数