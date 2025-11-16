import json
from flask import Response,Blueprint



bp = Blueprint('root', __name__)


@bp.route('/<path:url_path>',methods=['GET','POST'])
def last_roue(url_path):
    return Response(json.dumps({"code":-1}), status=404, content_type='application/json')
    
# 注册服务
import app.route.dispatch_service
import app.route.account_service
import app.route.view_service
import app.route.socketio_common_services
import app.route.webrtc_service
import app.route.chat_service
import app.route.sync_service
import app.route.whip_service
import app.route.shop_service
import app.route.device_controller_service