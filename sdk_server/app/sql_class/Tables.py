from datetime import date, datetime
from zoneinfo import ZoneInfo
from app.extensions import db
from app.settings import DefaultConfig
from sqlalchemy.dialects.mysql import LONGTEXT,INTEGER,BIGINT,DATETIME,TEXT,TINYTEXT,VARCHAR,DOUBLE,DECIMAL,DATE,TINYINT,TINYBLOB,BLOB,BOOLEAN
suffix = DefaultConfig.SUFFIX







# #######################################游戏账号SDK模型#####################################
class GameAccount(db.Model):
    __tablename__ = suffix + 'game_account'


    ID = db.Column(BIGINT, primary_key=True)
    token = db.Column(VARCHAR(255),nullable=False, default="")
    


# #######################################定义消息模型#####################################
class Message(db.Model):
    __tablename__ = suffix + 'messages'
    ID = db.Column(BIGINT ,primary_key=True, index=True)
    sender_uid = db.Column(BIGINT,nullable=False)
    recevice_uid = db.Column(INTEGER,nullable=False, default=0)
    sender_sid = db.Column(VARCHAR(255),nullable=False, default="")
    recevice_sid = db.Column(VARCHAR(255),nullable=False, default="")
    room = db.Column(VARCHAR(255),nullable=False, default="default")
    sender_username = db.Column(VARCHAR(255),nullable=False, default="")
    recevice_username = db.Column(VARCHAR(255),nullable=False, default="")
    type = db.Column(VARCHAR(50))
    message = db.Column(LONGTEXT,nullable=False)
    timestamp = db.Column(DATETIME,nullable=False, default=datetime.now)
# #######################################房间模型#####################################
class Room(db.Model):
    __tablename__ = suffix + 'room'

    ID = db.Column(BIGINT, primary_key=True, autoincrement=True)

    room_id = db.Column(VARCHAR(64), nullable=False, unique=True, default="")
    title = db.Column(VARCHAR(255), nullable=False, default="")
    desc = db.Column(TEXT, nullable=False, default="")

    password = db.Column(VARCHAR(255), nullable=False, default="")

    cover = db.Column(VARCHAR(255), nullable=False, default="")

    creator = db.Column(BIGINT, nullable=False)

    room_type = db.Column(VARCHAR(32), nullable=False, default="chat")

    create_time = db.Column(BIGINT, nullable=False, default=0)
    updated_time = db.Column(BIGINT, nullable=True)
    deleted_time = db.Column(BIGINT, nullable=True)

class RoomUser(db.Model):
    __tablename__ = suffix + 'room_user'

    ID = db.Column(BIGINT, primary_key=True, autoincrement=True)

    room_id = db.Column(VARCHAR(64), nullable=False, index=True)

    uid = db.Column(BIGINT, nullable=False)

    join_time = db.Column(BIGINT, nullable=False)

class RoomBanUser(db.Model):
    __tablename__ = suffix + 'room_ban_user'

    ID = db.Column(BIGINT, primary_key=True, autoincrement=True)

    room_id = db.Column(VARCHAR(64), nullable=False, index=True)

    uid = db.Column(BIGINT, nullable=False)

    ban_time = db.Column(BIGINT, nullable=False, default=0)

# ####################################### 商品分类 #######################################
class ProductCategory(db.Model):
    __tablename__ = suffix + 'product_categories'
    __table_args__ = (
        db.Index('category_sort', 'sort_order'),
    )

    ID = db.Column(INTEGER, primary_key=True, index=True)
    name = db.Column(VARCHAR(100), nullable=False, default="")
    parent_id = db.Column(INTEGER, nullable=False, default=0)
    sort_order = db.Column(INTEGER, nullable=False, default=0)
    icon_url = db.Column(VARCHAR(500), default="")
    create_time = db.Column(DATETIME, nullable=False, default=datetime.now)


# ####################################### 商品表 #######################################
class Product(db.Model):
    __tablename__ = suffix + 'products'
    __table_args__ = (
        db.Index('product_category', 'category_id'),
        db.Index('product_sales', 'sales_count'),
        db.Index('product_price', 'price'),
    )

    ID = db.Column(BIGINT, primary_key=True,index=True)
    user_id = db.Column(BIGINT, nullable=False, default=0)
    name = db.Column(VARCHAR(500), nullable=False, default="")
    subtitle = db.Column(VARCHAR(1000), default="")
    price = db.Column(DECIMAL(10, 2), nullable=False, default=0.00)
    original_price = db.Column(DECIMAL(10, 2), default=0.00)
    category_id = db.Column(INTEGER, nullable=False, default=0)
    image_url = db.Column(VARCHAR(500), default="")
    images = db.Column(LONGTEXT)
    detail_images = db.Column(LONGTEXT)
    sales_count = db.Column(INTEGER, nullable=False, default=0)
    stock = db.Column(INTEGER, nullable=False, default=0)
    sku = db.Column(VARCHAR(100), default="")
    brand = db.Column(VARCHAR(100), default="")
    material = db.Column(VARCHAR(200), default="")
    size_info = db.Column(VARCHAR(500), default="")
    weight = db.Column(VARCHAR(50), default="")
    colors = db.Column(VARCHAR(500), default="")
    sizes = db.Column(VARCHAR(500), default="")
    description = db.Column(LONGTEXT)
    status = db.Column(INTEGER, nullable=False, default=1)
    create_time = db.Column(DATETIME, nullable=False, default=datetime.now)
    update_time = db.Column(DATETIME, nullable=False, default=datetime.now, onupdate=datetime.now)


# ####################################### 论坛内容 #######################################
class Forums(db.Model):
    __tablename__ = suffix + 'forums'
    ID = db.Column(BIGINT(20), primary_key=True,index=True)
    forum_author = db.Column(BIGINT(20) ,nullable=False,default=0)
    forum_date = db.Column(DATETIME,nullable=False,default=datetime.now)
    forum_date_gmt = db.Column(DATETIME,nullable=False,default=lambda: datetime.now(ZoneInfo("UTC")) )
    forum_content = db.Column(LONGTEXT,nullable=False)
    forum_content_type = db.Column(LONGTEXT,default="html") # html md 
    forum_title = db.Column(LONGTEXT, nullable=False)
    forum_status =  db.Column(VARCHAR(20),nullable=False,default="private") # publish draft inherit
    comment_status = db.Column(VARCHAR(20),nullable=False,default="closed") # open closed
    ping_statue = db.Column(VARCHAR(20),nullable=False,default="closed") # open closed
    forum_password = db.Column(VARCHAR(200),nullable=False,default="")
    forum_name = db.Column(VARCHAR(200),nullable=False,default="")
    forum_modified = db.Column(DATETIME,nullable=False,default=datetime.now)
    forum_modified_gmt	= db.Column(DATETIME,default=lambda: datetime.now(ZoneInfo("UTC")))
    forum_content_filtered = db.Column(TEXT,nullable=False,default="")    # ""  暂不使用
    forum_parent = db.Column(INTEGER,default=0)
    guid = db.Column(VARCHAR(255),nullable=False,default="")   # 访问地址 暂不使用
    menu_order = db.Column(INTEGER,nullable=False,default=0)  #暂不使用
    forum_type = db.Column(VARCHAR(20),nullable=False)  #post  forum  page  revision attachment
    forum_mime_type = db.Column(VARCHAR(20),nullable=False,default = "")
    comment_count = db.Column(BIGINT,nullable=False,default = 0)
# ####################################### 论坛评论 #######################################
class ForumComment(db.Model):
    __tablename__ = suffix + 'forum_comment'
    ID = db.Column(BIGINT, primary_key=True,index=True)
    comment_forum_id = db.Column(BIGINT,nullable=False)
    comment_author = db.Column(TINYTEXT,nullable=False)
    comment_date = db.Column(DATETIME,nullable=False,default=datetime.now)
    comment_date_gmt = db.Column(DATETIME,nullable=False,default=lambda: datetime.now(ZoneInfo("UTC")) )
    comment_content = db.Column(LONGTEXT,nullable=False)
    comment_content_type = db.Column(LONGTEXT,nullable=False,default="text") # text html md
    comment_approved = db.Column(VARCHAR(20),nullable=False,default='0') #评论是否过审显示
    comment_type = db.Column(VARCHAR(20),nullable=False,default = "comment")
    comment_parent = db.Column(INTEGER,nullable=False,default=0)
    user_id =db.Column(BIGINT,nullable=False,default =0)

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
    username = db.Column(VARCHAR(100), nullable=False, default="")
    avatar = db.Column(VARCHAR(500), default="")
    content = db.Column(LONGTEXT, nullable=False)
    images = db.Column(LONGTEXT)
    rating = db.Column(INTEGER, nullable=False, default=5)
    create_time = db.Column(DATETIME, nullable=False, default=datetime.now)
    reply_content = db.Column(LONGTEXT, default="")
    reply_time = db.Column(DATETIME)


# ####################################### 货币表 ###########################################


class IceInfo(db.Model):
    __tablename__ = suffix + 'ice_info'
    ice_id = db.Column(INTEGER, primary_key=True, index=True)
    ice_have_money = db.Column(DOUBLE(10,2),nullable=False)
    ice_user_id = db.Column(INTEGER,nullable=False)
    ice_get_money =  db.Column(DOUBLE(10,2),nullable=False)
    ice_have_aff = db.Column(DOUBLE(10,2),nullable=True,default=0.00)
    ice_get_aff =  db.Column(DOUBLE(10,2),nullable=True,default=0.00)
    ice_ip  = db.Column(VARCHAR(50),nullable=True)
    userType  =db.Column(TINYINT,default = 0,nullable=False)
    endTime = db.Column(DATE,default=date(1000, 1, 1),nullable=False)
# ####################################### WordPress 用户元数据 #######################################
class Usermeta(db.Model):
    __tablename__ = suffix + 'usermeta'

    umeta_id = db.Column(BIGINT, primary_key=True)
    user_id = db.Column(BIGINT, nullable=False, default=0)
    meta_key = db.Column(VARCHAR(255))
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
    user_login = db.Column(VARCHAR(60), nullable=False, default="")
    user_pass = db.Column(VARCHAR(255), nullable=False, default="")
    user_nicename = db.Column(VARCHAR(50), nullable=False, default="")
    user_email = db.Column(VARCHAR(100), nullable=False, default="")
    user_url = db.Column(VARCHAR(100), nullable=False, default="")
    user_registered = db.Column(DATETIME, nullable=False, default=datetime.now)
    user_activation_key = db.Column(VARCHAR(255), nullable=False, default="")
    user_status = db.Column(INTEGER, nullable=False, default=0)
    display_name = db.Column(VARCHAR(250), nullable=False, default="")
    father_id = db.Column(INTEGER, nullable=False, default=0)
    reg_ip = db.Column(VARCHAR(100), default="")


# ####################################### WordPress Options #######################################
class Options(db.Model):
    __tablename__ = suffix + 'options'

    option_id = db.Column(BIGINT, primary_key=True)
    option_name = db.Column(VARCHAR(191), nullable=False, unique=True)
    option_value = db.Column(LONGTEXT, nullable=False)
    autoload = db.Column(VARCHAR(20), nullable=False, default='yes')



