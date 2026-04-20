import asyncio
from playwright.async_api import async_playwright
import os

async def capture_screenshots():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1280, 'height': 800})
        page = await context.new_page()
        
        base_url = "http://127.0.0.1:5001"
        screenshot_dir = "screenshots"
        
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        print("Logging in as admin...")
        await page.goto(f"{base_url}/login")
        await page.fill('input[name="email"]', 'newadmin@g.com')
        await page.fill('input[name="password"]', 'newadmin123')
        await page.click('button[type="submit"]')
        
        # Wait for the login redirect to finish (e.g., waiting for the logout button to appear or sleep)
        await page.wait_for_load_state("networkidle")
        await asyncio.sleep(2)
        
        print("Capturing 6 key pages...")
        
        # 1. Home Page
        print("- Home Page")
        await page.goto(f"{base_url}/")
        await asyncio.sleep(2)  # Wait for animations
        await page.screenshot(path=f"{screenshot_dir}/01_homepage.png", full_page=True)
        
        # 2. Product Catalog
        print("- Product Catalog")
        await page.goto(f"{base_url}/products")
        await asyncio.sleep(2)
        await page.screenshot(path=f"{screenshot_dir}/02_catalog.png", full_page=True)
        
        # 3. Product Detail (Air Force 1)
        print("- Product Detail")
        await page.goto(f"{base_url}/products/air-force-1-low-07-white-5c92")
        await asyncio.sleep(2)
        await page.screenshot(path=f"{screenshot_dir}/03_product_detail.png", full_page=True)
        
        # 4. Shopping Cart (Add to cart first)
        print("- Shopping Cart")
        # Try to find 'Add to Cart' button or select size first if required
        try:
            # Select first available size if size selection exists
            size_options = await page.query_selector_all('select[name="size_id"] option')
            if size_options and len(size_options) > 1:
                await page.select_option('select[name="size_id"]', index=1)
            
            await page.click('button:has-text("Add to Cart")')
            await page.wait_for_url(f"{base_url}/cart")
        except:
            print("Could not add to cart automatically, capturing empty cart or current page.")
            await page.goto(f"{base_url}/cart")
            
        await asyncio.sleep(2)
        await page.screenshot(path=f"{screenshot_dir}/04_cart.png", full_page=True)
        
        # 5. Admin Dashboard
        print("- Admin Dashboard")
        await page.goto(f"{base_url}/admin")
        await asyncio.sleep(2)
        await page.screenshot(path=f"{screenshot_dir}/05_admin_dashboard.png", full_page=True)
        
        # 6. Admin Product Management
        print("- Admin Products")
        await page.goto(f"{base_url}/admin/products")
        await asyncio.sleep(2)
        await page.screenshot(path=f"{screenshot_dir}/06_admin_products.png", full_page=True)
        
        await browser.close()
        print("Done! Screenshots saved in 'screenshots/' folder.")

if __name__ == "__main__":
    asyncio.run(capture_screenshots())
