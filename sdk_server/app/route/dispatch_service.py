# -*- coding:utf-8 -*-
import base64
import secrets
from app.route import bp
from flask import *
from app.settings import *
import datetime
import eyed3
from app.utils.CommonUtils import *
import secrets
from app.utils.ErrorCode import ErrorCode
from app.extensions import *



# ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'flac'}
# music_upload_dir = os.path.join(DefaultConfig.BASE_DIR, DefaultConfig.UPLOAD_FOLDER)
# database_path = os.path.join(DefaultConfig.BASE_DIR,"data/music_list.json")
# # 检查文件扩展名是否合法
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# # 提取音频文件的元数据
# def get_audio_metadata(file):
#     # 读取音频文件并解析
#     audio_file = eyed3.load(file)
    
#     # 提取标题、作者和封面图像
#     title = audio_file.tag.title if audio_file.tag.title else "Unknown Title"
#     artist = audio_file.tag.artist if audio_file.tag.artist else "Unknown Artist"
    
#     # 尝试获取封面图片
#     album = audio_file.tag.album if audio_file.tag.artist else "Unknown Album "
  
#     album_artist = audio_file.tag.album if audio_file.tag.artist else "Unknown AlbumArtist "

#     # cover_image_data = None
#     cover_image_base64= ""
#     cover_mime_type = ""
#     frame = audio_file.tag.frame_set[b"APIC"]
#     if (frame != None):
#         for subframe in frame:
            

#             image_data =subframe.image_data
        
#             mime_type = subframe.mime_type
#             image_type = subframe.picture_type
#             if(image_type == 6 ):
#                 # cover_image_data = image_data
#                 cover_image_base64 = base64.b64encode(image_data).decode('utf-8')
#                 cover_mime_type = mime_type
#                 # # 打印相关信息
#                 # print(f"图片的 MIME 类型: {mime_type}")
#                 # print(f"图片类型: {image_type}")
#                 # print(f"图片数据大小: {len(image_data)} bytes")
#     return title, artist, album,album_artist,cover_image_base64,cover_mime_type




# # 处理上传的音乐文件
# @bp.route('/api/upload_music', methods=['POST'])
# def api_upload_music():
    
#     if 'file' not in request.files:
#         return "No file part", 400
#     file = request.files['file']
    
#     if file.filename == '':
#         return "No selected file", 400
    
#     if file and allowed_file(file.filename):
#         # 安全保存文件
#         # filename = base64.b64encode(file.filename.encode()).decode()
#         filename = file.filename
#         CommonUtils.create_directory(music_upload_dir)
#         file_path = os.path.join(music_upload_dir, filename)
#         file.save(file_path)
        
#         # 提取音频文件的元数据
#         title, artist, album,album_artist,cover_image_base64,cover_mime_type = get_audio_metadata(file_path)

#         music_list = []
#         with open(database_path,"r",encoding="utf-8") as fp:
            
#             try:
#                 music_list = json.load(fp)
#             except Exception as e:
                
#                 pass
#         need_add = True
#         for item in music_list:
#             if item["title"] == title and item["artist"] == artist:
#                 need_add = False
#         # 获取当前时间对象
#         now = datetime.now()

#         # 获取当前时间戳（秒级）
#         timestamp = now.timestamp()
#         _id = (base64.b64encode((title+artist+str(timestamp)+secrets.token_hex(4)).encode())).decode()

#         nitem = {
#             "id":_id,
#             "url":f"{DefaultConfig.SDK_BASE_URL}/{DefaultConfig.UPLOAD_FOLDER}/{filename}",
#             "filename":filename,
#             "title":title,
#             "artist":artist,
#             "album":album,
#             "album_artist":album_artist,
#             "cover_image_base64":cover_image_base64,
#             "cover_mime_type":cover_mime_type
#         }
#         if need_add:
#             with open(database_path,"w",encoding="utf-8") as fp:
#                 music_list.append(nitem)
#                 json.dump(music_list,fp,ensure_ascii=False,indent=4)
   
#             return Response(json.dumps({"retcode":0,"msg":"OK"}))
#         else:
#             return Response(json.dumps({"retcode":-1,"msg":"已存在"}))
      
        
#     else:
#         return Response(json.dumps({"retcode":-1,"msg":"Invalid file type"}))



# @bp.route("/api/get_music_list")
# def api_get_music_list():
#     music_list = []
#     cookies = {
#         "uid":10001000,
#         "token": secrets.token_hex(16),
#     }
#     headers = {
#         'X-Organization': 'Nintendo',
#         "X-Session": secrets.token_hex(16),

#     }
#     with open(database_path,"r",encoding="utf-8") as fp:
            
#         try:
#             music_list = json.load(fp)
#         except Exception as e:
            
#             pass
#     nmusic_list = []
#     for nitem in music_list:

#         tmp = {
#             "id":nitem.get("id"),
#             "title":nitem.get("title"),
#             "artist":nitem.get("artist"),
#             "url":nitem.get("url"),
#             "cover":f"{nitem.get('filename').split('.')[0]}{CommonUtils.get_suffix_by_mimetype(nitem.get('cover_mime_type'))}"
            
#         }
#         nmusic_list.append(tmp)
#     return set_cookies(Response(json.dumps(nmusic_list,ensure_ascii=False), status=200, content_type='application/json'),cookies)  



# @bp.route("/api/get_cover/<img_name>", methods=["GET"])
# def api_get_cover(img_name):
#      # 读取音乐列表 JSON 文件
#     try:
#         with open(os.path.join(DefaultConfig.BASE_DIR, "data/music_list.json"), "r", encoding="utf-8") as fp:
#             music_list = json.load(fp)
#     except Exception as e:
#         return Response(
#             json.dumps({"retcode": -1, "msg": "read database failed", "error": str(e)}),
#             status=500,
#             content_type="application/json"
#         )

#     # 查找匹配的歌曲信息
#     cover_info = {
#         "cover_image_base64": "",
#         "cover_mime_type": ""
#     }

#     for item in music_list:
        
#         if item.get("filename").split(".")[0] == img_name.split(".")[0]:
#             cover_info["cover_image_base64"] = item.get("cover_image_base64", "")
#             cover_info["cover_mime_type"] = item.get("cover_mime_type", "")
#             break

#     # 如果没有找到封面数据
#     if not cover_info["cover_image_base64"]:
#         return Response(
#             json.dumps({"retcode": -1, "msg": "Cover not found for the given ID"}),
#             status=404,
#             content_type="application/json"
#         )
#     if (cover_info["cover_image_base64"] == ""):
#          # 返回图片数据
#         return Response(
#             b"",
#             status=200,
#             content_type="image/jpeg"
#         )
#     # 解码 Base64 封面图片数据
#     try:
#         cover_image_data = base64.b64decode(cover_info["cover_image_base64"])
#     except Exception as e:
#         return Response(
#             json.dumps({"retcode": -1, "msg": "Failed to decode image data", "error": str(e)}),
#             status=500,
#             content_type="application/json"
#         )

#     # 返回图片数据
#     return Response(
#         cover_image_data,
#         status=200,
#         content_type=cover_info["cover_mime_type"]
#     )


# @bp.route("/api/get_cover_by_id", methods=["POST"])
# def api_get_cover_by_id():
#     # 获取请求中的 ID
#     id = request.json.get("id")

#     # 读取音乐列表 JSON 文件
#     try:
#         with open(os.path.join(DefaultConfig.BASE_DIR, "data/music_list.json"), "r", encoding="utf-8") as fp:
#             music_list = json.load(fp)
#     except Exception as e:
#         return Response(
#             json.dumps({"retcode": -1, "msg": "read database failed", "error": str(e)}),
#             status=500,
#             content_type="application/json"
#         )

#     # 查找匹配的歌曲信息
#     cover_info = {
#         "cover_image_base64": "",
#         "cover_mime_type": ""
#     }

#     for item in music_list:
#         if item.get("id") == id:
#             cover_info["cover_image_base64"] = item.get("cover_image_base64", "")
#             cover_info["cover_mime_type"] = item.get("cover_mime_type", "")
#             break

#     # 如果没有找到封面数据
#     if not cover_info["cover_image_base64"]:
#         return Response(
#             json.dumps({"retcode": -1, "msg": "Cover not found for the given ID"}),
#             status=404,
#             content_type="application/json"
#         )
#     if (cover_info["cover_image_base64"] == ""):
#          # 返回图片数据
#         return Response(
#             b"",
#             status=200,
#             content_type="image/jpeg"
#         )
#     # 解码 Base64 封面图片数据
#     try:
#         cover_image_data = base64.b64decode(cover_info["cover_image_base64"])
#     except Exception as e:
#         return Response(
#             json.dumps({"retcode": -1, "msg": "Failed to decode image data", "error": str(e)}),
#             status=500,
#             content_type="application/json"
#         )

#     # 返回图片数据
#     return Response(
#         cover_image_data,
#         status=200,
#         content_type=cover_info["cover_mime_type"]
#     )


@bp.route("/bfs/static/blive/blfe-live-room/static/js/vendors.d45ab3a267b3a529412c.js")
def bfs_static_blive_blfe_live_room_static_js_vendors_d45ab3a267b3a529412c_js():
    data = ""
    with open("./data/vendors.d45ab3a267b3a529412c.js","r",encoding="utf-8") as fp:
        data = fp.read()
   
    return Response(
        data,
        status=200,
        content_type="application/javascript"
    )


@bp.route("/x/space/v2/myinfo")

def my_info():

    json_data_20661512 = {
        "code": 0,
        "message": "OK",
        "data": {
            "profile": {
                "mid": 20661512,
                # "name": "可乐雪碧与薯片",
                "name":"账号已注销",
                "sex": "保密",
                # "face": "https://i0.hdslb.com/bfs/face/5df2e10e14c79500d6fdaf39fa29f136a37af8f5.jpg",
                "face":"https://i0.hdslb.com/bfs/face/member/noface.jpg",
                "sign": "",
                "rank": 10000,
                "level": 4,
                "jointime": 0,
                "moral": 70,
                "silence": 0,
                "email_status": 0,
                "tel_status": 1,
                "identification": 1,
                "vip": {
                    "type": 2,
                    "status": 1,
                    "due_date": 1756569600000,
                    "vip_pay_type": 0,
                    "theme_type": 0,
                    "label": {
                        "path": "",
                        "text": "年度大会员",
                        "label_theme": "annual_vip",
                        "text_color": "#FFFFFF",
                        "bg_style": 1,
                        "bg_color": "#FB7299",
                        "border_color": "",
                        "use_img_label": True,
                        "img_label_uri_hans": "",
                        "img_label_uri_hant": "",
                        "img_label_uri_hans_static": "https://i0.hdslb.com/bfs/vip/8d4f8bfc713826a5412a0a27eaaac4d6b9ede1d9.png",
                        "img_label_uri_hant_static": "https://i0.hdslb.com/bfs/activity-plat/static/20220614/e369244d0b14644f5e1a06431e22a4d5/VEW8fCC0hg.png"
                    },
                    "avatar_subscript": 1,
                    "username_color": "#FB7299",
                    "role": 3,
                    "avatar_subscript_url": "",
                    "tv_vip_status": 0,
                    "tv_vip_pay_type": 0,
                    "tv_due_date": 0,
                    "avatar_icon": {
                        "icon_type": 1,
                        "icon_resource": {}
                    }
                },
                "pendant": {
                    "pid": 0,
                    "name": "",
                    "image": "",
                    "expire": 0,
                    "image_enhance": "",
                    "image_enhance_frame": "",
                    "n_pid": 0
                },
                "nameplate": {
                    "nid": 62,
                    "name": "有爱大佬",
                    "image": "https://i1.hdslb.com/bfs/face/a10ee6b613e0d68d2dfdac8bbf71b94824e10408.png",
                    "image_small": "https://i1.hdslb.com/bfs/face/54f4c31ab9b1f1fa2c29dbbc967f66535699337e.png",
                    "level": "普通勋章",
                    "condition": "当前持有粉丝勋章最高等级\u003e=15级"
                },
                "official": {
                    "role": 0,
                    "title": "",
                    "desc": "",
                    "type": -1
                },
                "birthday": 315504000,
                "is_tourist": 0,
                "is_fake_account": 0,
                "pin_prompting": 0,
                "is_deleted": 0,
                "in_reg_audit": 0,
                "is_rip_user": False,
                "profession": {
                    "id": 0,
                    "name": "",
                    "show_name": "",
                    "is_show": 0,
                    "category_one": "",
                    "realname": "",
                    "title": "",
                    "department": "",
                    "certificate_no": "",
                    "certificate_show": False
                },
                "face_nft": 0,
                "face_nft_new": 0,
                "is_senior_member": 0,
                "honours": {
                    "mid": 20661512,
                    "colour": {
                        "dark": "#CE8620",
                        "normal": "#F0900B"
                    },
                    "tags": None,
                    "is_latest_100honour": 0
                },
                "digital_id": "",
                "digital_type": -2,
                "attestation": {
                    "type": 0,
                    "common_info": {
                        "title": "",
                        "prefix": "",
                        "prefix_title": ""
                    },
                    "splice_info": {
                        "title": ""
                    },
                    "icon": "",
                    "desc": ""
                },
                "expert_info": {
                    "title": "",
                    "state": 0,
                    "type": 0,
                    "desc": ""
                },
                "name_render": None,
                "country_code": "86"
            },
            "level_exp": {
                "current_level": 4,
                "current_min": 4500,
                "current_exp": 5414,
                "next_exp": 10800,
                "level_up": 1731516540
            },
            "coins": 129.4,
            "following": 38,
            "follower": 38
        },
        "ttl": 1
    }
    return Response(
        json.dumps(json_data_20661512),
        status=200,
        content_type="application/json"
    )
@bp.route("/x/space/wbi/acc/info")
def info():
    mid = request.args.get("mid")
    if (mid == "20661512"):
        json_data_20661512 = {
            "code": 0,
            "message": "0",
            "ttl": 1,
            "data": {
                "mid": 20661512,
                # "name": "可乐雪碧与薯片",
                "name":"账号已注销",
                "sex": "保密",
                # "face": "https://i0.hdslb.com/bfs/face/5df2e10e14c79500d6fdaf39fa29f136a37af8f5.jpg",
                "face":"https://i0.hdslb.com/bfs/face/member/noface.jpg",
                "face_nft": 0,
                "face_nft_type": 0,
                "sign": "",
                "rank": 10000,
                "level": 6,
                "jointime": 0,
                "moral": 0,
                "silence": 0,
                "coins": 129.4,
                "fans_badge": True,
                "fans_medal": {
                    "show": True,
                    "wear": True,
                    "medal": {
                        "uid": 20661512,
                        "target_id": 3493117653158382,
                        "medal_id": 955558,
                        "level": 22,
                        "medal_name": "已上船",
                        "medal_color": 1725515,
                        "intimacy": 569,
                        "next_intimacy": 2500,
                        "day_limit": 250000,
                        "medal_color_start": 1725515,
                        "medal_color_end": 5414290,
                        "medal_color_border": 1725515,
                        "is_lighted": 1,
                        "light_status": 1,
                        "wearing_status": 1,
                        "score": 50002569
                    }
                },
                "official": {
                    "role": 0,
                    "title": "",
                    "desc": "",
                    "type": -1
                },
                "vip": {
                    "type": 2,
                    "status": 1,
                    "due_date": 1756569600000,
                    "vip_pay_type": 0,
                    "theme_type": 0,
                    "label": {
                        "path": "",
                        "text": "年度大会员",
                        "label_theme": "annual_vip",
                        "text_color": "#FFFFFF",
                        "bg_style": 1,
                        "bg_color": "#FB7299",
                        "border_color": "",
                        "use_img_label": True,
                        "img_label_uri_hans": "",
                        "img_label_uri_hant": "",
                        "img_label_uri_hans_static": "https://i0.hdslb.com/bfs/vip/8d4f8bfc713826a5412a0a27eaaac4d6b9ede1d9.png",
                        "img_label_uri_hant_static": "https://i0.hdslb.com/bfs/activity-plat/static/20220614/e369244d0b14644f5e1a06431e22a4d5/VEW8fCC0hg.png"
                    },
                    "avatar_subscript": 1,
                    "nickname_color": "#FB7299",
                    "role": 3,
                    "avatar_subscript_url": "",
                    "tv_vip_status": 0,
                    "tv_vip_pay_type": 0,
                    "tv_due_date": 0,
                    "avatar_icon": {
                        "icon_type": 1,
                        "icon_resource": {}
                    }
                },
                "pendant": {
                    "pid": 0,
                    "name": "",
                    "image": "",
                    "expire": 0,
                    "image_enhance": "",
                    "image_enhance_frame": "",
                    "n_pid": 0
                },
                "nameplate": {
                    "nid": 62,
                    "name": "有爱大佬",
                    "image": "https://i1.hdslb.com/bfs/face/a10ee6b613e0d68d2dfdac8bbf71b94824e10408.png",
                    "image_small": "https://i1.hdslb.com/bfs/face/54f4c31ab9b1f1fa2c29dbbc967f66535699337e.png",
                    "level": "普通勋章",
                    "condition": "当前持有粉丝勋章最高等级\u003e=15级"
                },
                "user_honour_info": {
                    "mid": 0,
                    "colour": None,
                    "tags": [],
                    "is_latest_100honour": 0
                },
                "is_followed": False,
                "top_photo": "http://i2.hdslb.com/bfs/space/cb1c3ef50e22b6096fde67febe863494caefebad.png",
                "sys_notice": {},
                "live_room": {
                    "roomStatus": 1,
                    "liveStatus": 0,
                    "url": "https://live.bilibili.com/982629?broadcast_type=0\u0026is_room_feed=1",
                    "title": "玩游戏",
                    "cover": "https://i0.hdslb.com/bfs/live/new_room_cover/a94ae8dbcf02f8bfc997819a830423c3e76ffbe9.jpg",
                    "roomid": 982629,
                    "roundStatus": 0,
                    "broadcast_type": 0,
                    "watched_show": {
                        "switch": True,
                        "num": 1,
                        "text_small": "3250",
                        "text_large": "3250人看过",
                        "icon": "https://i0.hdslb.com/bfs/live/a725a9e61242ef44d764ac911691a7ce07f36c1d.png",
                        "icon_location": "",
                        "icon_web": "https://i0.hdslb.com/bfs/live/8d9d0f33ef8bf6f308742752d13dd0df731df19c.png"
                    }
                },
                "birthday": "01-01",
                "school": {
                    "name": ""
                },
                "profession": {
                    "name": "",
                    "department": "",
                    "title": "",
                    "is_show": 0
                },
                "tags": None,
                "series": {
                    "user_upgrade_status": 3,
                    "show_upgrade_window": False
                },
                "is_senior_member": 0,
                "mcn_info": None,
                "gaia_res_type": 0,
                "gaia_data": None,
                "is_risk": False,
                "elec": {
                    "show_info": {
                        "show": False,
                        "state": -1,
                        "title": "",
                        "icon": "",
                        "jump_url": "?oid=20661512"
                    }
                },
                "contract": {
                    "is_display": False,
                    "is_follow_display": False
                },
                "certificate_show": False,
                "name_render": None,
                "top_photo_v2": {
                    "sid": 1,
                    "l_img": "https://i2.hdslb.com/bfs/space/cb1c3ef50e22b6096fde67febe863494caefebad.png",
                    "l_200h_img": "https://i1.hdslb.com/bfs/activity-plat/static/Dw4uXtEwLB.png"
                },
                "theme": None
            }
        }
        return Response(
            json.dumps(json_data_20661512),
            status=200,
            content_type="application/json"
        )


# https://api.bilibili.com/x/space/wbi/acc/info?mid=20661512&token=&platform=web&web_location=1550101&dm_img_list=[]&dm_img_str=V2ViR0wgMS4wIChPcGVuR0wgRVMgMi4wIENocm9taXVtKQ&dm_cover_img_str=QU5HTEUgKE5WSURJQSwgTlZJRElBIEdlRm9yY2UgUlRYIDMwNjAgTGFwdG9wIEdQVSAoMHgwMDAwMjUyMCkgRGlyZWN0M0QxMSB2c181XzAgcHNfNV8wLCBEM0QxMSlHb29nbGUgSW5jLiAoTlZJRElBKQ&dm_img_inter=%7B%22ds%22:[],%22wh%22:[3893,2936,89],%22of%22:[261,522,261]%7D&w_webid=eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzcG1faWQiOiIzMzMuOTk5IiwiYnV2aWQiOiIzNDkzNUE3MC03N0FDLTEyRTktMTU3Ri05MDFFRjYzRTI0MTIwNzcwMWluZm9jIiwidXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChXaW5kb3dzIE5UIDEwLjA7IFdpbjY0OyB4NjQpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMzEuMC4wLjAgU2FmYXJpLzUzNy4zNiIsImJ1dmlkX2ZwIjoiZDk2MGUxNzI2YjE0MDQ3N2E3ZmZhMjA1ZTE0YTY4NmQiLCJiaWxpX3RpY2tldCI6ImV5SmhiR2NpT2lKSVV6STFOaUlzSW10cFpDSTZJbk13TXlJc0luUjVjQ0k2SWtwWFZDSjkuZXlKbGVIQWlPakUzTXpZM01qTTROVGdzSW1saGRDSTZNVGN6TmpRMk5EVTVPQ3dpY0d4MElqb3RNWDAuREl5NmlvN3dPNEk4Q0VyZ1V6a0tsZGlsOTF4Y244RmxBYzJUTE5ZN3lldyIsImNyZWF0ZWRfYXQiOjE3MzY2NjU0NDQsInR0bCI6ODY0MDAsInVybCI6Ii8yMDY2MTUxMi8iLCJyZXN1bHQiOjAsImlzcyI6ImdhaWEiLCJpYXQiOjE3MzY2NjU0NDR9.EnVuvbB6eRHuLYp6K-TCBOo3ANEvPdFTm9SWNzxm19cdC26s8ukblbk96-NwL8a16rK2pWKRlfvEYTYn-RINix10FS5nS1Q8H3AxrCVzXZpQKBMTNhg4fgH_djVq4FHl1y9yyNexr52_GxviUPcXPPd6iE3Digs3DvQRDbyu3ARRZqTFrhEbu_RMOFGHK5omj2X5TwZnR3-yjTL-7-w6_GdN8HG8ERgBeLT2VG6W9oMRV9ObHUVkzdCc_VVwBimAk8SrBjhL94MKBc-kOiWBjevsAVGLaWnNfqwrGYy-TpikeA14YoYmHB__sKaVflkWln2TxAYHlofpgp35sfbHOw&w_rid=66769026ead0487b90559cb01025dd6f&wts=1736665437