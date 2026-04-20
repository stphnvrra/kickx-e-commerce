from kickx_app import app, db, Brand, Category, Size
from sqlalchemy.exc import IntegrityError

# Function to initialize the database with brands, categories, and sizes
def populate_db():
    with app.app_context():
        # Create brands
        brands = [
            {"id": 1, "name": "Nike", "slug": "nike", "description": "Nike sportswear and athletic shoes."},
            {"id": 2, "name": "Adidas", "slug": "adidas", "description": "Adidas sportswear and athletic shoes."},
            {"id": 3, "name": "Jordan", "slug": "jordan", "description": "Air Jordan basketball shoes and apparel."},
            {"id": 4, "name": "New Balance", "slug": "new-balance", "description": "New Balance athletic footwear."},
            {"id": 5, "name": "Puma", "slug": "puma", "description": "Puma sportswear and athletic shoes."},
            {"id": 6, "name": "Under Armour", "slug": "under-armour", "description": "Under Armour athletic apparel and footwear."},
            {"id": 7, "name": "Reebok", "slug": "reebok", "description": "Reebok sportswear and athletic shoes."},
            {"id": 8, "name": "Converse", "slug": "converse", "description": "Converse casual shoes and apparel."},
            {"id": 9, "name": "Vans", "slug": "vans", "description": "Vans skateboarding shoes and apparel."}
        ]
        
        # Create categories
        categories = [
            {"id": 1, "name": "Basketball", "slug": "basketball", "description": "Basketball shoes for court performance."},
            {"id": 2, "name": "Running", "slug": "running", "description": "Running shoes for all types of runners."},
            {"id": 3, "name": "Lifestyle", "slug": "lifestyle", "description": "Casual, everyday sneakers."},
            {"id": 4, "name": "Training", "slug": "training", "description": "Training and gym shoes."},
            {"id": 5, "name": "Soccer", "slug": "soccer", "description": "Soccer cleats and indoor soccer shoes."},
            {"id": 6, "name": "Tennis", "slug": "tennis", "description": "Tennis shoes for court performance."},
            {"id": 7, "name": "Skateboarding", "slug": "skateboarding", "description": "Skate shoes for skateboarding."},
            {"id": 8, "name": "Walking", "slug": "walking", "description": "Walking shoes for comfort and support."}
        ]
        
        # Create sizes for sneakers
        sizes = [
            {"id": 1, "value": "US 6", "display_order": 1},
            {"id": 2, "value": "US 6.5", "display_order": 2},
            {"id": 3, "value": "US 7", "display_order": 3},
            {"id": 4, "value": "US 7.5", "display_order": 4},
            {"id": 5, "value": "US 8", "display_order": 5},
            {"id": 6, "value": "US 8.5", "display_order": 6},
            {"id": 7, "value": "US 9", "display_order": 7},
            {"id": 8, "value": "US 9.5", "display_order": 8},
            {"id": 9, "value": "US 10", "display_order": 9},
            {"id": 10, "value": "US 10.5", "display_order": 10},
            {"id": 11, "value": "US 11", "display_order": 11},
            {"id": 12, "value": "US 11.5", "display_order": 12},
            {"id": 13, "value": "US 12", "display_order": 13},
            {"id": 14, "value": "US 12.5", "display_order": 14},
            {"id": 15, "value": "US 13", "display_order": 15}
        ]
        
        # Add brands to database
        for brand_data in brands:
            try:
                brand = Brand.query.get(brand_data["id"])
                if not brand:
                    brand = Brand(
                        id=brand_data["id"],
                        name=brand_data["name"],
                        slug=brand_data["slug"],
                        description=brand_data["description"]
                    )
                    db.session.add(brand)
                    print(f"Added brand: {brand_data['name']}")
                else:
                    print(f"Brand already exists: {brand_data['name']}")
            except IntegrityError:
                db.session.rollback()
                print(f"Error adding brand: {brand_data['name']}")
        
        # Add categories to database
        for category_data in categories:
            try:
                category = Category.query.get(category_data["id"])
                if not category:
                    category = Category(
                        id=category_data["id"],
                        name=category_data["name"],
                        slug=category_data["slug"],
                        description=category_data["description"]
                    )
                    db.session.add(category)
                    print(f"Added category: {category_data['name']}")
                else:
                    print(f"Category already exists: {category_data['name']}")
            except IntegrityError:
                db.session.rollback()
                print(f"Error adding category: {category_data['name']}")
                
        # Add sizes to database
        for size_data in sizes:
            try:
                size = Size.query.get(size_data["id"])
                if not size:
                    size = Size(
                        id=size_data["id"],
                        value=size_data["value"],
                        display_order=size_data["display_order"]
                    )
                    db.session.add(size)
                    print(f"Added size: {size_data['value']}")
                else:
                    print(f"Size already exists: {size_data['value']}")
            except IntegrityError:
                db.session.rollback()
                print(f"Error adding size: {size_data['value']}")
        
        # Commit changes
        db.session.commit()
        print("Database population completed!")

if __name__ == "__main__":
    populate_db() 