# -*- coding:utf-8 -*-
import os
import dotenv  # 导入 python-dotenv
dotenv.load_dotenv()
from app import app, socketio
from app.utils.LoggerManager import logger
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning, module="google_crc32c")



# 加载 .env 文件（优先加载项目根目录的 .env）
# load_dotenv() 会自动查找项目根目录的 .env 文件并加载到系统环境变量





if __name__ == "__main__":
    try:

        import os
        # 遍历所有环境变量并排序打印
        # for k, v in sorted(os.environ.items()):
        #     logger.info(f"{k} → {v}")
        socketio.run(
            app, 
            host=os.getenv("LISTEN_HOST","0.0.0.0"), 
            port=int(os.getenv("LISTEN_PORT",80)),
            debug=os.getenv("DEBUG",False), 
            use_reloader=False,
            allow_unsafe_werkzeug=True  # 允许在异步模式下使用调试功能
        )
    except Exception as e:
        logger.error(f"Failed to start server : {str(e)}")