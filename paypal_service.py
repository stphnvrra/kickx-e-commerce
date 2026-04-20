"""
PayPal Service for API interactions
"""
import requests
import json
from paypal_config import get_paypal_config, PAYPAL_API_BASE_URL

class PayPalService:
    def __init__(self):
        self.config = get_paypal_config()
        self.client_id = self.config['client_id']
        self.client_secret = self.config['client_secret']
        self.api_base_url = self.config['api_base_url']
        
    def get_access_token(self):
        """
        Get PayPal access token
        """
        auth_url = f'{self.api_base_url}/v1/oauth2/token'
        headers = {
            'Accept': 'application/json',
            'Accept-Language': 'en_US'
        }
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(
            auth_url, 
            auth=(self.client_id, self.client_secret),
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            # Log the error
            print(f"PayPal auth error: {response.text}")
            return None

    def create_order(self, total_amount, shipping_cost, items, currency='PHP'):
        """
        Create a PayPal order
        """
        access_token = self.get_access_token()
        if not access_token:
            return None
        
        create_order_url = f'{self.api_base_url}/v2/checkout/orders'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        # Create order items list
        order_items = []
        item_total = 0
        for item in items:
            price = item.product.price
            quantity = item.quantity
            item_total += price * quantity
            order_items.append({
                'name': item.product.name,
                'description': f"Size: {item.size}",
                'quantity': str(quantity),
                'unit_amount': {
                    'currency_code': currency,
                    'value': str(price)
                },
                'category': 'PHYSICAL_GOODS'
            })
        
        # Create the order payload
        payload = {
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {
                    'currency_code': currency,
                    'value': "1",
                    'breakdown': {
                        'item_total': {
                            'currency_code': currency,
                            'value': str(item_total)
                        },
                        'shipping': {
                            'currency_code': currency,
                            'value': str(shipping_cost)
                        }
                    }
                },
                'items': order_items
            }],
            'application_context': {
                'return_url': f'https://99d4-120-28-195-60.ngrok-free.app/{self.config["return_url"]}',
                'cancel_url': f'https://99d4-120-28-195-60.ngrok-free.app/{self.config["cancel_url"]}'
            }
        }
        
        response = requests.post(
            create_order_url,
            headers=headers,
            data=json.dumps(payload)
        )
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            # Log the error
            print(f"PayPal create order error: {response.text}")
            return None
            
    def capture_order(self, order_id):
        """
        Capture an approved PayPal order
        """
        access_token = self.get_access_token()
        if not access_token:
            return None
            
        capture_url = f'{self.api_base_url}/v2/checkout/orders/{order_id}/capture'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.post(capture_url, headers=headers)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            # Log the error
            print(f"PayPal capture order error: {response.text}")
            return None
            
    def get_order_details(self, order_id):
        """
        Get details of a PayPal order
        """
        access_token = self.get_access_token()
        if not access_token:
            return None
            
        order_url = f'{self.api_base_url}/v2/checkout/orders/{order_id}'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {access_token}'
        }
        
        response = requests.get(order_url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            # Log the error
            print(f"PayPal get order error: {response.text}")
            return None 