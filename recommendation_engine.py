"""
Kickx Recommendation Engine

This module provides a recommendation engine for the Kickx e-commerce platform.
It implements content-based filtering, collaborative filtering, and a hybrid approach.
"""

import numpy as np
import pandas as pd
from collections import defaultdict
import json
import os
from datetime import datetime, timedelta
from sklearn.metrics.pairwise import cosine_similarity

# Global recommendation engine instance
_recommendation_engine = None

def get_recommendation_engine():
    """Get the global recommendation engine instance."""
    return _recommendation_engine

def init_recommendation_engine(db):
    """Initialize the recommendation engine."""
    global _recommendation_engine
    _recommendation_engine = RecommendationEngine(db)
    return _recommendation_engine

class RecommendationEngine:
    """Recommendation engine for the KickX application."""
    
    def __init__(self, db):
        """Initialize the recommendation engine with database connection."""
        self.db = db
        self.settings_file = 'recommendation_settings.json'
        self.recommendations_cache = {}
        self.content_similarity_matrix = None
        self.collaborative_similarity_matrix = None
        self.product_index_map = {}  # Maps product_id to index in similarity matrices
        self.user_product_matrix = None
        self.last_rebuild = None
        
        # Load default settings or existing settings
        self.settings = self.load_settings()
        
        # Don't build model immediately to avoid circular import issues
        # The model will be built when first needed
    
    def load_settings(self):
        """Load recommendation engine settings from file."""
        default_settings = {
            'content_based_weight': 0.6,
            'collaborative_weight': 0.4,
            'min_recommendation_confidence': 0.3,
            'max_recommendations_per_product': 6,
            'enable_personalized_home': True,
            'recommendation_refresh_hours': 24,
            'trending_timespan_days': 7
        }
        
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading settings: {str(e)}")
                
        return default_settings
    
    def save_settings(self, settings):
        """Save recommendation engine settings to file."""
        self.settings = settings
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
            return True
        except Exception as e:
            print(f"Error saving settings: {str(e)}")
            return False
    
    def build_model(self):
        """Build the recommendation model using content-based and collaborative filtering."""
        try:
            # Set timestamp for when the model was built
            self.last_rebuild = datetime.now()
            
            # Build content-based similarity matrix
            self._build_content_based_model()
            
            # Build collaborative filtering model
            self._build_collaborative_model()
            
            # Pre-compute recommendations for all products
            self._cache_all_recommendations()
            
            return True
        except Exception as e:
            print(f"Error building model: {str(e)}")
            return False
    
    def _build_content_based_model(self):
        """Build content-based filtering model based on product attributes."""
        try:
            # Get Product model from registry
            Product = self.db.Model.registry._class_registry.get('Product')
            
            if Product is None:
                print("Product model not found in registry")
                return
                
            # Get all products
            products = Product.query.all()
            if not products:
                return
            
            # Create a mapping from product_id to index
            self.product_index_map = {product.id: i for i, product in enumerate(products)}
            
            # Create feature matrix for products
            feature_matrix = np.zeros((len(products), 4))  # brand_id, category_id, price_bin, color_encoded
            
            # Price normalization
            prices = np.array([p.price for p in products])
            price_mean = prices.mean()
            price_std = prices.std() if prices.std() > 0 else 1
            
            # Map colors to integers (simplified)
            color_map = {}
            color_index = 0
            
            for i, product in enumerate(products):
                # Brand ID
                feature_matrix[i, 0] = product.brand_id if product.brand_id is not None else 0
                
                # Category ID
                feature_matrix[i, 1] = product.category_id if product.category_id is not None else 0
                
                # Normalized price (bin into 5 ranges)
                normalized_price = (product.price - price_mean) / price_std
                feature_matrix[i, 2] = min(max(int(normalized_price + 2.5), 0), 4)  # 0-4 range
                
                # Color encoding
                if product.color and product.color not in color_map:
                    color_map[product.color] = color_index
                    color_index += 1
                feature_matrix[i, 3] = color_map.get(product.color, 0) if product.color else 0
            
            # Compute content-based similarity matrix
            self.content_similarity_matrix = cosine_similarity(feature_matrix)
            
        except Exception as e:
            print(f"Error building content-based model: {str(e)}")
    
    def _build_collaborative_model(self):
        """Build collaborative filtering model based on user behavior."""
        try:
            # Get models from registry
            User = self.db.Model.registry._class_registry.get('User')
            Product = self.db.Model.registry._class_registry.get('Product')
            Order = self.db.Model.registry._class_registry.get('Order')
            OrderItem = self.db.Model.registry._class_registry.get('OrderItem')
            Review = self.db.Model.registry._class_registry.get('Review')
            WishlistItem = self.db.Model.registry._class_registry.get('WishlistItem')
            
            if not all([User, Product, Order, OrderItem]):
                print("Required models not found in registry")
                return
            
            users = User.query.all()
            products = Product.query.all()
            
            if not users or not products:
                return
            
            # Create user-product interaction matrix
            user_index_map = {user.id: i for i, user in enumerate(users)}
            
            # Initialize user-product matrix
            self.user_product_matrix = np.zeros((len(users), len(products)))
            
            # Fill matrix with user interactions
            # Orders (highest weight: 3.0)
            orders = Order.query.all()
            for order in orders:
                user_idx = user_index_map.get(order.user_id)
                if user_idx is None:
                    continue
                    
                for item in order.items:
                    product_idx = self.product_index_map.get(item.product_id)
                    if product_idx is not None:
                        self.user_product_matrix[user_idx, product_idx] = 3.0
            
            # Reviews (weight based on rating: 0.5-2.5)
            reviews = Review.query.all()
            for review in reviews:
                user_idx = user_index_map.get(review.user_id)
                product_idx = self.product_index_map.get(review.product_id)
                if user_idx is not None and product_idx is not None:
                    self.user_product_matrix[user_idx, product_idx] = max(
                        self.user_product_matrix[user_idx, product_idx],
                        0.5 * review.rating  # 0.5 * (1-5) = 0.5-2.5
                    )
            
            # Wishlist items (weight: 1.0)
            wishlist_items = WishlistItem.query.all()
            for item in wishlist_items:
                # Need to get user_id from wishlist
                wishlist = self.db.session.get(self.db.get_class('Wishlist'), item.wishlist_id)
                if wishlist:
                    user_idx = user_index_map.get(wishlist.user_id)
                    product_idx = self.product_index_map.get(item.product_id)
                    if user_idx is not None and product_idx is not None:
                        self.user_product_matrix[user_idx, product_idx] = max(
                            self.user_product_matrix[user_idx, product_idx],
                            1.0
                        )
            
            # Compute collaborative similarity matrix (item-item collaborative filtering)
            # Use cosine similarity between product columns
            self.collaborative_similarity_matrix = cosine_similarity(self.user_product_matrix.T)
            
        except Exception as e:
            print(f"Error building collaborative model: {str(e)}")
    
    def _cache_all_recommendations(self):
        """Pre-compute and cache recommendations for all products."""
        try:
            # Get all products
            Product = self.db.Model.registry._class_registry.get('Product')
            products = Product.query.all()
            
            # Generate recommendations for each product
            for product in products:
                recommendations = self._generate_hybrid_recommendations(product.id)
                self.recommendations_cache[product.id] = recommendations
                
        except Exception as e:
            print(f"Error caching recommendations: {str(e)}")
    
    def _generate_hybrid_recommendations(self, product_id, limit=None):
        """Generate hybrid recommendations combining content-based and collaborative filtering."""
        if limit is None:
            limit = self.settings['max_recommendations_per_product']
            
        content_weight = self.settings['content_based_weight']
        collab_weight = self.settings['collaborative_weight']
        min_confidence = self.settings['min_recommendation_confidence']
        
        product_idx = self.product_index_map.get(product_id)
        if product_idx is None:
            return []
            
        # Get content-based similarities
        content_similarities = self.content_similarity_matrix[product_idx] if self.content_similarity_matrix is not None else None
        
        # Get collaborative similarities
        collab_similarities = self.collaborative_similarity_matrix[product_idx] if self.collaborative_similarity_matrix is not None else None
        
        # Combine similarities using weighted average
        combined_similarities = np.zeros(len(self.product_index_map))
        
        if content_similarities is not None:
            combined_similarities += content_weight * content_similarities
            
        if collab_similarities is not None:
            combined_similarities += collab_weight * collab_similarities
        
        # Create reverse mapping: index -> product_id
        index_product_map = {idx: pid for pid, idx in self.product_index_map.items()}
        
        # Generate recommendations
        recommendations = []
        for idx, similarity in enumerate(combined_similarities):
            if idx == product_idx or similarity < min_confidence:
                continue
                
            rec_product_id = index_product_map.get(idx)
            if rec_product_id:
                recommendations.append({
                    'id': rec_product_id,
                    'confidence': float(similarity),
                    'reason': self._get_recommendation_reason(similarity, content_similarities[idx] if content_similarities is not None else 0, 
                                                            collab_similarities[idx] if collab_similarities is not None else 0)
                })
        
        # Sort by confidence and limit
        sorted_recs = sorted(recommendations, key=lambda x: x['confidence'], reverse=True)
        return sorted_recs[:limit]
    
    def _get_recommendation_reason(self, combined_score, content_score, collab_score):
        """Determine the primary reason for recommendation."""
        if content_score > collab_score:
            if content_score > 0.8:
                return 'very_similar_product'
            else:
                return 'similar_product'
        else:
            if collab_score > 0.8:
                return 'frequently_bought_together'
            else:
                return 'others_also_liked'
    
    def get_recommendations(self, product_id, limit=None):
        """Get recommendations for a specific product."""
        if limit is None:
            limit = self.settings['max_recommendations_per_product']
            
        # Check if we need to initialize the model
        if not self.recommendations_cache:
            self.build_model()
            
        # Check if we have cached recommendations
        if product_id in self.recommendations_cache:
            return self.recommendations_cache[product_id][:limit]
        
        # If no cached recommendations, generate on-the-fly
        if self.content_similarity_matrix is not None or self.collaborative_similarity_matrix is not None:
            return self._generate_hybrid_recommendations(product_id, limit)
        
        # Fallback to basic recommendations
        return self._generate_fallback_recommendations(product_id, limit)
    
    def _generate_fallback_recommendations(self, product_id, limit):
        """Generate fallback recommendations when models aren't available."""
        try:
            # Get Product model from registry
            Product = self.db.Model.registry._class_registry.get('Product')
            
            if Product is None:
                return []
                
            product = Product.query.get(product_id)
            
            if product:
                # Get products from same brand or category
                similar_products = Product.query.filter(
                    ((Product.brand_id == product.brand_id) | 
                     (Product.category_id == product.category_id)),
                    Product.id != product.id
                ).order_by(Product.views.desc()).limit(limit).all()
                
                result = []
                for similar in similar_products:
                    # Higher confidence for same brand and category
                    confidence = 0.8 if (similar.brand_id == product.brand_id and 
                                         similar.category_id == product.category_id) else 0.6
                    
                    reason = 'same_brand_and_category' if (similar.brand_id == product.brand_id and 
                                                          similar.category_id == product.category_id) else \
                            'same_brand' if similar.brand_id == product.brand_id else 'same_category'
                    
                    result.append({
                        'id': similar.id,
                        'confidence': confidence,
                        'reason': reason
                    })
                
                return sorted(result, key=lambda x: x['confidence'], reverse=True)
        except Exception as e:
            print(f"Error generating fallback recommendations: {str(e)}")
        
        return []
    
    def get_trending_products(self, limit=8):
        """Get trending products based on views and orders."""
        try:
            # Get Product model from registry
            Product = self.db.Model.registry._class_registry.get('Product')
            
            if Product is None:
                return []
                
            # Simply return products with highest view counts
            trending = Product.query.order_by(Product.views.desc()).limit(limit).all()
            
            # Convert to dictionaries with confidence scores
            result = []
            for i, product in enumerate(trending):
                result.append({
                    'id': product.id,
                    'confidence': 0.95 - (i * 0.05),  # Descending confidence
                    'reason': 'trending'
                })
            
            return result
        except Exception as e:
            print(f"Error getting trending products: {str(e)}")
            return []
    
    def get_personalized_recommendations(self, user_id, limit=8):
        """Get personalized recommendations for a user using collaborative filtering."""
        try:
            # Check if we have a user-product matrix
            if self.user_product_matrix is None:
                self.build_model()
                
            if self.user_product_matrix is None:
                return self.get_trending_products(limit)
                
            # Get User and Product models
            User = self.db.Model.registry._class_registry.get('User')
            Product = self.db.Model.registry._class_registry.get('Product')
            
            if User is None or Product is None:
                return self.get_trending_products(limit)
                
            # Find user's index in the matrix
            user = User.query.get(user_id)
            if not user:
                return self.get_trending_products(limit)
                
            # Get all users to find index
            users = User.query.all()
            user_index_map = {u.id: i for i, u in enumerate(users)}
            
            user_idx = user_index_map.get(user_id)
            if user_idx is None:
                return self.get_trending_products(limit)
                
            # Get all products
            products = Product.query.all()
            if not products:
                return self.get_trending_products(limit)
                
            # Calculate predicted ratings for all products for this user
            user_vector = self.user_product_matrix[user_idx]
            predicted_ratings = np.zeros(len(products))
            
            # Skip products the user has already interacted with
            interacted_products = set(i for i, rating in enumerate(user_vector) if rating > 0)
            
            # Simple user-item collaborative filtering:
            # For each product, find similar products the user has interacted with
            for prod_idx in range(len(products)):
                if prod_idx in interacted_products:
                    continue
                    
                if self.collaborative_similarity_matrix is not None:
                    # Get similarities to other products
                    similarities = self.collaborative_similarity_matrix[prod_idx]
                    
                    # Calculate weighted rating
                    weighted_sum = 0
                    similarity_sum = 0
                    
                    for other_idx, similarity in enumerate(similarities):
                        if other_idx in interacted_products and similarity > 0:
                            weighted_sum += similarity * user_vector[other_idx]
                            similarity_sum += similarity
                    
                    if similarity_sum > 0:
                        predicted_ratings[prod_idx] = weighted_sum / similarity_sum
            
            # Create product index to product_id mapping
            index_product_map = {idx: product.id for idx, product in enumerate(products)}
            
            # Sort products by predicted rating
            top_indices = np.argsort(predicted_ratings)[::-1][:limit*2]  # Get more to filter valid ones
            
            # Create recommendations
            result = []
            for idx in top_indices:
                if predicted_ratings[idx] > 0:
                    product_id = index_product_map.get(idx)
                    if product_id:
                        confidence = min(predicted_ratings[idx] / 3.0, 0.95)  # Normalize to 0-0.95
                        result.append({
                            'id': product_id,
                            'confidence': float(confidence),
                            'reason': 'recommended_for_you'
                        })
            
            # If we don't have enough recommendations, add trending products
            if len(result) < limit:
                trending = self.get_trending_products(limit - len(result))
                # Check that trending recommendations aren't already in the list
                existing_ids = {rec['id'] for rec in result}
                for rec in trending:
                    if rec['id'] not in existing_ids:
                        result.append(rec)
            
            return result[:limit]
            
        except Exception as e:
            print(f"Error getting personalized recommendations: {str(e)}")
            return self.get_trending_products(limit)
    
    def get_frequent_recommendations(self, limit=10):
        """Get most frequently recommended products for admin dashboard."""
        # Initialize model if needed
        if not self.recommendations_cache:
            self.build_model()
            
        # Count occurrences of each product in recommendations
        product_counts = defaultdict(int)
        
        for product_id, recs in self.recommendations_cache.items():
            for rec in recs:
                product_counts[rec['id']] += 1
        
        # Sort products by recommendation frequency
        sorted_products = sorted(product_counts.items(), key=lambda x: x[1], reverse=True)
        
        try:
            # Get Product model from registry
            Product = self.db.Model.registry._class_registry.get('Product')
            
            if Product is None:
                return []
                
            result = []
            for product_id, count in sorted_products[:limit]:
                product = Product.query.get(product_id)
                if product:
                    result.append({
                        'product': product,
                        'recommendation_count': count
                    })
            
            return result
        except Exception as e:
            print(f"Error getting frequent recommendations: {str(e)}")
            return [] 