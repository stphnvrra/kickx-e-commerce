from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify, g
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, logout_user, login_required, current_user, login_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import os
from sqlalchemy import Integer, String, Text, Float, Boolean, ForeignKey, DateTime, JSON, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase
from werkzeug.utils import secure_filename
import time
import numpy as np
import pandas as pd
from recommendation_engine import init_recommendation_engine, get_recommendation_engine
from paypal_config import get_paypal_config, PAYPAL_JS_SDK_URL
from paypal_service import PayPalService

# Initialize PayPal service
paypal_service = PayPalService()

# Application Configuration
app = Flask(__name__)
bootstrap=Bootstrap5(app)

app.config['SECRET_KEY'] = '^wXer#e*we*$&wxQ^@*&@3'
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///kickx.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Login manager setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# File upload settings
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max upload

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database Models
class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128))
    first_name: Mapped[str] = mapped_column(String(64), nullable=True)
    last_name: Mapped[str] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    orders = relationship('Order', back_populates='user', lazy='dynamic')
    reviews = relationship('Review', back_populates='user', lazy='dynamic')
    cart = relationship('Cart', back_populates='user', uselist=False)
    wishlist = relationship('Wishlist', back_populates='user', uselist=False)
    addresses = relationship('Address', back_populates='user', lazy='dynamic')
    notifications = relationship('Notification', back_populates='user', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
        
    @property
    def unread_notifications_count(self):
        """Get the count of unread notifications for this user"""
        try:
            return Notification.query.filter_by(user_id=self.id, is_read=False).count()
        except Exception as e:
            # Handle case where table might not exist yet
            print(f"Error getting unread notifications count: {str(e)}")
            return 0

class Address(db.Model):
    __tablename__ = 'addresses'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    street_address: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='addresses')

class Category(db.Model):
    __tablename__ = 'category'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    products = relationship('Product', back_populates='category', lazy='dynamic')

class Brand(db.Model):
    __tablename__ = 'brand'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    products = relationship('Product', back_populates='brand', lazy='dynamic')

class Size(db.Model):
    __tablename__ = 'size'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    value: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    display_order: Mapped[int] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    product_sizes = relationship('ProductSize', back_populates='size', lazy='dynamic')

class Product(db.Model):
    __tablename__ = 'product'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    discount_price: Mapped[float] = mapped_column(Float, nullable=True)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str] = mapped_column(String(255), nullable=True)
    release_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)
    views: Mapped[int] = mapped_column(Integer, default=0)
    color: Mapped[str] = mapped_column(String(20), nullable=True)
    style_code: Mapped[str] = mapped_column(String(20), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey('category.id'), nullable=True)
    brand_id: Mapped[int] = mapped_column(ForeignKey('brand.id'), nullable=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Relationships
    category = relationship('Category', back_populates='products')
    brand = relationship('Brand', back_populates='products')
    product_sizes = relationship('ProductSize', back_populates='product', lazy='dynamic', cascade='all, delete-orphan')
    order_items = relationship('OrderItem', back_populates='product_info', lazy='dynamic')
    cart_items = relationship('CartItem', back_populates='product', lazy='dynamic')
    wishlist_items = relationship('WishlistItem', back_populates='product', lazy='dynamic')
    reviews = relationship('Review', back_populates='product', lazy='dynamic', cascade='all, delete-orphan')

class ProductSize(db.Model):
    __tablename__ = 'product_size'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id'), nullable=False)
    size_id: Mapped[int] = mapped_column(ForeignKey('size.id'), nullable=False)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    product = relationship('Product', back_populates='product_sizes')
    size = relationship('Size', back_populates='product_sizes')

class Order(db.Model):
    __tablename__ = 'order'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending')
    payment_status: Mapped[str] = mapped_column(String(20), default='pending')
    payment_id: Mapped[str] = mapped_column(String(64), nullable=True)
    payment_method: Mapped[str] = mapped_column(String(20), default='paypal')
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    shipping_address: Mapped[str] = mapped_column(Text, nullable=False)
    shipping_city: Mapped[str] = mapped_column(String(64), nullable=False)
    shipping_state: Mapped[str] = mapped_column(String(64), nullable=False)
    shipping_zip: Mapped[str] = mapped_column(String(20), nullable=False)
    shipping_country: Mapped[str] = mapped_column(String(64), nullable=False)
    tracking_number: Mapped[str] = mapped_column(String(64), nullable=True)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    discount_amount: Mapped[float] = mapped_column(Float, default=0.0)
    processing_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    shipping_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    delivery_date: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='orders')
    items = relationship('OrderItem', back_populates='order', lazy='dynamic', cascade='all, delete-orphan')

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey('order.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[str] = mapped_column(String(10), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    order = relationship('Order', back_populates='items')
    product_info = relationship('Product', back_populates='order_items')

class Cart(db.Model):
    __tablename__ = 'cart'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='cart')
    items = relationship('CartItem', back_populates='cart', lazy='dynamic', cascade='all, delete-orphan')

class CartItem(db.Model):
    __tablename__ = 'cart_item'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey('cart.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id'), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    size: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    cart = relationship('Cart', back_populates='items')
    product = relationship('Product', back_populates='cart_items')

class Wishlist(db.Model):
    __tablename__ = 'wishlist'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='wishlist')
    items = relationship('WishlistItem', back_populates='wishlist', lazy='dynamic', cascade='all, delete-orphan')

class WishlistItem(db.Model):
    __tablename__ = 'wishlist_item'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    wishlist_id: Mapped[int] = mapped_column(ForeignKey('wishlist.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id'), nullable=False)
    size_id: Mapped[int] = mapped_column(ForeignKey('size.id'), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    size: Mapped[str] = mapped_column(String(10), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    wishlist = relationship('Wishlist', back_populates='items')
    product = relationship('Product', back_populates='wishlist_items')
    size_info = relationship('Size', foreign_keys=[size_id])

class Review(db.Model):
    __tablename__ = 'review'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey('product.id'), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='reviews')
    product = relationship('Product', back_populates='reviews')

class NotificationSettings(db.Model):
    __tablename__ = 'notification_settings'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    new_arrival_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    restock_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    price_drop_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    exclusive_drop_notifications: Mapped[bool] = mapped_column(Boolean, default=True)
    notification_cooldown_hours: Mapped[int] = mapped_column(Integer, default=24)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

class Notification(db.Model):
    __tablename__ = 'notifications'
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # new_arrival, sale, exclusive, etc.
    message: Mapped[str] = mapped_column(String(255), nullable=False)
    link: Mapped[str] = mapped_column(String(255), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    related_product_id: Mapped[int] = mapped_column(ForeignKey('product.id'), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='notifications')
    related_product = relationship('Product')

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Main Routes
@app.route('/')
def index():
    featured_products = Product.query.filter_by(featured=True).limit(8).all()
    new_arrivals = Product.query.order_by(Product.created_at.desc()).limit(8).all()


    
    # Get trending products from recommendation engine
    recommendation_engine = get_recommendation_engine()
    if recommendation_engine is None:
        recommendation_engine = init_recommendation_engine(db)
    
    # Get trending products
    try:
        trending_products = recommendation_engine.get_trending_products(8)
        trending_product_ids = [p['id'] for p in trending_products]
        trending = Product.query.filter(Product.id.in_(trending_product_ids)).all()
        
        # Order by the original trending order
        id_to_position = {p['id']: i for i, p in enumerate(trending_products)}
        trending.sort(key=lambda p: id_to_position.get(p.id, 999))
    except Exception as e:
        print(f"Error getting trending products: {str(e)}")
        # Fallback to view count if recommendation engine fails
    trending = Product.query.order_by(Product.views.desc()).limit(8).all()
    
    # Get personalized recommendations for logged-in users
    personalized_recommendations = []
    if current_user.is_authenticated:
        settings = recommendation_engine.load_settings()
        if settings.get('enable_personalized_home', True):
            try:
                personalized_recs = recommendation_engine.get_personalized_recommendations(current_user.id, 8)
                if personalized_recs:
                    personalized_product_ids = [p['id'] for p in personalized_recs]
                    personalized_recommendations = Product.query.filter(Product.id.in_(personalized_product_ids)).all()
                    
                    # Order by the original recommendation order
                    id_to_position = {p['id']: i for i, p in enumerate(personalized_recs)}
                    personalized_recommendations.sort(key=lambda p: id_to_position.get(p.id, 999))
            except Exception as e:
                print(f"Error getting personalized recommendations: {str(e)}")
    
    return render_template('main/index.html', 
                           featured_products=featured_products,
                           new_arrivals=new_arrivals,
                          trending=trending,
                          personalized_recommendations=personalized_recommendations)

@app.route('/search')
def search():
    query = request.args.get('q', '')
    products = []
    if query:
        products = Product.query.filter(Product.name.contains(query)).all()
        
        # Mark items that are in user's wishlist if logged in
        for product in products:
            product.in_wishlist = False
            if current_user.is_authenticated:
                wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
                if wishlist:
                    in_wishlist = WishlistItem.query.filter_by(
                        wishlist_id=wishlist.id, 
                        product_id=product.id
                    ).first() is not None
                    product.in_wishlist = in_wishlist
        
        # Calculate number of reviews for each product
        for product in products:
            product.num_reviews = Review.query.filter_by(product_id=product.id).count()
            
    return render_template('products/search_results.html', products=products, query=query)

@app.route('/featured')
def featured():
    featured_products = Product.query.filter_by(featured=True).all()
    return render_template('main/featured.html', products=featured_products)

# Product Routes
@app.route('/products')
def product_catalog():
    # Get query parameters for filtering and sorting@
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'newest')
    category_ids = request.args.getlist('category')
    brand_ids = request.args.getlist('brand')
    size_values = request.args.getlist('size')
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    verified_only = request.args.get('verified') == '1'
    
    # Base query
    query = Product.query
    
    # Apply category filter
    if category_ids:
        query = query.filter(Product.category_id.in_(category_ids))
    
    # Apply brand filter
    if brand_ids:
        query = query.filter(Product.brand_id.in_(brand_ids))
    
    # Apply verified filter
    if verified_only:
        query = query.filter(Product.is_verified == True)
    
    # Apply size filter
    if size_values:
        # Get size IDs from values
        size_ids = Size.query.filter(Size.value.in_(size_values)).with_entities(Size.id).all()
        size_ids = [s.id for s in size_ids]
        
        # Find products with these sizes that have stock
        product_ids = ProductSize.query.filter(
            ProductSize.size_id.in_(size_ids),
            ProductSize.stock > 0
        ).with_entities(ProductSize.product_id).distinct().all()
        
        product_ids = [p.product_id for p in product_ids]
        query = query.filter(Product.id.in_(product_ids))
    
    # Apply price range filter
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    # Apply sorting
    if sort == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort == 'price_low':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_high':
        query = query.order_by(Product.price.desc())
    elif sort == 'popular':
        query = query.order_by(Product.views.desc())
    
    # Pagination
    products = query.paginate(page=page, per_page=12)
    
    # Get categories and brands for filter sidebar
    categories = Category.query.all()
    brands = Brand.query.all()
    
    # Get all available sizes
    sizes = [s.value for s in Size.query.order_by(Size.display_order).all()]
    
    # Mark items that are in user's wishlist if logged in
    for product in products.items:
        product.in_wishlist = False
        if current_user.is_authenticated:
            wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
            if wishlist:
                in_wishlist = WishlistItem.query.filter_by(
                    wishlist_id=wishlist.id, 
                    product_id=product.id
                ).first() is not None
                product.in_wishlist = in_wishlist
    
    # Calculate number of reviews for each product
    for product in products.items:
        product.num_reviews = Review.query.filter_by(product_id=product.id).count()
    
    return render_template('products/catalog.html', 
                          products=products,
                          categories=categories,
                          brands=brands,
                          sizes=sizes)

@app.route('/products/new-arrivals')
def new_arrivals():
    products = Product.query.order_by(Product.created_at.desc()).limit(12).all()
    
    # Mark items that are in user's wishlist if logged in
    for product in products:
        product.in_wishlist = False
        if current_user.is_authenticated:
            wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
            if wishlist:
                in_wishlist = WishlistItem.query.filter_by(
                    wishlist_id=wishlist.id, 
                    product_id=product.id
                ).first() is not None
                product.in_wishlist = in_wishlist
    
    # Calculate number of reviews for each product
    for product in products:
        product.num_reviews = Review.query.filter_by(product_id=product.id).count()
        
    return render_template('products/new_arrivals.html', products=products)

@app.route('/products/trending')
def trending_products():
    products = Product.query.order_by(Product.views.desc()).limit(12).all()
    
    # Mark items that are in user's wishlist if logged in
    for product in products:
        product.in_wishlist = False
        if current_user.is_authenticated:
            wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
            if wishlist:
                in_wishlist = WishlistItem.query.filter_by(
                    wishlist_id=wishlist.id, 
                    product_id=product.id
                ).first() is not None
                product.in_wishlist = in_wishlist
    
    # Calculate number of reviews for each product
    for product in products:
        product.num_reviews = Review.query.filter_by(product_id=product.id).count()
        
    return render_template('products/trending.html', products=products)

@app.route('/products/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    
    # Increment view count
    product.views += 1
    db.session.commit()
    
    # Get product sizes with inventory
    product_sizes = (ProductSize.query
                    .join(Size)
                    .filter(ProductSize.product_id == product.id)
                    .order_by(Size.display_order)
                    .all())

    # Get related products using recommendation engine
    recommendation_engine = get_recommendation_engine()
    if recommendation_engine is None:
        recommendation_engine = init_recommendation_engine(db)
        
    recommended_products = []
    recommendations = []
    try:
        # Get recommendations from the engine
        recommendations = recommendation_engine.get_recommendations(product.id)
        
        # Convert recommendation objects to actual Product objects
        if recommendations:
            recommended_product_ids = [rec['id'] for rec in recommendations]
            recommended_products = Product.query.filter(Product.id.in_(recommended_product_ids)).all()
            
            # Sort based on the original recommendation order
            id_to_position = {rec['id']: i for i, rec in enumerate(recommendations)}
            recommended_products.sort(key=lambda p: id_to_position.get(p.id, 999))
    except Exception as e:
        print(f"Error getting recommendations: {str(e)}")
    
    # Use traditional related products as fallback
    if not recommended_products:
        recommended_products = (Product.query
                       .filter_by(brand_id=product.brand_id)
                       .filter(Product.id != product.id)
                       .limit(4)
                       .all())
        # Create basic recommendations for the fallback products
        recommendations = [{'id': p.id, 'reason': 'same_brand'} for p in recommended_products]
    
    # Get review data
    reviews = Review.query.filter_by(product_id=product.id).order_by(Review.created_at.desc()).all()
    
    # Calculate average rating
    average_rating = 0
    if reviews:
        average_rating = sum(review.rating for review in reviews) / len(reviews)
    
    # Generate rating distribution
    rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for review in reviews:
        rating_distribution[review.rating] += 1
    
    # Flag product as in wishlist if user is logged in
    in_wishlist = False
    if current_user.is_authenticated:
        wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
        if wishlist:
            wishlist_item = WishlistItem.query.filter_by(
                wishlist_id=wishlist.id,
                product_id=product.id
            ).first()
            if wishlist_item:
                in_wishlist = True
    
    return render_template(
        'products/detail.html', 
        product=product,
        product_sizes=product_sizes,
        related_products=recommended_products,
        recommendations=recommendations,
        reviews=reviews,
        num_reviews=len(reviews),
        average_rating=average_rating,
        rating_distribution=rating_distribution,
        in_wishlist=in_wishlist
    )

@app.route('/brands/<slug>')
def brand_products(slug):
    brand = Brand.query.filter_by(slug=slug).first_or_404()
    products = Product.query.filter_by(brand_id=brand.id).all()
    return render_template('products/brand.html', brand=brand, products=products)

@app.route('/categories/<slug>')
def category_products(slug):
    category = Category.query.filter_by(slug=slug).first_or_404()
    products = Product.query.filter_by(category_id=category.id).all()
    return render_template('products/category.html', category=category, products=products)

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Please check your login details and try again.', 'danger')
            return redirect(url_for('login'))
        
        # Log in the user with Flask-Login
        login_user(user, remember=request.form.get('remember', False))
        
        
        # Check if the user is admin
        if user.is_admin:
            return redirect(url_for('admin_dashboard'))
        
            
        return redirect(url_for('index'))
        
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('register'))
            
        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists!', 'danger')
            return redirect(url_for('register'))
            
        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))
            
        # Create new user
        new_user = User(email=email, username=username, first_name=first_name, last_name=last_name)
        new_user.set_password(password)
        
        # Create cart and wishlist for the user
        cart = Cart(user=new_user)
        wishlist = Wishlist(user=new_user)
        
        db.session.add(new_user)
        db.session.add(cart)
        db.session.add(wishlist)
        db.session.commit()
        
        
        flash('Registration successful! Welcome to Kickx!', 'success')
        return redirect(url_for('index'))
        
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real app, you would generate a token and send an email
            flash('Password reset instructions have been sent to your email.', 'info')
            return redirect(url_for('login'))
        else:
            flash('Email not found!', 'danger')
            
    return render_template('auth/forgot_password.html')

# Cart Routes
@app.route('/cart')
@login_required
def view_cart():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    
    # Add calculated total_price to each cart item
    for item in cart_items:
        item.total_price = item.product.price * item.quantity
        
    total = sum(item.total_price for item in cart_items)
    shipping_cost = 400.0  # Default shipping cost
    
    return render_template('cart/view.html', 
                          cart_items=cart_items, 
                          total=total,
                          shipping_cost=shipping_cost)

@app.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    product_id = request.form.get('product_id')
    size_id = request.form.get('size_id')
    quantity = int(request.form.get('quantity', 1))
    
    # Validate that product and size exist and have stock
    product_size = ProductSize.query.filter_by(product_id=product_id, size_id=size_id).first()
    
    if not product_size or product_size.stock <= 0:
        flash('Sorry, this size is out of stock!', 'danger')
        return redirect(url_for('product_detail', slug=Product.query.get(product_id).slug))
        
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
        
    # Check if product already in cart with the same size
    cart_item = CartItem.query.filter_by(
        cart_id=cart.id,
        product_id=product_id,
        size=product_size.size.value  # Store the size value string for display
    ).first()
    
    if cart_item:
        # Only add more if there's enough stock
        if product_size.stock >= cart_item.quantity + quantity:
            cart_item.quantity += quantity
        else:
            flash(f'Sorry, only {product_size.stock} items available in this size!', 'warning')
            cart_item.quantity = product_size.stock  # Set to max available
    else:
        if product_size.stock >= quantity:
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=quantity,
                size=product_size.size.value  # Store the size value string for display
            )
            db.session.add(cart_item)
        else:
            flash(f'Sorry, only {product_size.stock} items available in this size!', 'warning')
            cart_item = CartItem(
                cart_id=cart.id,
                product_id=product_id,
                quantity=product_size.stock,  # Set to max available
                size=product_size.size.value  # Store the size value string for display
            )
            db.session.add(cart_item)
        
    db.session.commit()
    flash('Product added to cart!', 'success')
    return redirect(url_for('view_cart'))

@app.route('/cart/update', methods=['POST'])
@login_required
def update_cart():
    item_id = request.form.get('item_id')
    quantity = int(request.form.get('quantity'))
    
    cart_item = CartItem.query.get_or_404(item_id)
    if quantity > 0:
        cart_item.quantity = quantity
    else:
        db.session.delete(cart_item)
    db.session.commit()
        
    return redirect(url_for('view_cart'))

@app.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    db.session.delete(cart_item)
    db.session.commit()
        
    flash('Item removed from cart!', 'success')
    return redirect(url_for('view_cart'))

# Checkout Routes
@app.route('/checkout')
@login_required
def checkout():
    # Check if this is a "buy now" checkout
    buy_now_item = session.get('buy_now_item')
    
    if buy_now_item:
        # For buy now, we use just the specific item
        cart_item = CartItem.query.get_or_404(buy_now_item['id'])
        cart_items = [cart_item]
        total = cart_item.product.price * cart_item.quantity
        # Clear the session after retrieving the item
        session.pop('buy_now_item', None)
    else:
        # Normal checkout with all cart items
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart or cart.items.count() == 0:
            flash('Your cart is empty!', 'warning')
            return redirect(url_for('view_cart'))
        
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
    
    # Add shipping cost (this could be calculated based on location)
    shipping_cost = 400.0
    
    # Get addresses
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    return render_template('checkout/index.html', 
                          addresses=addresses, 
                          cart_items=cart_items, 
                          total=total,
                          shipping_cost=shipping_cost)

@app.route('/checkout/address', methods=['GET', 'POST'])
@login_required
def checkout_address():
    if request.method == 'POST':
        # Check if this is selecting an existing address or creating/updating
        address_type = request.form.get('address_type')
        address_id = request.form.get('address_id')
        
        if address_type == 'existing' and address_id:
            # Just selecting an existing address without modification
            # Store the selected address ID in session for the next step
            session['checkout_address_id'] = address_id
            
            # Make sure the address actually exists
            address = Address.query.get(address_id)
            if not address or address.user_id != current_user.id:
                flash('Invalid address selected.', 'danger')
                return redirect(url_for('checkout_address'))
                
            return redirect(url_for('checkout_payment'))
        
        # Create or update address (this is the edit/create flow)
        if address_id:
            # Update existing address
            address = Address.query.get_or_404(address_id)
            # Verify ownership
            if address.user_id != current_user.id:
                flash('You do not have permission to edit this address.', 'danger')
                return redirect(url_for('checkout_address'))
        else:
            # Create new address
            address = Address(user_id=current_user.id)
            
        # Ensure all required fields are present
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        street_address = request.form.get('street_address')
        city = request.form.get('city')
        state = request.form.get('state')
        postal_code = request.form.get('postal_code')
        country = request.form.get('country')
        
        # Validate required fields
        if not (full_name and phone and street_address and city and state and postal_code and country):
            flash('Please fill in all required address fields.', 'danger')
            return redirect(url_for('checkout_address'))
            
        # Update address fields
        address.full_name = full_name
        address.phone = phone
        address.street_address = street_address
        address.city = city
        address.state = state
        address.postal_code = postal_code
        address.country = country
        
        if request.form.get('is_default'):
            # Set all other addresses as non-default
            Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
            address.is_default = True
            
        db.session.add(address)
        db.session.commit()
        
        # Store the address ID for the next step
        session['checkout_address_id'] = str(address.id)  # Convert to string for PayPal custom field
        
        # Debug output for address ID
        print(f"Setting checkout address ID in session: {address.id}")
        
        return redirect(url_for('checkout_payment'))
        
    # For GET requests, try to pre-select a default address
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    # If we have addresses but no address ID in session, try to select a default
    if addresses and 'checkout_address_id' not in session:
        # Look for default address first
        default_address = Address.query.filter_by(user_id=current_user.id, is_default=True).first()
        if default_address:
            session['checkout_address_id'] = str(default_address.id)
        else:
            # Just use the first address
            session['checkout_address_id'] = str(addresses[0].id)
            
    return render_template('checkout/address.html', addresses=addresses)

@app.route('/checkout/payment', methods=['GET', 'POST'])
@login_required
def checkout_payment():
    if request.method == 'POST':
        payment_method = request.form.get('payment_method')
        
        # In a real application, you would process payment here
        # For demonstration, we'll just create the order
        
        # Get cart items
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        
        # Calculate total
        total = sum(item.product.price * item.quantity for item in cart_items)
        shipping_cost = 400.0  # This could be calculated based on location
        
        # Get shipping address
        address_id = request.form.get('address_id')
        address = Address.query.get_or_404(address_id)
        
        # Create order
        order = Order(
            user_id=current_user.id,
            status='pending',
            payment_status='paid',
            payment_method=payment_method,
            total_amount=total + shipping_cost,
            shipping_cost=shipping_cost,
            shipping_address=address.street_address,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_zip=address.postal_code,
            shipping_country=address.country
        )
        
        db.session.add(order)
        db.session.flush()  # This assigns an ID to order
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                size=item.size,
                price=item.product.price
            )
            db.session.add(order_item)
            
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
            
        db.session.commit()
        
        return redirect(url_for('checkout_confirmation', order_id=order.id))
        
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    shipping_cost = 400.0
    
    # Get address from session if it exists
    selected_address_id = session.get('checkout_address_id')
    if selected_address_id:
        selected_address = Address.query.get(selected_address_id)
        if selected_address and selected_address.user_id == current_user.id:
            # Move the selected address to the front of the list
            addresses = [selected_address] + [addr for addr in addresses if addr.id != int(selected_address_id)]
    
    # Generate current timestamp for the template
    current_timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    
    return render_template('checkout/payment.html', 
                          addresses=addresses, 
                          cart_items=cart_items, 
                          total=total,
                          shipping_cost=shipping_cost,
                          paypal_sdk_url=PAYPAL_JS_SDK_URL,
                          now=current_timestamp)

@app.route('/checkout/confirmation/<int:order_id>')
@login_required
def checkout_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order!', 'danger')
        return redirect(url_for('index'))
        
    # Calculate estimated delivery date (7 days from order creation)
    if order.created_at:
        delivery_date = order.created_at + timedelta(days=7)
        estimated_delivery_date = delivery_date.strftime('%B %d, %Y')
    else:
        # Fallback if order date is not set
        estimated_delivery_date = (datetime.utcnow() + timedelta(days=7)).strftime('%B %d, %Y')
    
    # Add status color for proper badge styling
    order.status_color = {
        'pending': 'warning',
        'processing': 'info',
        'shipped': 'primary',
        'delivered': 'success',
        'cancelled': 'danger'
    }.get(order.status, 'secondary')
        
    return render_template('checkout/confirmation.html', 
                          order=order, 
                          estimated_delivery_date=estimated_delivery_date)

# Profile Routes
@app.route('/profile')
@login_required
def profile_dashboard():
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('profile/dashboard.html', 
                          user=current_user, 
                          recent_orders=recent_orders,
                          addresses=addresses)

@app.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    if request.method == 'POST':
        # Update user information
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        
        # Update email if it's changed and not already taken
        new_email = request.form.get('email')
        if new_email and new_email != current_user.email:
            # Check if the email is already in use
            existing_user = User.query.filter_by(email=new_email).first()
            if existing_user and existing_user.id != current_user.id:
                flash('Email already in use by another account.', 'danger')
                return redirect(url_for('profile_settings'))
            current_user.email = new_email
        
        # Check if password is being updated
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if current_password and new_password:
            if not current_user.check_password(current_password):
                flash('Current password is incorrect!', 'danger')
                return redirect(url_for('profile_settings'))
                
            if new_password != confirm_password:
                flash('New passwords do not match!', 'danger')
                return redirect(url_for('profile_settings'))
                
            current_user.set_password(new_password)
            
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile_dashboard'))
        
    return render_template('profile/settings.html', user=current_user)

@app.route('/profile/orders')
@login_required
def profile_orders():
    page = request.args.get('page', 1, type=int)
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('profile/orders.html', orders=orders)

@app.route('/profile/order/<int:order_id>')
@login_required
def profile_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        flash('You do not have permission to view this order!', 'danger')
        return redirect(url_for('profile_orders'))
        
    # Map order status to Bootstrap color classes
    status_colors = {
        'pending': 'warning',
        'processing': 'info',
        'shipped': 'primary',
        'delivered': 'success',
        'cancelled': 'danger'
    }
    
    # Get color for current status or default to secondary
    status_color = status_colors.get(order.status, 'secondary')
        
    return render_template('profile/order_detail.html', 
                          order=order,
                          status_color=status_color)

@app.route('/profile/wishlist')
@login_required
def profile_wishlist():
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=current_user.id)
        db.session.add(wishlist)
        db.session.commit()
        
    wishlist_items = WishlistItem.query.filter_by(wishlist_id=wishlist.id).all()
    
    # Calculate total value based on price and quantity
    total_value = sum((item.product.discount_price or item.product.price) * item.quantity for item in wishlist_items)
    
    # Get recently viewed products (if implemented)
    recently_viewed = []
    if 'recently_viewed' in session:
        product_ids = session['recently_viewed'][:5]  # Get up to 5 recently viewed products
        recently_viewed = Product.query.filter(Product.id.in_(product_ids)).all()
        
        # Reorder products based on the order in the session
        id_to_position = {id: i for i, id in enumerate(product_ids)}
        recently_viewed.sort(key=lambda p: id_to_position.get(p.id, 999))
    
    return render_template('profile/wishlist.html', 
                          wishlist_items=wishlist_items,
                          total_value=total_value,
                          recently_viewed=recently_viewed)

@app.route('/profile/wishlist/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_wishlist(product_id):
    # Get size and quantity from form
    size_id = request.form.get('size_id')
    
    # If no size_id is provided, try to get it from the size radio buttons
    if not size_id:
        size_id = request.form.get('size')
    
    quantity = request.form.get('quantity', 1, type=int)
    
    # Validate size_id
    if not size_id:
        flash('Please select a size before adding to wishlist!', 'warning')
        return redirect(url_for('product_detail', slug=Product.query.get(product_id).slug))
    
    # Get size value
    size_info = Size.query.get(size_id)
    if not size_info:
        flash('Invalid size selected!', 'warning')
        return redirect(url_for('product_detail', slug=Product.query.get(product_id).slug))
    
    # Get or create wishlist
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=current_user.id)
        db.session.add(wishlist)
        db.session.commit()
    
    # Check if product with same size already in wishlist
    wishlist_item = WishlistItem.query.filter_by(
        wishlist_id=wishlist.id,
        product_id=product_id,
        size_id=size_id
    ).first()
    
    if not wishlist_item:
        # Create new wishlist item
        wishlist_item = WishlistItem(
            wishlist_id=wishlist.id,
            product_id=product_id,
            size_id=size_id,
            size=size_info.value,
            quantity=quantity
        )
        db.session.add(wishlist_item)
        db.session.commit()
        flash('Product added to wishlist!', 'success')
    else:
        # Update quantity if already exists
        wishlist_item.quantity = quantity
        db.session.commit()
        flash('Wishlist updated with new quantity!', 'success')
        
    return redirect(url_for('profile_wishlist'))

@app.route('/profile/wishlist/remove/<int:item_id>', methods=['POST'])
@login_required
def remove_from_wishlist(item_id):
    wishlist_item = WishlistItem.query.get_or_404(item_id)
    wishlist = Wishlist.query.get_or_404(wishlist_item.wishlist_id)
    
    if wishlist.user_id != current_user.id:
        flash('You do not have permission to modify this wishlist!', 'danger')
        return redirect(url_for('profile_wishlist'))
    
    # Store product name for confirmation message
    product_name = wishlist_item.product.name
        
    db.session.delete(wishlist_item)
    db.session.commit()
    flash(f'{product_name} removed from wishlist!', 'success')
    return redirect(url_for('profile_wishlist'))

@app.route('/profile/wishlist/move_to_cart/<int:item_id>', methods=['POST'])
@login_required
def move_to_cart(item_id):
    # Get wishlist item
    wishlist_item = WishlistItem.query.get_or_404(item_id)
    wishlist = Wishlist.query.get_or_404(wishlist_item.wishlist_id)
    
    # Check if this user owns the wishlist item
    if wishlist.user_id != current_user.id:
        flash('You do not have permission to modify this wishlist!', 'danger')
        return redirect(url_for('profile_wishlist'))
    
    # Get cart or create one if not exists
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()
    
    # Check if product already in cart with the same size
    existing_cart_item = None
    if wishlist_item.size:
        existing_cart_item = CartItem.query.filter_by(
            cart_id=cart.id,
            product_id=wishlist_item.product_id,
            size=wishlist_item.size
        ).first()
    
    # If exists in cart, update quantity; otherwise create new cart item
    if existing_cart_item:
        existing_cart_item.quantity += wishlist_item.quantity
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=wishlist_item.product_id,
            quantity=wishlist_item.quantity,
            size=wishlist_item.size or 'One Size'  # Default size if none specified
        )
        db.session.add(cart_item)
    
    # Store product name for flash message
    product_name = wishlist_item.product.name
    
    # Remove from wishlist
    db.session.delete(wishlist_item)
    db.session.commit()
    
    flash(f'{product_name} has been moved to your cart!', 'success')
    return redirect(url_for('profile_wishlist'))

@app.route('/profile/addresses')
@login_required
def profile_addresses():
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    return render_template('profile/addresses.html', addresses=addresses)

@app.route('/profile/address/add', methods=['GET', 'POST'])
@login_required
def profile_add_address():
    if request.method == 'POST':
        address = Address(user_id=current_user.id)
        address.full_name = request.form.get('full_name')
        address.phone = request.form.get('phone')
        address.street_address = request.form.get('street_address')
        address.city = request.form.get('city')
        address.state = request.form.get('state')
        address.postal_code = request.form.get('postal_code')
        address.country = request.form.get('country')
        
        if request.form.get('is_default'):
            # Set all other addresses as non-default
            Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
            address.is_default = True
            
        db.session.add(address)
        db.session.commit()
        flash('Address added successfully!', 'success')
        return redirect(url_for('profile_addresses'))
        
    return render_template('profile/address_form.html')

@app.route('/profile/address/edit/<int:address_id>', methods=['GET', 'POST'])
@login_required
def profile_edit_address(address_id):
    address = Address.query.get_or_404(address_id)
    
    if address.user_id != current_user.id:
        flash('You do not have permission to edit this address!', 'danger')
        return redirect(url_for('profile_addresses'))
        
    if request.method == 'POST':
        address.full_name = request.form.get('full_name')
        address.phone = request.form.get('phone')
        address.street_address = request.form.get('street_address')
        address.city = request.form.get('city')
        address.state = request.form.get('state')
        address.postal_code = request.form.get('postal_code')
        address.country = request.form.get('country')
        
        if request.form.get('is_default'):
            # Set all other addresses as non-default
            Address.query.filter_by(user_id=current_user.id, is_default=True).update({'is_default': False})
            address.is_default = True
            
        db.session.commit()
        flash('Address updated successfully!', 'success')
        return redirect(url_for('profile_addresses'))
        
    return render_template('profile/address_form.html', address=address)

@app.route('/profile/address/delete/<int:address_id>')
@login_required
def profile_delete_address(address_id):
    address = Address.query.get_or_404(address_id)
    
    if address.user_id != current_user.id:
        flash('You do not have permission to delete this address!', 'danger')
        return redirect(url_for('profile_addresses'))
        
    db.session.delete(address)
    db.session.commit()
    flash('Address deleted successfully!', 'success')
    return redirect(url_for('profile_addresses'))

@app.route('/profile/notifications', methods=['GET', 'POST'])
@login_required
def profile_notifications():
    if request.method == 'POST':
        flash('Notification preferences are not available in this version.', 'info')
        return redirect(url_for('profile_settings'))
        
    # In a real app, you would fetch notifications from the database
    return render_template('profile/notifications.html')

# Admin Routes
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin dashboard.', 'danger')
        return redirect(url_for('index'))
    
    # Get some summary statistics
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    revenue = db.session.query(func.sum(OrderItem.price * OrderItem.quantity)).scalar() or 0
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Get low stock products
    low_stock_products = Product.query.filter(Product.stock < 10).limit(5).all()
    
    # Get verified products
    verified_products = Product.query.filter_by(is_verified=True).limit(5).all()
    
    # Get recent user signups
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html', 
                          total_users=total_users, 
                          total_products=total_products, 
                          total_orders=total_orders, 
                          revenue=revenue,
                          recent_orders=recent_orders,
                          low_stock_products=low_stock_products,
                          verified_products=verified_products,
                          recent_users=recent_users)

@app.route('/admin/products')
@login_required
def admin_products():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=20)
    brands = Brand.query.all()
    categories = Category.query.all()
    
    return render_template('admin/products.html', 
                          products=products,
                          brands=brands,
                          categories=categories)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@login_required
def admin_add_product():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        slug = request.form.get('slug')
        description = request.form.get('description')
        price = float(request.form.get('price'))
        category_id = request.form.get('category_id')
        brand_id = request.form.get('brand_id')
        stock = int(request.form.get('stock', 0))
        color = request.form.get('color')
        style_code = request.form.get('style_code')
        release_date = datetime.strptime(request.form.get('release_date'), '%Y-%m-%d') if request.form.get('release_date') else None
        is_verified = 'is_verified' in request.form
        
        image_url = None
        # Handle image file upload
        if 'image_file' in request.files and request.files['image_file'].filename:
            image_file = request.files['image_file']
            
            # Check if the file has an allowed extension
            if image_file and allowed_file(image_file.filename):
                # Generate secure filename
                filename = secure_filename(f"{slug}_{int(time.time())}{os.path.splitext(image_file.filename)[1]}")
                
                # Ensure upload directory exists
                upload_dir = os.path.join(app.static_folder, 'uploads/products')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # Save the file
                file_path = os.path.join(upload_dir, filename)
                image_file.save(file_path)
                
                # Update image URL to point to the uploaded file
                image_url = url_for('static', filename=f'uploads/products/{filename}')
        
        product = Product(
            name=name,
            slug=slug,
            description=description,
            price=price,
            category_id=category_id,
            brand_id=brand_id,
            stock=stock,
            image_url=image_url,
            color=color,
            style_code=style_code,
            release_date=release_date,
            is_verified=is_verified
        )
        
        db.session.add(product)
        db.session.commit()
        
        # Add sizes for the product
        sizes = request.form.getlist('sizes')
        for size_id in sizes:
            size_stock = request.form.get(f'size_stock_{size_id}', 0)
            if int(size_stock) > 0:
                product_size = ProductSize(
                    product_id=product.id,
                    size_id=size_id,
                    stock=size_stock
                )
                db.session.add(product_size)
                
        db.session.commit()
        flash('Product added successfully!', 'success')
        
        # Create notification for verified products
        if is_verified:
            notification_message = f"Verified Authentic: {name} is now authenticated!"
            notification_link = url_for('product_detail', slug=slug)
            create_bulk_notifications(
                notification_type="verified",
                message=notification_message,
                link=notification_link,
                related_product_id=product.id
            )
            
        return redirect(url_for('admin_products'))
        
    categories = Category.query.all()
    brands = Brand.query.all()
    sizes = Size.query.all()
    
    return render_template('admin/product_form.html', 
                          categories=categories,
                          brands=brands,
                          sizes=sizes)

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_product(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        was_verified = product.is_verified
        
        product.name = request.form.get('name')
        product.slug = request.form.get('slug')
        product.description = request.form.get('description')
        product.price = float(request.form.get('price'))
        product.category_id = request.form.get('category_id')
        product.brand_id = request.form.get('brand_id')
        product.stock = int(request.form.get('stock', 0))
        product.color = request.form.get('color')
        product.style_code = request.form.get('style_code')
        product.is_verified = 'is_verified' in request.form
        if request.form.get('release_date'):
            product.release_date = datetime.strptime(request.form.get('release_date'), '%Y-%m-%d')
        product.featured = True if request.form.get('featured') else False
        
        # Handle image file upload
        if 'image_file' in request.files and request.files['image_file'].filename:
            image_file = request.files['image_file']
            
            # Check if the file has an allowed extension
            if image_file and allowed_file(image_file.filename):
                # Generate secure filename
                filename = secure_filename(f"{product.slug}_{int(time.time())}{os.path.splitext(image_file.filename)[1]}")
                
                # Ensure upload directory exists
                upload_dir = os.path.join(app.static_folder, 'uploads/products')
                if not os.path.exists(upload_dir):
                    os.makedirs(upload_dir)
                
                # Save the file
                file_path = os.path.join(upload_dir, filename)
                image_file.save(file_path)
                
                # Update image URL to point to the uploaded file
                product.image_url = url_for('static', filename=f'uploads/products/{filename}')
        elif request.form.get('image_url'):
            # If no new file but URL provided, update the URL
            product.image_url = request.form.get('image_url')
        
        # Update sizes
        existing_sizes = ProductSize.query.filter_by(product_id=product.id).all()
        for ps in existing_sizes:
            db.session.delete(ps)
            
        sizes = request.form.getlist('sizes')
        for size_id in sizes:
            size_stock = request.form.get(f'size_stock_{size_id}', 0)
            if int(size_stock) > 0:
                product_size = ProductSize(
                    product_id=product.id,
                    size_id=size_id,
                    stock=size_stock
                )
                db.session.add(product_size)
                
        db.session.commit()
        
        # Create notification if verification status changed
        if not was_verified and product.is_verified:
            notification_message = f"Verified Authentic: {product.name} is now authenticated!"
            notification_link = url_for('product_detail', slug=product.slug)
            create_bulk_notifications(
                notification_type="verified",
                message=notification_message,
                link=notification_link,
                related_product_id=product.id
            )
        
        flash('Product updated successfully!', 'success')
        return redirect(url_for('admin_products'))
        
    categories = Category.query.all()
    brands = Brand.query.all()
    sizes = Size.query.all()
    product_sizes = ProductSize.query.filter_by(product_id=product_id).all()
    print([i.stock for i in product_sizes])
    return render_template('admin/product_form.html', 
                          product=product,
                          categories=categories,
                          brands=brands,
                          sizes=sizes,
                          product_sizes=product_sizes)

@app.route('/admin/product/delete/<int:product_id>', methods=['GET', 'POST'])
@login_required
def admin_delete_product(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@login_required
def admin_orders():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status')
    
    if status:
        orders = Order.query.filter_by(status=status).paginate(page=page, per_page=20)
    else:
        orders = Order.query.paginate(page=page, per_page=20)
        
    return render_template('admin/orders.html', orders=orders, current_status=status)

@app.route('/admin/order/<int:order_id>')
@login_required
def admin_order_detail(order_id):
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/order/update/<int:order_id>', methods=['GET', 'POST'])
@login_required
def admin_update_order(order_id):
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    order = Order.query.get_or_404(order_id)
    
    if request.method == 'POST':
        order.status = request.form.get('status')
        order.payment_status = request.form.get('payment_status')
        order.tracking_number = request.form.get('tracking_number')
        
        # Update dates based on status
        if order.status == 'processing' and not order.processing_date:
            order.processing_date = datetime.utcnow()
        elif order.status == 'shipped' and not order.shipping_date:
            order.shipping_date = datetime.utcnow()
        elif order.status == 'delivered' and not order.delivery_date:
            order.delivery_date = datetime.utcnow()
            
        db.session.commit()
        flash('Order updated successfully!', 'success')
        return redirect(url_for('admin_order_detail', order_id=order.id))
        
    return render_template('admin/update_order_status.html', order=order)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role = request.args.get('role', '')
    status = request.args.get('status', '')
    
    # Base query
    query = User.query
    
    # Apply filters
    if search:
        query = query.filter(
            (User.username.contains(search)) | 
            (User.email.contains(search)) |
            (User.first_name.contains(search)) | 
            (User.last_name.contains(search))
        )
    
    if role == 'admin':
        query = query.filter_by(is_admin=True)
    elif role == 'user':
        query = query.filter_by(is_admin=False)
    
    if status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)
    
    # Get paginated results
    users = query.paginate(page=page, per_page=20)
    
    # Separate counts for admins and customers for the badges
    admins = [user for user in users.items if user.is_admin]
    customers = [user for user in users.items if not user.is_admin]
    
    return render_template('admin/users.html', 
                          users=users,
                          admins=admins,
                          customers=customers)

@app.route('/admin/user/<int:user_id>')
@login_required
def admin_view_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.created_at.desc()).all()
    addresses = Address.query.filter_by(user_id=user.id).all()
    
    return render_template('admin/view_user.html', user=user, orders=orders, addresses=addresses)

@app.route('/admin/user/add', methods=['GET', 'POST'])
@login_required
def admin_add_user():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('new_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Get user type for role assignment
        user_type = request.form.get('user_type', 'customer')
        
        # Only set admin if explicitly selected in user type
        is_admin = user_type == 'admin'
        
        # Customer type can never be admin
        if user_type == 'customer':
            is_admin = False
        
        is_active = True if request.form.get('is_active') else False
        
        # Check if email already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email address already exists!', 'danger')
            return redirect(url_for('admin_add_user'))
            
        # Check if username already exists
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('admin_add_user'))
            
        # Create new user
        new_user = User(
            email=email, 
            username=username,
            first_name=first_name,
            last_name=last_name,
            is_admin=is_admin,
            is_active=is_active
        )
        new_user.set_password(password)
        
        # Create cart and wishlist for the user
        cart = Cart(user=new_user)
        wishlist = Wishlist(user=new_user)
        
        db.session.add(new_user)
        db.session.add(cart)
        db.session.add(wishlist)
        db.session.commit()
        
        user_type_label = "Administrator" if is_admin else "Customer"
        flash(f'{user_type_label} {username} has been added successfully!', 'success')
        return redirect(url_for('admin_users'))
        
    return render_template('admin/user_form.html')

@app.route('/admin/user/edit/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Check if delete operation is requested
        if request.form.get('delete'):
            # Can't delete your own account
            if user.id == current_user.id:
                flash('You cannot delete your own admin account!', 'danger')
                return redirect(url_for('admin_users'))
                
            # Delete all associated data
            try:
                # Delete cart items
                cart = Cart.query.filter_by(user_id=user.id).first()
                if cart:
                    CartItem.query.filter_by(cart_id=cart.id).delete()
                    db.session.delete(cart)
                
                # Delete wishlist items
                wishlist = Wishlist.query.filter_by(user_id=user.id).first()
                if wishlist:
                    WishlistItem.query.filter_by(wishlist_id=wishlist.id).delete()
                    db.session.delete(wishlist)
                
                # Delete addresses
                Address.query.filter_by(user_id=user.id).delete()
                
                # Delete reviews
                Review.query.filter_by(user_id=user.id).delete()
                
                # Delete user
                user_type = "Administrator" if user.is_admin else "Customer"
                user_name = f"{user.first_name} {user.last_name}"
                db.session.delete(user)
                db.session.commit()
                flash(f'{user_type} {user_name} has been deleted successfully!', 'success')
                return redirect(url_for('admin_users'))
            except Exception as e:
                db.session.rollback()
                flash(f'Error deleting user: {str(e)}', 'danger')
                return redirect(url_for('admin_users'))
        
        # Check if status toggle is requested
        if request.form.get('is_active') is not None and len(request.form) == 1:
            is_active_val = request.form.get('is_active')
            user.is_active = True if is_active_val == '1' else False
            
            # If deactivating the only admin account, prevent it
            if not user.is_active and user.is_admin:
                admin_count = User.query.filter_by(is_admin=True, is_active=True).count()
                if admin_count <= 1 and user.id == current_user.id:
                    flash('Cannot deactivate the only admin account!', 'danger')
                    return redirect(url_for('admin_view_user', user_id=user.id))
            
            db.session.commit()
            status_text = 'activated' if user.is_active else 'deactivated'
            user_type = "Administrator" if user.is_admin else "Customer"
            flash(f'{user_type} account has been {status_text} successfully!', 'success')
            return redirect(url_for('admin_view_user', user_id=user.id))
            
        # Normal update operation
        username = request.form.get('username')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Only admins can have admin status changed, customers always remain customers
        if user.is_admin:
            is_admin = True if request.form.get('is_admin') else False
            
            # Validate admin changes
            if user.is_admin != is_admin:
                # If removing admin role from self, check if this is the only admin
                if user.id == current_user.id and user.is_admin and not is_admin:
                    admin_count = User.query.filter_by(is_admin=True).count()
                    if admin_count <= 1:
                        flash('Cannot remove admin privileges from the only admin account!', 'danger')
                        return redirect(url_for('admin_edit_user', user_id=user.id))
            
            # Track role change for message
            role_changed = user.is_admin != is_admin
            old_role = "Administrator" if user.is_admin else "Customer"
        else:
            # For customers, always keep is_admin as False
            is_admin = False
            role_changed = False
        
        is_active = True if request.form.get('is_active') else False
        
        # Check if username already exists
        if username != user.username:
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                flash('Username already exists!', 'danger')
                return redirect(url_for('admin_edit_user', user_id=user.id))
        
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.is_admin = is_admin
        user.is_active = is_active
        
        # Check if password is being updated
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
            
        db.session.commit()
        
        new_role = "Administrator" if is_admin else "Customer"
        if role_changed:
            flash(f'User role changed from {old_role} to {new_role} successfully!', 'success')
        else:
            flash(f'{new_role} updated successfully!', 'success')
            
        return redirect(url_for('admin_view_user', user_id=user.id))
        
    return render_template('admin/user_form.html', user=user)

@app.route('/admin/recommendation-engine', methods=['GET', 'POST'])
@login_required
def admin_recommendation_engine():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    # Initialize recommendation engine if not already initialized
    recommendation_engine = get_recommendation_engine()
    if recommendation_engine is None:
        recommendation_engine = init_recommendation_engine(db)
    
    # Handle form submission
    if request.method == 'POST':
        # Check if this is a rebuild action
        if request.form.get('action') == 'rebuild':
            try:
                # Rebuild the recommendation model
                success = recommendation_engine.build_model()
                if success:
                    flash('Recommendation model rebuilt successfully!', 'success')
                else:
                    flash('Failed to rebuild recommendation model. Please check the logs.', 'danger')
            except Exception as e:
                flash(f'Error rebuilding model: {str(e)}', 'danger')
            return redirect(url_for('admin_recommendation_engine'))
        
        # Otherwise, it's a settings update
        try:
            # Get form data
            settings = {
                'content_based_weight': float(request.form.get('content_based_weight', 0.5)),
                'collaborative_weight': float(request.form.get('collaborative_weight', 0.5)),
                'min_recommendation_confidence': float(request.form.get('min_recommendation_confidence', 0.3)),
                'max_recommendations_per_product': int(request.form.get('max_recommendations_per_product', 6)),
                'enable_personalized_home': 'enable_personalized_home' in request.form,
                'recommendation_refresh_hours': int(request.form.get('recommendation_refresh_hours', 24)),
                'trending_timespan_days': int(request.form.get('trending_timespan_days', 7))
            }
            
            # Save settings to the recommendation engine
            recommendation_engine.save_settings(settings)
            flash('Recommendation engine settings have been updated successfully.', 'success')
            
        except ValueError as e:
            flash(f'Invalid input: {str(e)}', 'danger')
        
        return redirect(url_for('admin_recommendation_engine'))
    
    # Get current settings from recommendation engine
    settings = recommendation_engine.load_settings()
    
    # Get frequently recommended products for display
    recent_recommendations = recommendation_engine.get_frequent_recommendations(10)
    
    return render_template('admin/recommendation_settings.html', 
                          settings=settings,
                          recent_recommendations=recent_recommendations)

@app.route('/admin/notification-settings', methods=['GET'])
@login_required
def admin_notification_settings():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
    
    # Get notification settings
    settings = NotificationSettings.query.first()
    
    # Create default settings if none exist
    if not settings:
        settings = NotificationSettings()
        db.session.add(settings)
        db.session.commit()
    
    return render_template('admin/notification_settings.html', settings=settings)

@app.route('/admin/update-notification-settings', methods=['POST'])
@login_required
def update_notification_settings():
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
    
    try:
        # Get current settings or create if not exists
        settings = NotificationSettings.query.first()
        
        # Create new settings if they don't exist
        if not settings:
            settings = NotificationSettings()
            db.session.add(settings)
        
        # Update settings based on form data
        settings.new_arrival_notifications = 'new_arrival_notifications' in request.form
        settings.restock_notifications = 'restock_notifications' in request.form
        settings.price_drop_notifications = 'price_drop_notifications' in request.form
        settings.exclusive_drop_notifications = 'exclusive_drop_notifications' in request.form
        
        try:
            settings.notification_cooldown_hours = int(request.form.get('notification_cooldown_hours', 24))
            if settings.notification_cooldown_hours < 1 or settings.notification_cooldown_hours > 168:
                settings.notification_cooldown_hours = 24
                flash('Notification cooldown hours must be between 1 and 168. Reset to default (24).', 'warning')
        except ValueError:
            settings.notification_cooldown_hours = 24
            flash('Invalid notification cooldown value. Reset to default (24).', 'warning')
        
        db.session.commit()
        flash('Notification settings updated successfully!', 'success')
    except Exception as e:
        # Handle database errors
        print(f"Database error: {str(e)}")
        
        # Create tables if they don't exist
        try:
            db.create_all()
            flash('Database tables created. Please try again.', 'warning')
        except Exception as inner_e:
            print(f"Failed to create table: {str(inner_e)}")
            flash('Error updating notification settings. Database tables may not be properly set up.', 'danger')
        
        db.session.rollback()
    
    return redirect(url_for('admin_notification_settings'))

# Product review routes
@app.route('/product/<slug>/review', methods=['POST'])
@login_required
def add_review(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')
    
    # Check if user has already reviewed this product
    existing_review = Review.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    
    if existing_review:
        # Update existing review
        existing_review.rating = rating
        existing_review.comment = comment
        existing_review.updated_at = datetime.utcnow()
        flash('Review updated successfully!', 'success')
    else:
        # Create new review
        review = Review(
            user_id=current_user.id,
            product_id=product.id,
            rating=rating,
            comment=comment
        )
        db.session.add(review)
        flash('Review added successfully!', 'success')
        
    db.session.commit()
    return redirect(url_for('product_detail', slug=slug))

@app.route('/review/delete/<int:review_id>')
@login_required
def delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    # Check if user is the owner of the review or an admin
    if review.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this review!', 'danger')
        return redirect(url_for('product_detail', slug=review.product.slug))
        
    product_slug = review.product.slug
    db.session.delete(review)
    db.session.commit()
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('product_detail', slug=product_slug))

# Other Main Routes
@app.route('/contact')
def contact():
    return render_template('main/contact.html')

@app.route('/faq')
def faq():
    return render_template('main/faq.html')

@app.route('/shipping')
def shipping():
    return render_template('main/shipping.html')

@app.route('/clear-cookies')
def clear_cookies():
    response = redirect(url_for('index'))
    # Clear all cookies
    for cookie in request.cookies:
        response.delete_cookie(cookie)
    flash('All cookies have been cleared!', 'success')
    return response

@app.route('/api/wishlist/<int:product_id>', methods=['POST'])
@login_required
def toggle_wishlist_item(product_id):
    wishlist = Wishlist.query.filter_by(user_id=current_user.id).first()
    if not wishlist:
        wishlist = Wishlist(user_id=current_user.id)
        db.session.add(wishlist)
        db.session.commit()
        
    # Check if product already in wishlist
    wishlist_item = WishlistItem.query.filter_by(
        wishlist_id=wishlist.id,
        product_id=product_id
    ).first()
    
    if wishlist_item:
        # Remove from wishlist if it exists
        db.session.delete(wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'in_wishlist': False})
    else:
        # Add to wishlist if it doesn't exist
        wishlist_item = WishlistItem(
            wishlist_id=wishlist.id,
            product_id=product_id
        )
        db.session.add(wishlist_item)
        db.session.commit()
        return jsonify({'success': True, 'in_wishlist': True})

# Setup a template filter for displaying time ago
@app.template_filter('time_ago')
def time_ago(dt):
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 7:
        return dt.strftime('%b %d, %Y')
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days > 1 else ''} ago"
    elif diff.seconds >= 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif diff.seconds >= 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    else:
        return "Just now"

# Notification Routes and Functions
def create_notification(user_id, notification_type, message, link=None, related_product_id=None):
    """Create a notification for a specific user"""
    notification = Notification(
        user_id=user_id,
        type=notification_type,
        message=message,
        link=link,
        related_product_id=related_product_id
    )
    db.session.add(notification)
    db.session.commit()
    return notification

def create_bulk_notifications(notification_type, message, link=None, related_product_id=None):
    """Create notifications for all users who have opted in to this notification type"""
    users = User.query.filter_by(is_active=True).all()
    
    for user in users:
        # Check if the user has opted in to this type of notification
        # For now, just create notifications for all active users
        notification = Notification(
            user_id=user.id,
            type=notification_type,
            message=message,
            link=link,
            related_product_id=related_product_id
        )
        db.session.add(notification)
    
    db.session.commit()

@app.route('/notifications/mark-read/<int:notification_id>')
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Check if notification belongs to user
    if notification.user_id != current_user.id:
        flash('You do not have permission to access this notification.', 'danger')
        return redirect(url_for('index'))
    
    notification.is_read = True
    db.session.commit()
    
    # Redirect to the notification link if it exists
    if notification.link:
        return redirect(notification.link)
    else:
        return redirect(url_for('view_all_notifications'))

@app.route('/notifications/mark-all-read')
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    flash('All notifications marked as read.', 'success')
    return redirect(url_for('view_all_notifications'))

@app.route('/notifications')
@login_required
def view_all_notifications():
    try:
        page = request.args.get('page', 1, type=int)
        notifications = Notification.query.filter_by(user_id=current_user.id) \
            .order_by(Notification.created_at.desc()) \
            .paginate(page=page, per_page=20)
        
        return render_template('profile/notifications.html', notifications=notifications)
    except Exception as e:
        # Handle case where table might not exist yet
        print(f"Error viewing notifications: {str(e)}")
        return render_template('profile/notifications.html', notifications=None)

# Admin notification creation route
@app.route('/admin/create-notification', methods=['GET', 'POST'])
@login_required
def admin_create_notification():
    if not current_user.is_admin:
        flash('You do not have permission to access this area.', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        notification_type = request.form.get('type')
        message = request.form.get('message')
        link = request.form.get('link')
        related_product_id = request.form.get('related_product_id')
        
        # Create notification for all users
        create_bulk_notifications(
            notification_type=notification_type,
            message=message,
            link=link,
            related_product_id=related_product_id if related_product_id else None
        )
        
        flash('Notification sent to all users successfully.', 'success')
        return redirect(url_for('admin_dashboard'))
    
    # Get product data for selection
    products = Product.query.all()
    return render_template('admin/create_notification.html', products=products)



# Add before_request handler to make notifications available in templates
@app.before_request
def load_notifications():
    if current_user.is_authenticated:
        # Fetch 5 most recent notifications
        notifications = Notification.query.filter_by(user_id=current_user.id) \
            .order_by(Notification.created_at.desc()) \
            .limit(5) \
            .all()
        g.notifications = notifications
    else:
        g.notifications = []

@app.context_processor
def utility_processor():
    def get_notifications():
        if hasattr(g, 'notifications'):
            return g.notifications
        return []
    
    return {'notifications': get_notifications()} 

@app.route('/admin/products/update-price/<int:product_id>', methods=['POST'])
@login_required
def admin_update_product_price(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'danger')
        return redirect(url_for('index'))
    
    product = Product.query.get_or_404(product_id)
    
    # Get new price information
    new_price = float(request.form.get('price', product.price))
    new_sale_price = float(request.form.get('sale_price', 0)) if request.form.get('sale_price') else None
    
    # Check if this is a price drop (sale)
    is_new_sale = False
    if new_sale_price and (product.sale_price is None or new_sale_price < product.sale_price):
        is_new_sale = True
    
    # Update product
    product.price = new_price
    product.sale_price = new_sale_price
    product.is_sale = True if new_sale_price and new_sale_price < new_price else False
    
    db.session.commit()
    
    # Create sale notification if this is a new sale or price drop
    if is_new_sale:
        discount_percentage = round((1 - (new_sale_price / new_price)) * 100)
        notification_message = f"SALE: {product.brand} {product.model} now {discount_percentage}% OFF!"
        notification_link = url_for('product_detail', product_id=product.id)
        
        create_bulk_notifications(
            notification_type="sale",
            message=notification_message,
            link=notification_link,
            related_product_id=product.id
        )
    
    flash('Product price updated successfully!', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/product/authenticate/<int:product_id>', methods=['POST'])
@login_required
def admin_authenticate_product(product_id):
    if not current_user.is_admin:
        flash('You do not have permission to access the admin area!', 'danger')
        return redirect(url_for('index'))
        
    product = Product.query.get_or_404(product_id)
    
    # Get the previous authentication status
    was_verified = product.is_verified
    
    # Update authentication status
    product.is_verified = 'is_verified' in request.form
    
    # If we wanted to store additional authentication data, we could create an Authentication model
    # For now, we'll just log the authenticator and notes in the console
    authenticator = request.form.get('authenticator', 'internal')
    auth_notes = request.form.get('auth_notes', '')
    print(f"Product {product.name} authenticated by {authenticator}. Notes: {auth_notes}")
    
    db.session.commit()
    
    # Create notification if verification status changed to verified
    if not was_verified and product.is_verified:
        notification_message = f"Verified Authentic: {product.name} is now authenticated!"
        notification_link = url_for('product_detail', slug=product.slug)
        create_bulk_notifications(
            notification_type="verified",
            message=notification_message,
            link=notification_link,
            related_product_id=product.id
        )
        flash(f'{product.name} has been verified as authentic!', 'success')
    elif was_verified and not product.is_verified:
        flash(f'{product.name} is no longer marked as verified.', 'warning')
    else:
        flash(f'Authentication status updated for {product.name}.', 'success')
    
    return redirect(url_for('admin_products'))

@app.route('/buy-now/<int:item_id>', methods=['POST'])
@login_required
def buy_now(item_id):
    # Get the cart item
    cart_item = CartItem.query.get_or_404(item_id)
    cart = Cart.query.get_or_404(cart_item.cart_id)
    
    # Check if this user owns the cart item
    if cart.user_id != current_user.id:
        flash('You do not have permission to access this item!', 'danger')
        return redirect(url_for('view_cart'))
    
    # Create a temporary session variable to store this item as the only checkout item
    session['buy_now_item'] = {
        'id': cart_item.id,
        'product_id': cart_item.product_id,
        'quantity': cart_item.quantity,
        'size': cart_item.size
    }
    
    # Redirect to checkout
    return redirect(url_for('checkout'))

# PayPal Integration Routes
@app.route('/api/paypal/create-order', methods=['POST'])
@login_required
def create_paypal_order():
    try:
        # Get cart items
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart:
            return jsonify({'error': 'Cart not found'}), 400
            
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            return jsonify({'error': 'Cart is empty'}), 400
            
        # Calculate totals
        total = sum(item.product.price * item.quantity for item in cart_items)
        shipping_cost = 400.0  # Same as in checkout
        total_amount = total + shipping_cost
        
        # Create PayPal order
        order_response = paypal_service.create_order(total_amount, shipping_cost, cart_items)
        
        if not order_response:
            return jsonify({'error': 'Failed to create PayPal order'}), 500
            
        # Store PayPal order ID in session for verification later
        session['paypal_order_id'] = order_response['id']
        
        # Return the order details
        return jsonify({
            'id': order_response['id'],
            'status': order_response['status']
        })
            
    except Exception as e:
        print(f"Error creating PayPal order: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/checkout/paypal/complete', methods=['POST', 'GET'])
@login_required
def complete_paypal_order():
    try:
        # Handle PayPal standard form redirect (GET) or our API-based flow (POST)
        if request.method == 'GET':
            # This is a PayPal standard redirect
            # PayPal transaction ID from the return URL
            txn_id = request.args.get('tx')
            payment_status = request.args.get('st')  # PayPal payment status
            address_id = session.get('checkout_address_id')
            
            # Log all parameters from PayPal for debugging
            print("PayPal Return Parameters:", request.args)
            
            # If we have a transaction ID, assume payment was successful
            # PayPal sometimes doesn't include status in the return URL
            if txn_id:
                # For PayPal standard integration, we'll assume success if we have a transaction ID
                print(f"PayPal transaction ID received: {txn_id}")
            elif payment_status and payment_status != 'Completed' and payment_status != 'Pending':
                flash(f'Payment not completed. Status: {payment_status}', 'warning')
                return redirect(url_for('checkout_payment'))
                
            # If we don't have an address ID in session, try to get a default address
            if not address_id:
                default_address = Address.query.filter_by(user_id=current_user.id, is_default=True).first()
                if default_address:
                    address_id = default_address.id
                else:
                    # Get any address
                    any_address = Address.query.filter_by(user_id=current_user.id).first()
                    if any_address:
                        address_id = any_address.id
                    else:
                        flash('No shipping address found. Please add an address.', 'danger')
                        return redirect(url_for('profile_add_address'))
                        
            # Set PayPal order ID to the transaction ID
            paypal_order_id = txn_id
        else:
            # This is our API-based flow
            paypal_order_id = request.form.get('paypal_order_id')
            address_id = request.form.get('address_id')
            
            if not paypal_order_id:
                flash('PayPal order ID is missing', 'danger')
                return redirect(url_for('checkout_payment'))
                
            if not address_id:
                flash('Shipping address is required', 'danger')
                return redirect(url_for('checkout_payment'))
                
            # Verify this is the same order ID we created in the API flow
            if session.get('paypal_order_id') and session.get('paypal_order_id') != paypal_order_id:
                flash('Invalid order ID', 'danger')
                return redirect(url_for('checkout_payment'))
                
            # For API flow, capture the payment
            capture_response = paypal_service.capture_order(paypal_order_id)
            
            if not capture_response:
                flash('Failed to capture PayPal payment', 'danger')
                return redirect(url_for('checkout_payment'))
                
            if capture_response['status'] != 'COMPLETED':
                flash(f'Payment not completed. Status: {capture_response["status"]}', 'warning')
                return redirect(url_for('checkout_payment'))
            
        # Make sure we have a valid payment ID
        if not paypal_order_id and request.method == 'GET':
            # If we don't have a txn_id but we're in a GET request,
            # we might be in the success redirect from PayPal but without parameters
            # Try to use the most recent order as a fallback
            latest_order = Order.query.filter_by(
                user_id=current_user.id
            ).order_by(Order.created_at.desc()).first()
            
            if latest_order and (datetime.utcnow() - latest_order.created_at).total_seconds() < 300:
                # If order was created in the last 5 minutes, assume it's the current one
                flash('Your payment was successful!', 'success')
                return redirect(url_for('checkout_confirmation', order_id=latest_order.id))
            else:
                # Create a dummy transaction ID based on timestamp if none provided
                paypal_order_id = f"MANUAL_{int(time.time())}"
                print(f"Generated manual transaction ID: {paypal_order_id}")
        
        # Check if an order with this payment ID already exists
        if paypal_order_id:
            existing_order = Order.query.filter_by(payment_id=paypal_order_id).first()
            if existing_order:
                # Order already exists, don't create a duplicate
                flash('Your order has already been processed!', 'success')
                return redirect(url_for('checkout_confirmation', order_id=existing_order.id))
            
        # Get address
        address = Address.query.get_or_404(address_id)
        
        # Get cart items
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        if not cart:
            flash('Your cart is empty or not found.', 'warning')
            return redirect(url_for('view_cart'))
            
        cart_items = CartItem.query.filter_by(cart_id=cart.id).all()
        if not cart_items:
            flash('Your cart is empty. Please add items before checkout.', 'warning')
            return redirect(url_for('view_cart'))
        
        # Calculate total
        total = sum(item.product.price * item.quantity for item in cart_items)
        shipping_cost = 400.0
        
        # Create order in our database
        order = Order(
            user_id=current_user.id,
            status='processing',  # Already paid with PayPal
            payment_status='paid',
            payment_method='paypal',
            payment_id=paypal_order_id,
            total_amount=total + shipping_cost,
            shipping_cost=shipping_cost,
            shipping_address=address.street_address,
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_zip=address.postal_code,
            shipping_country=address.country,
            processing_date=datetime.utcnow()  # Mark as processing immediately
        )
        
        db.session.add(order)
        db.session.flush()  # This assigns an ID to order
        
        # Create order items
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                size=item.size,
                price=item.product.price
            )
            db.session.add(order_item)
            
        # Clear cart
        for item in cart_items:
            db.session.delete(item)
            
        # Clear session variables
        session.pop('paypal_order_id', None)
        session.pop('checkout_address_id', None)
        session.pop('buy_now_item', None)  # Clear any buy now items too
            
        db.session.commit()
        
        # Create notification for successful order
        create_notification(
            user_id=current_user.id,
            notification_type="order_confirmation",
            message=f"Your order #{order.id} has been confirmed and is being processed!",
            link=url_for('profile_order_detail', order_id=order.id)
        )
        
        flash('Payment completed successfully!', 'success')
        return redirect(url_for('checkout_confirmation', order_id=order.id))
        
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full stack trace to console for debugging
        print(f"Error completing PayPal order: {str(e)}")
        flash(f"Error completing order: {str(e)}", 'danger')
        return redirect(url_for('checkout_payment'))

@app.route('/checkout/success')
@login_required
def checkout_success():
    # Get order ID from PayPal custom parameter or from our session
    order_id = request.args.get('order_id')
    custom_value = request.args.get('cm')  # PayPal passes the custom field as 'cm'
    
    # Log all parameters for debugging
    print("Checkout Success Parameters:", request.args)
    
    # If we have an order_id directly, use it
    if order_id:
        return redirect(url_for('checkout_confirmation', order_id=order_id))
    # If we have a custom value with an address ID, look up the most recent order
    elif custom_value:
        # Find the most recent order for the current user
        latest_order = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).first()
        if latest_order:
            return redirect(url_for('checkout_confirmation', order_id=latest_order.id))
        
    # If no order found, check if we have a payment ID in the URL (PayPal sometimes returns this)
    paypal_txn_id = request.args.get('tx')
    if paypal_txn_id:
        # Try to find an order with this payment ID
        order = Order.query.filter_by(payment_id=paypal_txn_id).first()
        if order:
            return redirect(url_for('checkout_confirmation', order_id=order.id))
    
    # As a last resort, just find the most recent order for this user
    latest_order = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).first()
    if latest_order and (datetime.utcnow() - latest_order.created_at).total_seconds() < 300:
        # If we have a recent order (created in the last 5 minutes), use that
        return redirect(url_for('checkout_confirmation', order_id=latest_order.id))
    
    # If all else fails, redirect to orders with a message
    flash('Order ID not found. Please check your orders for confirmation.', 'warning')
    return redirect(url_for('profile_orders'))

# Run the app
if __name__ == '__main__':
    app.run(debug=True, port=5001) 
