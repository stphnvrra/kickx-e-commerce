# KickX E-Commerce 👟🔥

KickX E-Commerce is a premium, high-end web application for authentic sneaker retail. Built on a powerful Python/Flask backend and styled with a custom, modern design system, KickX offers a seamless, secure, and visually stunning sneaker shopping experience. 

The application features user authentication, dynamic catalog sorting/filtering, a remote Supabase PostgreSQL database, custom reviews, a secure checkout flow, and an intelligent recommendation engine built using **Pandas** and **NumPy**.

---

## 🌟 Premium Features

### 🎨 Visual & UX Excellence
- **Outfit & Inter Typography**: Styled with high-contrast fonts (`Outfit` for headings/branding, `Inter` for clean readability).
- **Glassmorphic Fixed Header**: A transparent-orange gradient top navigation bar that dynamically scrolls and clears content layouts.
- **Unified Product Cards**: Modern sneaker display cards featuring custom shadows, hover micro-animations, green "Verified Authentic" trust badges, and wishlist action triggers.
- **Size Selector Grid**: Custom interactive size pills showing stock count and size parameters, highlighting the active selection with a dark slide-in transition.

### 🔌 Intelligent Features
- **Numpy/Pandas Recommendation Engine**: Utilizes structured product view matrices, user preference data, and brand/category matches to rank and serve personalized recommendations (New Arrivals, Hot/Trending, and similar models).
- **Interactive Wishlist**: Real-time asynchronous endpoints let users bookmark favorites directly from product grids or detail views.
- **Comprehensive Reviews System**: Multi-point star ratings and detailed textual reviews with user summaries.
- **Admin Management Panel**: Dashboard to configure products, inventory, orders, user roles, and adjust recommendation thresholds.

### 💳 Transaction Flow
- **Shopping Cart & Direct Buy**: Support for regular checkout queues or instant "Buy Now" pathways.
- **Multiple Address Book**: Multi-address management with defaults.
- **Order & Shipping Tracking**: Complete address verification, shipping setup, and order creation flows.

---

## 🛠️ Tech Stack

- **Backend**: Python 3, Flask, Flask-Login, Flask-SQLAlchemy (ORM)
- **Database**: Supabase (PostgreSQL)
- **Data Science**: Pandas, NumPy
- **Frontend**: Jinja2 Templates, Bootstrap 5, Custom Vanilla CSS
- **Deployment**: Vercel configuration ready (`vercel.json`, `api/index.py`)

---

## 📁 Project Directory Structure

```text
├── kickx_app.py                # Main Flask application (routes, business logic)
├── recommendation_engine.py     # Pandas & Numpy-based recommendation model
├── vercel.json                 # Vercel deployment route handler config
├── api/
│   └── index.py                # Serverless entry point for Vercel deployment
├── static/
│   ├── css/
│   │   └── style.css           # Premium vanilla CSS styling system
│   ├── images/
│   │   ├── hero_bg.jpg         # Sneaker boutique lifestyle hero background
│   │   └── favicon.png         # Brand favicon asset
│   └── uploads/
│       └── products/           # Seeded product high-res images
├── templates/
│   ├── base.html               # Base structural shell & fixed header
│   ├── auth/                   # login.html, register.html, forgot_password.html
│   ├── main/                   # index.html (Hero Home), featured.html
│   └── products/               # catalog.html, detail.html, category.html, trending.html
└── requirements.txt            # Python dependencies list
```

---

## 🚀 Installation & Local Development

### Prerequisites
- Python 3.8+ installed on your system.

### Step-by-Step Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/stphnvrra/kickz-e-commerce.git
   cd kickz-e-commerce
   ```

2. **Set Up Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Seed the Database**
   Initialize database schemas, default admin users, and premium product listings:
   ```bash
   # Run users setup
   python3 MISC/important/create_users.py
   
   # Populate store catalog with items
   python3 MISC/populate_db.py
   ```

5. **Configure Supabase Database**
   Set the `DATABASE_URL` environment variable or edit `SQLALCHEMY_DATABASE_URI` configuration to connect to your Supabase PostgreSQL database:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql://postgres:your_password@db.supabase.co:5432/postgres"
   ```

6. **Start the Development Server**
   ```bash
   python3 kickx_app.py
   ```
   Open your browser and navigate to `http://127.0.0.1:5001`.

---

## ⚡ Deployment to Vercel

The application is pre-configured to build and run as a serverless Flask app on Vercel.

1. **Prerequisites**: Install the Vercel CLI:
   ```bash
   npm install -g vercel
   ```
2. **Deploy**:
   ```bash
   vercel --prod
   ```
   Vercel will build the workspace using Python runtime, route requests through `api/index.py`, and host static assets under the `/static` prefix.

---

## 📄 License

This project is built and maintained for demonstration, educational, and portfolio purposes.
