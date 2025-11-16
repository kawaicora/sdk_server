from datetime import datetime
from app.extensions import db
from app.settings import DefaultConfig
from sqlalchemy.dialects.mysql import LONGTEXT,INTEGER,BIGINT,DATETIME
suffix = DefaultConfig.SUFFIX


# #######################################定义消息模型#####################################
class Message(db.Model):
    __tablename__ = suffix + 'messages'
    id = db.Column(INTEGER, primary_key=True, index=True)
    sender_uid = db.Column(INTEGER)
    recevice_uid = db.Column(INTEGER, default=-1)
    sender_sid = db.Column(db.String(255), default="")
    recevice_sid = db.Column(db.String(255), default="")
    room = db.Column(db.String(255), default="default")
    sender_username = db.Column(db.String(255), default="Anonymous")
    recevice_username = db.Column(db.String(255), default="Anonymous")
    type = db.Column(db.String(50))
    message = db.Column(db.String(1000))
    timestamp = db.Column(DATETIME, default=datetime.now)


# ####################################### 商品分类 #######################################
class ProductCategory(db.Model):
    __tablename__ = suffix + 'product_categories'
    __table_args__ = (
        db.Index('category_sort', 'sort_order'),
    )

    id = db.Column(INTEGER, primary_key=True, index=True)
    name = db.Column(db.String(100), nullable=False, default="")
    parent_id = db.Column(INTEGER, nullable=False, default=0)
    sort_order = db.Column(INTEGER, nullable=False, default=0)
    icon_url = db.Column(db.String(500), default="")
    create_time = db.Column(DATETIME, nullable=False, default=datetime.now)


# ####################################### 商品表 #######################################
class Product(db.Model):
    __tablename__ = suffix + 'products'
    __table_args__ = (
        db.Index('product_category', 'category_id'),
        db.Index('product_sales', 'sales_count'),
        db.Index('product_price', 'price'),
    )

    id = db.Column(INTEGER, primary_key=True, index=True)
    user_id = db.Column(BIGINT, nullable=False, default=0)
    name = db.Column(db.String(500), nullable=False, default="")
    subtitle = db.Column(db.String(1000), default="")
    price = db.Column(db.DECIMAL(10, 2), nullable=False, default=0.00)
    original_price = db.Column(db.DECIMAL(10, 2), default=0.00)
    category_id = db.Column(INTEGER, nullable=False, default=0)
    image_url = db.Column(db.String(500), default="")
    images = db.Column(LONGTEXT)
    detail_images = db.Column(LONGTEXT)
    sales_count = db.Column(INTEGER, nullable=False, default=0)
    stock = db.Column(INTEGER, nullable=False, default=0)
    sku = db.Column(db.String(100), default="")
    brand = db.Column(db.String(100), default="")
    material = db.Column(db.String(200), default="")
    size_info = db.Column(db.String(500), default="")
    weight = db.Column(db.String(50), default="")
    colors = db.Column(db.String(500), default="")
    sizes = db.Column(db.String(500), default="")
    description = db.Column(LONGTEXT)
    status = db.Column(INTEGER, nullable=False, default=1)
    create_time = db.Column(DATETIME, nullable=False, default=datetime.now)
    update_time = db.Column(DATETIME, nullable=False, default=datetime.now, onupdate=datetime.now)


# ####################################### 商品评价 #######################################
class ProductComment(db.Model):
    __tablename__ = suffix + 'product_comments'
    __table_args__ = (
        db.Index('comment_product', 'product_id'),
        db.Index('comment_time', 'create_time'),
    )

    id = db.Column(INTEGER, primary_key=True, index=True)
    product_id = db.Column(INTEGER, nullable=False, default=0)
    user_id = db.Column(BIGINT, nullable=False, default=0)
    username = db.Column(db.String(100), nullable=False, default="Anonymous")
    avatar = db.Column(db.String(500), default="")
    content = db.Column(LONGTEXT, nullable=False)
    images = db.Column(LONGTEXT)
    rating = db.Column(INTEGER, nullable=False, default=5)
    create_time = db.Column(DATETIME, nullable=False, default=datetime.now)
    reply_content = db.Column(LONGTEXT, default="")
    reply_time = db.Column(DATETIME)


# ####################################### WordPress 用户元数据 #######################################
class Usermeta(db.Model):
    __tablename__ = suffix + 'usermeta'

    umeta_id = db.Column(BIGINT, primary_key=True)
    user_id = db.Column(BIGINT, nullable=False, default=0)
    meta_key = db.Column(db.String(255))
    meta_value = db.Column(LONGTEXT)


# ####################################### WordPress 用户表 #######################################
class Users(db.Model):
    __tablename__ = suffix + 'users'
    __table_args__ = (
        db.Index('user_email', 'user_email'),
        db.Index('user_login_key', 'user_login'),
        db.Index('user_nicename', 'user_nicename'),
    )

    ID = db.Column(BIGINT, primary_key=True)
    user_login = db.Column(db.String(60), nullable=False, default="")
    user_pass = db.Column(db.String(255), nullable=False, default="")
    user_nicename = db.Column(db.String(50), nullable=False, default="")
    user_email = db.Column(db.String(100), nullable=False, default="")
    user_url = db.Column(db.String(100), nullable=False, default="")
    user_registered = db.Column(DATETIME, nullable=False, default=datetime.now)
    user_activation_key = db.Column(db.String(255), nullable=False, default="")
    user_status = db.Column(INTEGER, nullable=False, default=0)
    display_name = db.Column(db.String(250), nullable=False, default="")
    father_id = db.Column(INTEGER, nullable=False, default=0)
    reg_ip = db.Column(db.String(100), default="")


# ####################################### WordPress Options #######################################
class Options(db.Model):
    __tablename__ = suffix + 'options'

    option_id = db.Column(BIGINT, primary_key=True)
    option_name = db.Column(db.String(191), nullable=False, unique=True)
    option_value = db.Column(LONGTEXT, nullable=False)
    autoload = db.Column(db.String(20), nullable=False, default='yes')
