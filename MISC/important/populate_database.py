from kickx_app import app, db, User, Brand, Category, Size, Product, ProductSize
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
import os
import requests
import random
from datetime import datetime, timedelta
import time
import string
from pathlib import Path

# Configuration
UPLOAD_FOLDER = 'static/uploads/products'
BRAND_LOGOS_FOLDER = 'static/uploads/brands'

# Make sure upload directories exist
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
Path(BRAND_LOGOS_FOLDER).mkdir(parents=True, exist_ok=True)

# Sample sneaker data
SNEAKERS = [
    {
        "name": "Air Jordan 1 High OG Chicago",
        "brand": "Jordan",
        "category": "Lifestyle",
        "description": "The Air Jordan 1 High OG 'Chicago' features the iconic colorway that started it all, dressed in Bulls red and black.",
        "price": 180.00,
        "style_code": "DZ5485-612",
        "color": "Red/White/Black",
        "image_url": "https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/8b08b791-7c87-457a-9fc8-03db71bd7ada/air-jordan-1-high-shoes-MvZ9v0.png",
        "is_verified": True,
        "featured": True,
        "stock": 15
    },
    {
        "name": "Yeezy Boost 350 V2 Zebra",
        "brand": "Adidas",
        "category": "Lifestyle",
        "description": "The adidas Yeezy Boost 350 V2 'Zebra' features a white and black Primeknit upper with a red 'SPLY-350' branding.",
        "price": 220.00,
        "style_code": "CP9654",
        "color": "White/Core Black/Red",
        "image_url": "https://cdn.shopify.com/s/files/1/0603/3031/1875/products/main-square_95b8a57f-b5a9-422c-a552-1c32c94d7fca_1024x1024@2x.jpg",
        "is_verified": True,
        "featured": True,
        "stock": 10
    },
    {
        "name": "Nike Dunk Low Panda",
        "brand": "Nike",
        "category": "Lifestyle",
        "description": "The Nike Dunk Low 'Panda' features a simple but classic black and white colorway that goes with everything.",
        "price": 110.00,
        "style_code": "DD1391-100",
        "color": "White/Black",
        "image_url": "https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/5e7687f1-c13e-4bac-9530-148a8e4a2507/dunk-low-shoes-lkHNLP.png",
        "is_verified": True,
        "featured": True,
        "stock": 25
    },
    {
        "name": "New Balance 550 White Green",
        "brand": "New Balance",
        "category": "Lifestyle",
        "description": "The New Balance 550 'White Green' brings vintage basketball style to casual everyday wear.",
        "price": 120.00,
        "style_code": "BB550WT1",
        "color": "White/Green",
        "image_url": "https://nb.scene7.com/is/image/NB/bb550wt1_nb_02_i?$pdpflexf2$&wid=880&hei=880",
        "is_verified": True,
        "featured": False,
        "stock": 18
    },
    {
        "name": "Air Force 1 Low '07 White",
        "brand": "Nike",
        "category": "Lifestyle",
        "description": "The iconic Air Force 1 Low in classic all white, a staple in any sneaker collection.",
        "price": 100.00,
        "style_code": "CW2288-111",
        "color": "White/White",
        "image_url": "https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/b9026d85-06bd-4629-a727-dd68f6c49807/air-force-1-07-shoes-WrLlWX.png",
        "is_verified": True,
        "featured": False,
        "stock": 30
    },
    {
        "name": "Converse Chuck Taylor All Star High Top",
        "brand": "Converse",
        "category": "Lifestyle",
        "description": "The classic Chuck Taylor All Star High Top canvas sneaker never goes out of style.",
        "price": 60.00,
        "style_code": "M9160",
        "color": "Black/White",
        "image_url": "https://www.converse.com/dw/image/v2/BJJF_PRD/on/demandware.static/-/Sites-cnv-master-catalog/default/dw090f100e/images/a_107/M9160_A_107X1.jpg",
        "is_verified": True,
        "featured": False,
        "stock": 22
    },
    {
        "name": "Vans Old Skool",
        "brand": "Vans",
        "category": "Skateboarding",
        "description": "The Vans Old Skool is a classic skate shoe and the first to feature the iconic Vans side stripe.",
        "price": 65.00,
        "style_code": "VN000D3HY28",
        "color": "Black/White",
        "image_url": "https://images.vans.com/is/image/VansEU/VN000D3HY28-HERO?$PDP-FULL-IMAGE$",
        "is_verified": True,
        "featured": False,
        "stock": 20
    },
    {
        "name": "Air Jordan 4 Retro Thunder",
        "brand": "Jordan",
        "category": "Basketball",
        "description": "The Air Jordan 4 Retro 'Thunder' brings back the classic colorway inspired by Michael Jordan's Motorsports team.",
        "price": 210.00,
        "style_code": "DH6927-017",
        "color": "Black/Yellow",
        "image_url": "https://static.nike.com/a/images/t_PDP_1280_v1/f_auto,q_auto:eco/af529f29-e75f-4424-9f8b-5318a35825e5/air-jordan-4-retro-shoes-GtdSNs.png",
        "is_verified": True,
        "featured": True,
        "stock": 12
    },
    {
        "name": "Puma Suede Classic",
        "brand": "Puma",
        "category": "Lifestyle",
        "description": "The Puma Suede Classic is one of the most iconic sneakers in Puma's history, known for its soft suede upper.",
        "price": 70.00,
        "style_code": "352634-03",
        "color": "Blue/White",
        "image_url": "https://images.puma.com/image/upload/f_auto,q_auto,b_rgb:fafafa,w_1350,h_1350/global/374915/01/sv01/fnd/PNA/fmt/png/Suede-Classic-XXI-Sneakers",
        "is_verified": True,
        "featured": False,
        "stock": 15
    },
    {
        "name": "Reebok Classic Leather",
        "brand": "Reebok",
        "category": "Lifestyle",
        "description": "The Reebok Classic Leather is a timeless silhouette that combines style and comfort.",
        "price": 80.00,
        "style_code": "49799",
        "color": "White/Gum",
        "image_url": "https://assets.reebok.com/images/w_600,f_auto,q_auto/9aecc1a799bb468886f7addb0088cd9f_9366/Classic_Leather_Shoes_White_49799_01_standard.jpg",
        "is_verified": True,
        "featured": False,
        "stock": 18
    }
]

# Brands data
BRANDS = [
    {"name": "Nike", "slug": "nike", "description": "Nike sportswear and athletic shoes."},
    {"name": "Adidas", "slug": "adidas", "description": "Adidas sportswear and athletic shoes."},
    {"name": "Jordan", "slug": "jordan", "description": "Air Jordan basketball shoes and apparel."},
    {"name": "New Balance", "slug": "new-balance", "description": "New Balance athletic footwear."},
    {"name": "Puma", "slug": "puma", "description": "Puma sportswear and athletic shoes."},
    {"name": "Under Armour", "slug": "under-armour", "description": "Under Armour athletic apparel and footwear."},
    {"name": "Reebok", "slug": "reebok", "description": "Reebok sportswear and athletic shoes."},
    {"name": "Converse", "slug": "converse", "description": "Converse casual shoes and apparel."},
    {"name": "Vans", "slug": "vans", "description": "Vans skateboarding shoes and apparel."}
]

# Categories data
CATEGORIES = [
    {"name": "Basketball", "slug": "basketball", "description": "Basketball shoes for court performance."},
    {"name": "Running", "slug": "running", "description": "Running shoes for all types of runners."},
    {"name": "Lifestyle", "slug": "lifestyle", "description": "Casual, everyday sneakers."},
    {"name": "Training", "slug": "training", "description": "Training and gym shoes."},
    {"name": "Soccer", "slug": "soccer", "description": "Soccer cleats and indoor soccer shoes."},
    {"name": "Tennis", "slug": "tennis", "description": "Tennis shoes for court performance."},
    {"name": "Skateboarding", "slug": "skateboarding", "description": "Skate shoes for skateboarding."},
    {"name": "Walking", "slug": "walking", "description": "Walking shoes for comfort and support."}
]

# Common US shoe sizes
SIZES = [
    {"value": "4", "display_order": 1},
    {"value": "4.5", "display_order": 2},
    {"value": "5", "display_order": 3},
    {"value": "5.5", "display_order": 4},
    {"value": "6", "display_order": 5},
    {"value": "6.5", "display_order": 6},
    {"value": "7", "display_order": 7},
    {"value": "7.5", "display_order": 8},
    {"value": "8", "display_order": 9},
    {"value": "8.5", "display_order": 10},
    {"value": "9", "display_order": 11},
    {"value": "9.5", "display_order": 12},
    {"value": "10", "display_order": 13},
    {"value": "10.5", "display_order": 14},
    {"value": "11", "display_order": 15},
    {"value": "11.5", "display_order": 16},
    {"value": "12", "display_order": 17},
    {"value": "12.5", "display_order": 18},
    {"value": "13", "display_order": 19},
    {"value": "13.5", "display_order": 20},
    {"value": "14", "display_order": 21}
]

def download_image(url, save_path):
    """Download an image from a URL and save it to the specified path"""
    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Raise exception for non-200 status codes
        
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)
        
        return True
    except Exception as e:
        print(f"Error downloading image from {url}: {str(e)}")
        return False

def generate_slug(name):
    """Generate a URL-friendly slug from a name"""
    # Convert to lowercase and replace spaces with hyphens
    slug = name.lower().replace(' ', '-')
    
    # Remove special characters
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    
    # Add random suffix to ensure uniqueness
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    slug = f"{slug}-{random_suffix}"
    
    return slug

def populate_database():
    """Populate the database with brands, categories, sizes, and products"""
    with app.app_context():
        print("Starting database population...")
        
        # Create admin user
        try:
            admin = User.query.filter_by(email="admin@kickx.com").first()
            if not admin:
                admin = User(
                    username="admin",
                    email="admin@kickx.com",
                    first_name="Admin",
                    last_name="User",
                    is_admin=True
                )
                admin.set_password("adminpass")
                db.session.add(admin)
                print("Admin user created!")
            else:
                print("Admin user already exists")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {str(e)}")
        
        # Create test user
        try:
            test_user = User.query.filter_by(email="user@kickx.com").first()
            if not test_user:
                test_user = User(
                    username="testuser",
                    email="user@kickx.com",
                    first_name="Test",
                    last_name="User"
                )
                test_user.set_password("userpass")
                db.session.add(test_user)
                print("Test user created!")
            else:
                print("Test user already exists")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test user: {str(e)}")
        
        # Add brands
        brand_objects = {}
        for brand_data in BRANDS:
            try:
                brand = Brand.query.filter_by(name=brand_data["name"]).first()
                if not brand:
                    brand = Brand(
                        name=brand_data["name"],
                        slug=brand_data["slug"],
                        description=brand_data["description"]
                    )
                    db.session.add(brand)
                    print(f"Added brand: {brand_data['name']}")
                else:
                    print(f"Brand already exists: {brand_data['name']}")
                    
                # Store brand object for later use
                brand_objects[brand_data["name"]] = brand
            except IntegrityError:
                db.session.rollback()
                print(f"Error adding brand: {brand_data['name']}")
        
        # Add categories
        category_objects = {}
        for category_data in CATEGORIES:
            try:
                category = Category.query.filter_by(name=category_data["name"]).first()
                if not category:
                    category = Category(
                        name=category_data["name"],
                        slug=category_data["slug"],
                        description=category_data["description"]
                    )
                    db.session.add(category)
                    print(f"Added category: {category_data['name']}")
                else:
                    print(f"Category already exists: {category_data['name']}")
                    
                # Store category object for later use
                category_objects[category_data["name"]] = category
            except IntegrityError:
                db.session.rollback()
                print(f"Error adding category: {category_data['name']}")
        
        # Add sizes
        size_objects = {}
        for size_data in SIZES:
            try:
                size = Size.query.filter_by(value=size_data["value"]).first()
                if not size:
                    size = Size(
                        value=size_data["value"],
                        display_order=size_data["display_order"]
                    )
                    db.session.add(size)
                    print(f"Added size: {size_data['value']}")
                else:
                    print(f"Size already exists: {size_data['value']}")
                    
                # Store size object for later use
                size_objects[size_data["value"]] = size
            except IntegrityError:
                db.session.rollback()
                print(f"Error adding size: {size_data['value']}")
        
        # Commit changes so far
        db.session.commit()
        
        # Add products with downloaded images
        for sneaker_data in SNEAKERS:
            try:
                # Create a unique slug for the product
                slug = generate_slug(sneaker_data["name"])
                
                # Check if product already exists
                existing_product = Product.query.filter_by(name=sneaker_data["name"]).first()
                if existing_product:
                    print(f"Product already exists: {sneaker_data['name']}")
                    continue
                
                # Download the image
                image_url = sneaker_data["image_url"]
                filename = f"{slug}_{int(time.time())}.jpg"
                save_path = os.path.join(UPLOAD_FOLDER, filename)
                
                image_downloaded = download_image(image_url, save_path)
                if image_downloaded:
                    local_image_url = f"/static/uploads/products/{filename}"
                else:
                    # If download fails, use the original URL as fallback
                    local_image_url = image_url
                
                # Get brand and category objects
                brand = brand_objects.get(sneaker_data["brand"])
                category = category_objects.get(sneaker_data["category"])
                
                if not brand or not category:
                    print(f"Could not find brand or category for {sneaker_data['name']}")
                    continue
                
                # Create release date (random date in the past year)
                days_ago = random.randint(0, 365)
                release_date = datetime.now() - timedelta(days=days_ago)
                
                # Create product
                product = Product(
                    name=sneaker_data["name"],
                    slug=slug,
                    description=sneaker_data["description"],
                    price=sneaker_data["price"],
                    stock=sneaker_data["stock"],
                    image_url=local_image_url,
                    brand_id=brand.id,
                    category_id=category.id,
                    color=sneaker_data["color"],
                    style_code=sneaker_data["style_code"],
                    release_date=release_date,
                    is_verified=sneaker_data["is_verified"],
                    featured=sneaker_data["featured"],
                    views=random.randint(0, 1000)  # Random view count
                )
                
                db.session.add(product)
                db.session.flush()  # Flush to get product ID
                
                # Add product sizes with random stock
                available_sizes = random.sample(list(size_objects.keys()), random.randint(8, 15))
                for size_value in available_sizes:
                    size = size_objects[size_value]
                    size_stock = random.randint(0, 10)
                    if size_stock > 0:
                        product_size = ProductSize(
                            product_id=product.id,
                            size_id=size.id,
                            stock=size_stock
                        )
                        db.session.add(product_size)
                
                print(f"Added product: {sneaker_data['name']}")
                
            except Exception as e:
                db.session.rollback()
                print(f"Error adding product {sneaker_data['name']}: {str(e)}")
        
        # Commit all changes
        db.session.commit()
        print("Database population completed!")

if __name__ == "__main__":
    populate_database() 