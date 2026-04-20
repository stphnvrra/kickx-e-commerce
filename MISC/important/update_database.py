from kickx_app import app, db, Product, WishlistItem, Size
from sqlalchemy import inspect

print("Starting database update...")

# Create application context
with app.app_context():
    inspector = inspect(db.engine)
    needs_update = False
    
    # Check for is_verified column in Product table
    try:
        # First try to query with is_verified to see if it exists
        try:
            Product.query.filter_by(is_verified=True).first()
            print("The is_verified column already exists in the Product table.")
        except Exception as e:
            if "no such column: product.is_verified" in str(e):
                print("The is_verified column does not exist.")
                needs_update = True
            else:
                print(f"An error occurred: {str(e)}")
    except Exception as e:
        print(f"Error checking Product table: {str(e)}")
        needs_update = True
    
    # Check for new columns in WishlistItem table
    try:
        # Check if the WishlistItem table exists
        if 'wishlist_item' in inspector.get_table_names():
            # Get existing columns
            columns = [column['name'] for column in inspector.get_columns('wishlist_item')]
            if 'size_id' not in columns or 'quantity' not in columns or 'size' not in columns:
                print("WishlistItem table is missing new columns (size_id, quantity, or size).")
                needs_update = True
            else:
                print("WishlistItem table already has the required columns.")
        else:
            print("WishlistItem table does not exist.")
            needs_update = True
    except Exception as e:
        print(f"Error checking WishlistItem table: {str(e)}")
        needs_update = True
    
    # Update database schema if needed
    if needs_update:
        print("Updating database schema...")
        # Drop all tables and recreate them
        try:
            db.drop_all()
            db.create_all()
            print("Database schema updated successfully!")
        except Exception as e:
            print(f"Error updating database schema: {str(e)}")
    else:
        print("Database schema is up to date.")

print("Database update completed!") 