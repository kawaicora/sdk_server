




import traceback
from app.utils.LoggerManager import logger
from flask import Flask
from flask_cors import CORS
from app.settings import DefaultConfig
from app.extensions import socketio, db
from app.route import bp

# 创建 Flask 应用
app:Flask = Flask(__name__, 
           instance_relative_config=True,
           template_folder=DefaultConfig.TEMPLATES_FOLDER,
           static_folder=DefaultConfig.STATIC_FOLDER)

# 初始化日志管理器

app.logger = logger

# 加载配置文件
app.config.from_object(DefaultConfig)
logger.info("config load successfully")

# 设置路径信息
app.root_path = DefaultConfig.BASE_DIR
# 配置跨域支持
CORS(app, supports_credentials=True)

# 注册蓝图
app.register_blueprint(bp)

# 初始化扩展
db.init_app(app)
logger.info("database init successfully")
socketio.init_app(app)
logger.info("socketio init successfully")



# 创建数据库表
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        # 打印完整的异常堆栈（包含错误位置和详情）
        logger.error(f"Failed to create database tables: {str(e)}")
        logger.error(traceback.format_exc())  # 新增这行，打印完整错误栈


