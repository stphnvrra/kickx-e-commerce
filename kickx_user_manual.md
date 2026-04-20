# KickX User Manual

## Creating an Account & Signing In

### Registration
- **URL:** `/register`
- Create a new account by providing your email, username, first name, last name, and password
- All fields are required for registration
- Your email and username must be unique

### Login
- **URL:** `/login`
- Sign in with your email and password
- Option to remember your login session
- If you forget your password, use the "Forgot Password" link

### Logout
- **URL:** `/logout`
- Click to end your session and log out

---

## Browsing Products

### Home Page
- **URL:** `/`
- Features trending products, new arrivals, and featured items
- Personalized recommendations for logged-in users

### Product Catalog
- **URL:** `/products`
- Browse the complete sneaker collection
- Filter products by:
  - Category
  - Brand
  - Size
  - Price range
  - Verification status
- Sort options:
  - Newest
  - Price: Low to High
  - Price: High to Low
  - Popularity

### New Arrivals
- **URL:** `/products/new-arrivals`
- Latest additions to the store

### Trending Products
- **URL:** `/products/trending`
- Most popular items based on user views

### Search
- **URL:** `/search?q=your_search_terms`
- Find products by name, brand, or keywords

---

## Product Details

### View Product
- **URL:** `/products/<product_slug>`
- Detailed product information including:
  - Brand and verification status
  - Price
  - Release date
  - Available sizes with stock information
  - Product description
  - Reviews and ratings
- Related product recommendations
- Size selection (required for cart or wishlist)
- Quantity selection (1-10 items)

---

## Shopping Cart

### View Cart
- **URL:** `/cart`
- See all products added to your cart
- Each item shows:
  - Product image and name
  - Size
  - Unit price
  - Quantity
  - Total price
- Displays cart subtotal and shipping costs

### Add to Cart
- From product detail page, select size and quantity
- Click "Add to Cart" button

### Update Cart
- Change quantity for items
- Remove individual items
- Empty entire cart

### Buy Now
- Bypass cart and go directly to checkout with a specific item

---

## Wishlist

### View Wishlist
- **URL:** `/profile/wishlist`
- See saved items for future purchase
- Displays total value of wishlist items

### Add to Wishlist
- From product detail page, select size
- Click heart icon to add to wishlist

### Manage Wishlist
- Remove items from wishlist
- Move items directly to cart

---

## Checkout Process

### Checkout Overview
- **URL:** `/checkout`
- Review items, quantities, and total cost before proceeding

### Shipping Address
- **URL:** `/checkout/address`
- Select existing address or add a new one
- Required fields: full name, phone number, street address, city, state, postal code, and country

### Payment
- **URL:** `/checkout/payment`
- Select payment method (PayPal supported)
- Review order details including:
  - Items
  - Subtotal
  - Shipping fee
  - Total amount

### Order Confirmation
- **URL:** `/checkout/confirmation/<order_id>`
- Order summary with estimated delivery date
- Order ID for future reference

---

## Order Management

### Order History
- **URL:** `/profile/orders`
- View all past orders with status
- Sort by date, status, or amount

### Order Details
- **URL:** `/profile/order/<order_id>`
- Complete information about a specific order:
  - Order status
  - Payment status
  - Shipping information
  - Items ordered with prices
  - Tracking number (if available)

---

## User Profile

### Dashboard
- **URL:** `/profile`
- Overview of account information
- Recent orders
- Saved addresses

### Profile Settings
- **URL:** `/profile/settings`
- Update personal information
- Change email address
- Change password

### Address Management
- **URL:** `/profile/addresses`
- View saved shipping addresses
- Add new addresses
- Edit existing addresses
- Set default address
- Delete addresses

---

## Writing Reviews

### Add/Edit Review
- From product detail page
- Rate product from 1-5 stars
- Write detailed comments about your experience
- Edit your existing review if you've already submitted one

---

## Notifications

### View Notifications
- **URL:** `/notifications`
- See important updates about:
  - Order status changes
  - Price drops
  - New arrivals
  - Authentication updates

### Manage Notifications
- Mark individual notifications as read
- Mark all notifications as read 