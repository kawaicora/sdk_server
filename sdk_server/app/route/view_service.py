# -*- coding:utf-8 -*-
from app.route import bp

from flask import *
from app.settings import *
import yaml
from app.extensions import parse_encrypted_resume
from app.sql_class.Tables import Users,Usermeta
from app.utils.ErrorCode import get_response_string

import xml.etree.ElementTree as ET


# def check_login(request):
#     uid = request.cookies.get("uid")
#     token = request.cookies.get("token")
#     if (not uid) or (not token):
#         return False
#     account = Account.query.filter_by(id=uid,login_token=token).first()
#     if account:
#         return True
#     else:
#         return False
    

    
@bp.route("/")
@bp.route("/view/")
def view_index():
    response = make_response(render_template("index.html"),200)
    response.headers['X-Organization'] = 'Nintendo'
    return response


@bp.route("/favicon.ico")
def view_favicon():
    return send_from_directory("static/img","favicon.ico")

# @bp.route("/view/login")
# def view_login():
#     response = make_response(render_template("login.html"),200)
#     response.headers['X-Organization'] = 'Nintendo'
#     return response

# @bp.route("/view/register")
# def view_register():
#     response = make_response(render_template("register.html"),200)
#     response.headers['X-Organization'] = 'Nintendo'
#     return response
@bp.route("/view/home_controller")
def view_home_controller():
    # result = check_login(request)
    # if not result:
    #     return redirect(url_for('root.view_login'))
    response = make_response(render_template("home_controller.html"),200)
    response.headers['X-Organization'] = 'Nintendo'
    return response
@bp.route("/view/webrtc")
def view_webrtc():
    # result = check_login(request)
    # if not result:
    #     return redirect(url_for('root.view_login'))
    response = make_response(render_template("webrtc.html"),200)
    response.headers['X-Organization'] = 'Nintendo'
    return response

@bp.route("/view/chat")
def view_chat():
    # result = check_login(request)
    # if not result:
    #     return redirect(url_for('root.view_login'))
    response = make_response(render_template("chat.html"),200)
    response.headers['X-Organization'] = 'Nintendo'
    return response

@bp.route("/view/resume")
def view_resume():
    # 这里假设你的 YAML 文件名为 resume.yaml，你可以根据实际情况修改路径
    resume_data = parse_encrypted_resume()
    response = make_response(render_template("resume.html", **resume_data),200)
    response.headers['X-Organization'] = 'Nintendo'
    return response

def read_yaml():
    with open(os.path.join(DefaultConfig.BASE_DIR,"./data/resume.yaml"), 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def write_yaml(data):
    with open(os.path.join(DefaultConfig.BASE_DIR,"./data/resume.yaml"), 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True, default_flow_style=False)





@bp.route("/view/forum")
def view_forum():
    if len(request.args) >0:
        return Response(get_response_string(0),status=200,content_type="application/json")
    response = make_response(render_template("forum.html"),200)
    response.headers['X-Organization'] = 'Nintendo'
    return response

@bp.route("/view/vrtest")
def view_vrtest():
    if len(request.args) >0:
        return Response(get_response_string(0),status=200,content_type="application/json")
    response = make_response(render_template("vr-test.html"),200)
    response.headers['X-Organization'] = 'Nintendo'
    return response

