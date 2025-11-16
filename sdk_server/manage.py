# -*- coding:utf-8 -*-

from app import app, socketio,logger

import warnings
from app.utils.LoggerManager import logger
import logging
warnings.filterwarnings("ignore", category=RuntimeWarning, module="google_crc32c")



if __name__ == "__main__":
    try:
        socketio.run(
            app, 
            host="0.0.0.0", 
            port=5000, 
            debug=True, 
            use_reloader=False,
            allow_unsafe_werkzeug=True  # 允许在异步模式下使用调试功能
        )
    except Exception as e:
        logger.error(f"Failed to start server : {str(e)}")