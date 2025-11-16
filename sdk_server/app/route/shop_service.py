import os
import base64
from datetime import datetime
import io
import secrets
from app.route import bp
from app.sql_class.Tables import Users, Usermeta, ProductCategory, Product, ProductComment  # 导入ORM模型
from flask import *
from app.settings import *
import gzip
import yaml
from app.extensions import db  # 导入SQLAlchemy实例
from app.utils.ErrorCode import get_response_string
import xml.etree.ElementTree as ET


# -------------------------- 数据库工具函数 --------------------------
def init_db():
    """初始化数据库（创建表并插入测试数据）"""
    # 注意：实际项目中应使用迁移工具（如Flask-Migrate）管理表结构
    db.create_all()  # 创建所有模型对应的表（仅首次运行有效）
    
    # 插入测试分类（避免重复插入）
    if not ProductCategory.query.first():
        categories = [
            ProductCategory(name="手机数码", sort_order=1),
            ProductCategory(name="电脑办公", sort_order=2),
            ProductCategory(name="家用电器", sort_order=3),
            ProductCategory(name="服装鞋帽", sort_order=4)
        ]
        db.session.add_all(categories)
        db.session.commit()
    
    # 插入测试商品（避免重复插入）
    if not Product.query.first():
        # 获取第一个分类作为默认分类
        default_category = ProductCategory.query.first()
        if default_category:
            product1 = Product(
                name="旗舰款智能手机",
                subtitle="5G全网通，超大内存，超长续航",
                price=3999.00,
                original_price=4599.00,
                category_id=default_category.id,
                image_url="https://picsum.photos/450/450?random=1",
                images="https://picsum.photos/80/80?random=11,https://picsum.photos/80/80?random=12",
                detail_images="https://picsum.photos/800/400?random=101,https://picsum.photos/800/400?random=102",
                sales_count=1200,
                stock=500,
                sku="JD10001",
                brand="XX品牌",
                material="玻璃+金属",
                size_info="6.7英寸",
                weight="约200g",
                colors="黑色,白色,蓝色",
                sizes="8GB+128GB,8GB+256GB",
                description="<p>【旗舰配置】搭载最新处理器，性能强劲...</p>",
                status=1
            )
            db.session.add(product1)
            db.session.commit()
            
            # 添加测试评价
            comment1 = ProductComment(
                product_id=product1.id,
                user_id=1,
                username="用户123",
                content="手机很好用，续航特别强！",
                images="https://picsum.photos/100/100?random=comment11",
                rating=5
            )
            db.session.add(comment1)
            db.session.commit()


# -------------------------- 核心路由 --------------------------


@bp.route('/view/products')
def product_list():
    """商品列表页：支持分类筛选、搜索、排序（使用ORM查询）"""
    # 1. 获取请求参数
    category_id = request.args.get('category', '').strip()
    search_query = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'sales_desc')

    # 2. 构建ORM查询
    query = Product.query

    # 分类筛选
    if category_id and category_id.isdigit():
        query = query.filter(Product.category_id == int(category_id))

    # 搜索筛选（匹配商品名称）
    if search_query:
        query = query.filter(Product.name.like(f'%{search_query}%'))

    # 排序逻辑
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    else:  # 默认按销量降序
        query = query.order_by(Product.sales_count.desc())

    # 执行查询
    products = query.all()

    # 3. 获取所有分类（用于筛选下拉框）
    categories = ProductCategory.query.order_by(ProductCategory.sort_order.asc()).all()

    # 4. 转换模型对象为字典（处理复杂字段）
    products_dict = []
    for p in products:
        product = {
            'id': p.id,
            'name': p.name,
            'subtitle': p.subtitle,
            'price': p.price,
            'original_price': p.original_price,
            'category_id': p.category_id,
            'image_url': p.image_url,
            'sales_count': p.sales_count,
            'stock': p.stock,
            # 处理逗号分隔的字段（转为列表）
            'images': p.images.split(',') if p.images else [],
            'colors': p.colors.split(',') if p.colors else [],
            'sizes': p.sizes.split(',') if p.sizes else []
        }
        products_dict.append(product)

    # 5. 渲染模板
    return render_template(
        'product_list.html',
        products=products_dict,
        categories=categories,
        selected_category=category_id,
        search_query=search_query
    )


@bp.route('/view/product/<int:product_id>')
def product_detail(product_id):
    """商品详情页：使用ORM查询商品及评价"""
    # 1. 查询商品详情（使用ORM的get方法）
    product = Product.query.get(product_id)

    # 商品不存在时返回404
    if not product:
        return render_template('404.html'), 404

    # 2. 查询商品评价（关联查询）
    comments = ProductComment.query.filter_by(product_id=product_id).order_by(ProductComment.create_time.desc()).all()

    # 3. 转换模型对象为字典（处理复杂字段）
    product_dict = {
        'id': product.id,
        'name': product.name,
        'subtitle': product.subtitle,
        'price': product.price,
        'original_price': product.original_price,
        'category_id': product.category_id,
        'image_url': product.image_url,
        'sales_count': product.sales_count,
        'stock': product.stock,
        'sku': product.sku,
        'brand': product.brand,
        'material': product.material,
        'size_info': product.size_info,
        'weight': product.weight,
        'description': product.description,
        # 处理逗号分隔的字段
        'images': product.images.split(',') if product.images else [],
        'detail_images': product.detail_images.split(',') if product.detail_images else [],
        'colors': product.colors.split(',') if product.colors else [],
        'sizes': product.sizes.split(',') if product.sizes else []
    }

    # 处理评价列表
    comments_dict = []
    for c in comments:
        comments_dict.append({
            'id': c.id,
            'product_id': c.product_id,
            'username': c.username,
            'avatar': c.avatar,
            'content': c.content,
            'rating': c.rating,
            'create_time': c.create_time,
            'images': c.images.split(',') if c.images else []
        })
    product_dict['comments'] = comments_dict

    # 4. 渲染模板
    return render_template('product_detail.html', product=product_dict)


@bp.route('/init-db')
def init_db_route():
    """初始化数据库的路由（仅测试用）"""
    init_db()
    return '数据库初始化完成！请关闭此路由（/init-db）后再上线。'
    