from kickx_app import app, db, User, Cart, Wishlist
from datetime import datetime

def main():
    with app.app_context():
            admin = User(
                username='admin123',
                email='admin1@g.com',
                first_name='Admin',
                last_name='Admin1',
                is_admin=True
            )
            admin.set_password('admin')
            db.session.add(admin)

            
            # Create cart and wishlist for admin
            admin_cart = Cart(user=admin)
            admin_wishlist = Wishlist(user=admin)
            db.session.add(admin_cart)
            db.session.add(admin_wishlist)
            print("Created admin user: admin / admin123")

    
        
            # Commit changes
            db.session.commit()
            print("Database updated successfully")

if __name__ == "__main__":
    main() 