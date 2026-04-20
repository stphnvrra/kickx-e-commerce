from kickx_app import app, db, Size
from sqlalchemy.exc import IntegrityError

# Common US shoe sizes with display order
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

def populate_sizes():
    with app.app_context():
        for size_data in SIZES:
            try:
                # Check if size already exists
                existing_size = Size.query.filter_by(value=size_data["value"]).first()
                
                if not existing_size:
                    # Create new size
                    size = Size(
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
        
        # Commit all changes
        db.session.commit()
        print("Size data population completed!")

if __name__ == "__main__":
    populate_sizes() 