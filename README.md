# KickX E-Commerce

KickX E-Commerce is a comprehensive, modern sneakers web application built with Python and Flask. It provides a complete e-commerce experience including user authentication, product catalog, a recommendation engine, and secure checkout using the PayPal SDK.

## Key Features

- **User Authentication**: Secure sign-up, login, and profile management using Flask-Login and Werkzeug security.
- **Product Catalog**: Browse, sort, and filter a wide selection of sneakers by brand, category, size, and price. Includes out-of-the-box support for sizes and stock management.
- **Intelligent Recommendation Engine**: Built using Pandas and Numpy to analyze product views, trends, and user history to provide personalized recommendations (Trending, New Arrivals, Related Products).
- **Shopping Cart & Checkout**: Add verified sneakers to your cart, set shipping addresses, and securely checkout using the integration with PayPal SDK.
- **Wishlist & Reviews**: Users can save items to their wishlist for later and leave ratings/reviews on purchased products.
- **Order Management & Tracking**: View order history, track order statuses, and receive notifications for price drops, new arrivals, and restocks.
- **Admin Dashboard**: Specialized dashboard for administrators to manage products, users, orders, notifications, and tweak the recommendation engine thresholds.

## Tech Stack

- **Backend framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM (Flask-SQLAlchemy)
- **Payment Gateway**: PayPal SDK (`paypal-checkout-server-sdk`)
- **Data Analysis / Engine**: Pandas, NumPy
- **Frontend**: HTML5, CSS3, JavaScript (Jinja2 Templates & Bootstrap 5)

## Installation & Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/stphnvrra/kickz-e-commerce.git
   cd kickz-e-commerce
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r MISC/important/requirements.txt
   ```

3. **Initialize the Database**
   ```bash
   python MISC/important/create_users.py
   python MISC/populate_db.py
   ```

4. **Configuration**
   Ensure your PayPal credentials are set up inside `paypal_config.py`.

5. **Run the Application**
   ```bash
   python kickx_app.py
   ```
   Navigate to `http://127.0.0.1:5000` in your web browser.

## Project Structure

- `kickx_app.py` - the main application and route definitions.
- `recommendation_engine.py` - Pandas/Numpy-based logic for product recommendations.
- `paypal_service.py` & `paypal_config.py` - handles communication with the PayPal APIs.
- `templates/` - contains all HTML pages, organized by user, admin, and products.
- `static/` - stores CSS, JavaScript, and product uploads.
- `kickx_user_manual.md` - deeper guide on the application usages & navigation flows.

## License

This project is intended for demonstration and educational purposes.
