# -*- coding: utf-8 -*-
from flask import Response
from flask_sqlalchemy import SQLAlchemy

from flask_socketio import SocketIO
from sqlalchemy import Engine, create_engine

from app.settings import DefaultConfig
from engineio.payload import Payload

# 提高单个 payload 允许的最大数据包数量（默认 16）

Payload.max_decode_packets = 1024
db:SQLAlchemy = SQLAlchemy()
socketio:SocketIO = SocketIO(
    logger=DefaultConfig.SOCKETIO_LOGGER,
    engineio_logger=DefaultConfig.ENGINEIO_LOGGER,
    transports=['websocket', 'polling', 'xhr-polling', 'jsonp-polling'],
    # 如果通过代理，需要设置这些
    ping_timeout=60,
    ping_interval=25,
    cors_allowed_origins='*',
    async_mode='gevent'
)



def set_cookies(response :Response,cookies,samesite:str='None',secure:bool = True,path:str="/",max_age:int|None = None):
    for k,v in cookies.items():
        response.set_cookie(key = k,value = str(v), samesite=samesite,secure=secure,path=path ,max_age = max_age)
    return response



def parse_encrypted_resume():
    from proto.resume_pb2 import Resume
    from app.utils.Ec2b import Ec2b
    from app.settings import DefaultConfig

    # 1. 读取加密文件
    with open("data/resume.dat", "rb") as fp:
        encrypted_bytes = fp.read()

    # 2. 生成解密所需的种子
    with open(DefaultConfig.CLIENT_SECRET_KEY_FILE, "rb") as fp:
        csk = fp.read()
    key, data = Ec2b.LoadKey(csk)
    seed = Ec2b.GetSeed(key, data)
    temp = Ec2b.SetSeed(seed)

    # 3. 解密数据
    decrypted_bytes = Ec2b.Xor(encrypted_bytes, temp)

    # 4. 解析 Protobuf 字节
    resume_proto = Resume()
    resume_proto.ParseFromString(decrypted_bytes)

    # 5. 转换为字典结构
    resume_dict = {
        "person_info": {
            "birth": resume_proto.personal_info.birth,
            "school": resume_proto.personal_info.school,
            "education": resume_proto.personal_info.education,
            "major": resume_proto.personal_info.major,
            "native_place": resume_proto.personal_info.native_place,
            "current_place": resume_proto.personal_info.current_place,
            "email": resume_proto.personal_info.email,
            "phone": resume_proto.personal_info.phone,
            "address": resume_proto.personal_info.address,
            "content": resume_proto.personal_info.content,
            "label": resume_proto.personal_info.label,
            "name": resume_proto.personal_info.name,
            "photo_url": resume_proto.personal_info.photo_url
        },
        "education": [
            {
                "degree": edu.degree,
                "major": edu.major,
                "school_name": edu.school_name,
                "time": edu.time
            } for edu in resume_proto.educations
        ],
        "project_works": [
            {
                "name": proj.name,
                "work_time": proj.work_time,
                "content": proj.content
            } for proj in resume_proto.project_works
        ],
        "skills_introduction": {
            "title": resume_proto.skills_introduction.title,
            "content": resume_proto.skills_introduction.content
        },
        "tag_list": [
            {
                "icon": tag.icon,
                "name": tag.name
            } for tag in resume_proto.tag_lists
        ],
        "work_experience": [
            {
                "company_name": exp.company_name,
                "position": exp.position,
                "work_time": exp.work_time,
                "work_content": exp.work_content
            } for exp in resume_proto.work_experiences
        ]
    }


    return resume_dict

