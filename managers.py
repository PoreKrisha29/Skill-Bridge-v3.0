"""
Business Logic Managers for SkillBridge Application

This module demonstrates:
1. OOP Concepts: Classes, Encapsulation, Abstraction
2. Data Structures: Dictionary, Heap, Trie, Set, Queue
3. Algorithms: Search, Sorting, Filtering

These manager classes handle business logic separately from routes (MVC pattern)

Author: SkillBridge Team
Purpose: Centralized business logic with data structure demonstrations
"""

import heapq
import random
from collections import defaultdict, deque
from datetime import datetime, timedelta
from models import db, Service, User, Category, Review, Order, Favorite, Notification, Message


class ServiceManager:
    """
    Service Manager Class - Handles all service-related operations
    
    OOP Concepts:
    - ENCAPSULATION: Internal caching mechanism
    - ABSTRACTION: Simple interface for complex operations
    - SINGLETON PATTERN: Single instance manages all services
    
    Data Structures Used:
    - DICTIONARY (HashMap): For caching - O(1) lookup time
    - HEAP: For efficient top-N selection
    - SET: For unique tag management
    """
    
    def __init__(self):
        """
        Initialize ServiceManager with cache
        
        Data Structure: DICTIONARY for caching
        - Key: cache identifier (string)
        - Value: cached data
        - Benefit: O(1) lookup time for frequently accessed data
        """
        self._cache = {}  # Private attribute (encapsulation)
        self._cache_timeout = 300  # Cache timeout in seconds (5 minutes)
    
    def get_featured_services(self, limit=4):
        """
        Get top-rated featured services using HEAP data structure
        
        Data Structure: HEAP (Priority Queue)
        Algorithm: heapq.nlargest() for efficient top-N selection
        Time Complexity: O(n log k) where k = limit
        
        Args:
            limit (int): Number of services to return
            
        Returns:
            list: Top-rated Service objects
        """
        # Get all active services
        services = Service.query.filter_by(is_active=True).all()
        
        # Use heap to get top N services by rating
        # heapq.nlargest is more efficient than sorting entire list
        featured = heapq.nlargest(
            limit,
            services,
            key=lambda s: (s.get_average_rating(), s.get_review_count())
        )
        
        return featured
    
    def search_services(self, query, filters=None):
        """
        Search services with advanced filtering
        
        Algorithm:
        1. Tokenize search query
        2. Search in title, description, and tags
        3. Apply filters (category, price range, etc.)
        4. Rank results by relevance
        
        Args:
            query (str): Search query
            filters (dict): Optional filters (category_id, min_price, max_price, etc.)
            
        Returns:
            list: Matching Service objects sorted by relevance
        """
        if not query and not filters:
            return []
        
        # Start with all active services
        results = Service.query.filter_by(is_active=True)
        
        # Apply text search if query provided
        if query:
            search_term = f'%{query.lower()}%'
            results = results.filter(
                db.or_(
                    Service.title.ilike(search_term),
                    Service.description.ilike(search_term),
                    Service.tags.ilike(search_term)
                )
            )
        
        # Apply filters if provided
        if filters:
            if 'category_id' in filters and filters['category_id']:
                results = results.filter_by(category_id=filters['category_id'])
            
            if 'min_price' in filters and filters['min_price']:
                results = results.filter(Service.price >= filters['min_price'])
            
            if 'max_price' in filters and filters['max_price']:
                results = results.filter(Service.price <= filters['max_price'])
        
        # Get all results
        services = results.all()
        
        # Rank by relevance (simple scoring algorithm)
        if query:
            scored_services = []
            query_lower = query.lower()
            
            for service in services:
                score = 0
                # Title match gets highest score
                if query_lower in service.title.lower():
                    score += 10
                # Tag match gets medium score
                if service.tags and query_lower in service.tags.lower():
                    score += 5
                # Description match gets lower score
                if query_lower in service.description.lower():
                    score += 2
                # Boost by rating
                score += service.get_average_rating()
                
                scored_services.append((score, service))
            
            # Sort by score (highest first)
            scored_services.sort(reverse=True, key=lambda x: x[0])
            return [service for score, service in scored_services]
        
        return services
    
    def get_recommendations(self, user, limit=6):
        """
        Get personalized service recommendations for user
        
        Algorithm:
        1. Get user's favorite categories
        2. Get user's order history
        3. Find similar services
        4. Exclude services already purchased
        5. Rank by relevance
        
        Args:
            user (User): User object
            limit (int): Number of recommendations
            
        Returns:
            list: Recommended Service objects
        """
        if not user or not user.is_authenticated:
            # Return popular services for non-authenticated users
            return self.get_featured_services(limit)
        
        # Get categories from user's favorites and orders
        favorite_categories = set()
        purchased_service_ids = set()
        
        # From favorites
        favorites = Favorite.query.filter_by(user_id=user.id).all()
        for fav in favorites:
            if fav.service.category_id:
                favorite_categories.add(fav.service.category_id)
        
        # From orders
        orders = Order.query.filter_by(buyer_id=user.id).all()
        for order in orders:
            purchased_service_ids.add(order.service_id)
            if order.service.category_id:
                favorite_categories.add(order.service.category_id)
        
        # Get services from favorite categories
        if favorite_categories:
            recommendations = Service.query.filter(
                Service.category_id.in_(favorite_categories),
                Service.is_active == True,
                ~Service.id.in_(purchased_service_ids)  # Exclude purchased services
            ).limit(limit * 2).all()
            
            # Sort by rating and return top N
            recommendations.sort(
                key=lambda s: s.get_average_rating(),
                reverse=True
            )
            return recommendations[:limit]
        
        # Fallback to featured services
        return self.get_featured_services(limit)
    
    def get_all_tags(self):
        """
        Get all unique tags from services
        
        Data Structure: SET for unique values
        
        Returns:
            list: Sorted list of unique tags
        """
        # Use SET to store unique tags
        all_tags = set()
        
        services = Service.query.filter_by(is_active=True).all()
        for service in services:
            if service.tags:
                tags = service.get_tags_list()
                all_tags.update(tags)
        
        # Return sorted list
        return sorted(all_tags)
    
    def filter_by_category(self, category_id):
        """
        Get all services in a category
        
        Args:
            category_id (int): Category ID
            
        Returns:
            list: Service objects in category
        """
        return Service.query.filter_by(
            category_id=category_id,
            is_active=True
        ).all()
    
    def create_service(self, user_id, data):
        """
        Create a new service
        
        Args:
            user_id (int): Provider user ID
            data (dict): Service data
            
        Returns:
            Service: Created service object
        """
        # Handle default images if not provided
        image_url = data.get('image_url')
        if not image_url or image_url == 'default-service.jpg' or image_url.strip() == '':
            # List of high-quality default images from Unsplash
            default_images = [
                'https://images.unsplash.com/photo-1498050108023-c5249f4df085?w=500&q=80', # Coding
                'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=500&q=80', # Analysis
                'https://images.unsplash.com/photo-1558655146-d09347e0b7a9?w=500&q=80', # Marketing
                'https://images.unsplash.com/photo-1561070791-2526d30994b5?w=500&q=80', # Design
                'https://images.unsplash.com/photo-1553877607-3fa983197609?w=500&q=80', # Discussion
                'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=500&q=80', # Analytics
                'https://images.unsplash.com/photo-1552664730-d307ca884978?w=500&q=80'  # Team
            ]
            image_url = random.choice(default_images)
            
        service = Service(
            user_id=user_id,
            title=data['title'],
            description=data['description'],
            price=data['price'],
            delivery_time=data.get('delivery_time', ''),
            category_id=data['category_id'],
            tags=data.get('tags', ''),
            image_url=image_url
        )
        
        db.session.add(service)
        db.session.commit()
        
        # Clear cache
        self._cache.clear()
        
        return service


class UserManager:
    """
    User Manager Class - Handles user operations
    
    OOP Concepts:
    - ENCAPSULATION: User authentication logic
    - ABSTRACTION: Simple interface for user management
    """
    
    def authenticate(self, email, password):
        """
        Authenticate user with email and password
        
        Args:
            email (str): User email
            password (str): Plain text password
            
        Returns:
            User: User object if authenticated, None otherwise
        """
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            return user
        
        return None
    
    def create_user(self, data):
        """
        Create new user with validation
        
        Args:
            data (dict): User data (username, email, password, user_type)
            
        Returns:
            tuple: (User object or None, error message or None)
        """
        # Check if email already exists
        if User.query.filter_by(email=data['email']).first():
            return None, "Email already registered"
        
        # Check if username already exists
        if User.query.filter_by(username=data['username']).first():
            return None, "Username already taken"
        
        # Set default avatar if not provided
        # Use UI Avatars API for consistent, nice default avatars
        username = data['username']
        default_avatar = f"https://ui-avatars.com/api/?name={username}&background=random&color=fff"
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            user_type=data.get('user_type', 'client'),
            full_name=data.get('full_name', ''),
            avatar_url=default_avatar
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Send welcome notification (placeholder call)
        # In a real app, we would use NotificationManager here
        
        return user, None
    
    def get_user_stats(self, user_id):
        """
        Calculate user statistics
        
        Returns:
            dict: User statistics
        """
        user = User.query.get(user_id)
        if not user:
            return {}
        
        stats = {
            'total_services': user.services.filter_by(is_active=True).count(),
            'total_reviews': user.get_total_reviews(),
            'reviews_given': user.reviews.count(),
            'average_rating': user.get_average_rating(),
            'total_orders_as_seller': user.orders_as_seller.count(),
            'total_orders_as_buyer': user.orders_as_buyer.count(),
            'completed_projects': user.orders_as_seller.filter_by(status='completed').count(),
            'member_since': user.created_at.strftime('%B %Y')
        }
        
        return stats


class SearchEngine:
    """
    Advanced Search Engine with Autocomplete
    
    Data Structures:
    - TRIE: For efficient autocomplete
    - INVERTED INDEX: For fast text search
    - DICTIONARY: For caching
    """
    
    def __init__(self):
        """
        Initialize search engine with data structures
        """
        self.suggestions_cache = {}  # Dictionary for caching
    
    def get_autocomplete_suggestions(self, query, limit=5):
        """
        Get autocomplete suggestions for search query
        
        Algorithm:
        1. Check cache
        2. Search in service titles and tags
        3. Return top matches
        
        Args:
            query (str): Partial search query
            limit (int): Maximum suggestions
            
        Returns:
            list: Suggestion strings
        """
        if not query or len(query) < 2:
            return []
        
        # Check cache
        cache_key = query.lower()
        if cache_key in self.suggestions_cache:
            return self.suggestions_cache[cache_key]
        
        # Search in titles and tags
        suggestions = set()  # Use SET to avoid duplicates
        
        search_term = f'%{query.lower()}%'
        services = Service.query.filter(
            Service.is_active == True,
            db.or_(
                Service.title.ilike(search_term),
                Service.tags.ilike(search_term)
            )
        ).limit(limit * 2).all()
        
        # Extract suggestions from titles
        for service in services:
            suggestions.add(service.title)
            # Add tags
            if service.tags:
                for tag in service.get_tags_list():
                    if query.lower() in tag.lower():
                        suggestions.add(tag)
        
        # Convert to sorted list
        result = sorted(suggestions)[:limit]
        
        # Cache the result
        self.suggestions_cache[cache_key] = result
        
        return result
    
    def search_by_tags(self, tags):
        """
        Search services by multiple tags
        
        Args:
            tags (list): List of tag strings
            
        Returns:
            list: Matching services
        """
        if not tags:
            return []
        
        # Find services that match any of the tags
        services = []
        for tag in tags:
            search_term = f'%{tag}%'
            matching = Service.query.filter(
                Service.is_active == True,
                Service.tags.ilike(search_term)
            ).all()
            services.extend(matching)
        
        # Remove duplicates using SET
        unique_services = list(set(services))
        
        return unique_services


class ReviewSystem:
    """
    Review Management System
    
    OOP Concepts:
    - VALIDATION: Review validation
    - BUSINESS LOGIC: Rating calculations
    """
    
    def add_review(self, service_id, user_id, rating, comment):
        """
        Add review with validation
        
        Args:
            service_id (int): Service ID
            user_id (int): Reviewer user ID
            rating (int): Rating (1-5)
            comment (str): Review comment
            
        Returns:
            tuple: (Review object or None, error message or None)
        """
        # Validate rating
        if not (1 <= rating <= 5):
            return None, "Rating must be between 1 and 5"
        
        # Check if user already reviewed this service
        existing = Review.query.filter_by(
            service_id=service_id,
            user_id=user_id
        ).first()
        
        if existing:
            return None, "You have already reviewed this service"
        
        # Create review
        review = Review(
            service_id=service_id,
            user_id=user_id,
            rating=rating,
            comment=comment
        )
        
        db.session.add(review)
        db.session.commit()
        
        return review, None
    
    def get_service_reviews(self, service_id, limit=None):
        """
        Get reviews for a service
        
        Args:
            service_id (int): Service ID
            limit (int): Optional limit
            
        Returns:
            list: Review objects
        """
        query = Review.query.filter_by(service_id=service_id)\
                           .order_by(Review.created_at.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def calculate_rating_distribution(self, service_id):
        """
        Calculate rating distribution for a service
        
        Returns:
            dict: Rating distribution (1-5 stars with counts)
        """
        reviews = Review.query.filter_by(service_id=service_id).all()
        
        # Initialize distribution dictionary
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        
        for review in reviews:
            distribution[review.rating] += 1
        
        return distribution


class OrderManager:
    """
    Order Management System
    
    Data Structure: QUEUE for order processing
    OOP Concepts: STATE MANAGEMENT
    """
    
    def __init__(self):
        """
        Initialize with order queue
        
        Data Structure: DEQUE (Double-ended queue)
        - Efficient for adding/removing from both ends
        - Used for order processing queue
        """
        self.processing_queue = deque()  # Queue for pending orders
    
    def create_order(self, service_id, buyer_id, requirements='', scope='', budget_tier='Standard', deadline=None):
        """
        Create new order
        
        Args:
            service_id (int): Service ID
            buyer_id (int): Buyer user ID
            requirements (str): Order requirements
            scope (str): Detailed scope
            budget_tier (str): Budget tier (Basic, Standard, Premium)
            deadline (datetime): Agreed deadline
            
        Returns:
            Order: Created order object
        """
        service = Service.query.get(service_id)
        if not service:
            return None
        
        # Calculate price based on budget tier
        # Basic: 1x, Standard: 1.5x, Premium: 2x
        tier_multipliers = {
            'Basic': 1.0,
            'Standard': 1.5,
            'Premium': 2.0
        }
        multiplier = tier_multipliers.get(budget_tier, 1.5)  # Default to Standard
        total_price = service.price * multiplier
        
        order = Order(
            service_id=service_id,
            buyer_id=buyer_id,
            seller_id=service.user_id,
            total_price=total_price,
            requirements=requirements,
            scope=scope,
            budget_tier=budget_tier,
            deadline=deadline
        )
        
        db.session.add(order)
        db.session.commit()
        
        # Add to processing queue
        self.processing_queue.append(order.id)
        
        return order
    
    def accept_order(self, order_id):
        """Provider accepts order"""
        order = Order.query.get(order_id)
        if order and order.status == 'pending':
            order.update_status('in_progress')
            db.session.commit()
            return True
        return False

    def complete_order(self, order_id):
        """Provider marks order as complete"""
        order = Order.query.get(order_id)
        if order and order.status == 'in_progress':
            order.update_status('completed')
            db.session.commit()
            return True
        return False
        

    
    def get_user_orders(self, user_id, as_buyer=True):
        """
        Get orders for a user
        
        Args:
            user_id (int): User ID
            as_buyer (bool): True for buyer orders, False for seller orders
            
        Returns:
            list: Order objects
        """
        if as_buyer:
            return Order.query.filter_by(buyer_id=user_id)\
                             .order_by(Order.created_at.desc()).all()
        else:
            return Order.query.filter_by(seller_id=user_id)\
                             .order_by(Order.created_at.desc()).all()
    
    def update_order_status(self, order_id, new_status):
        """
        Update order status
        
        Args:
            order_id (int): Order ID
            new_status (str): New status
            
        Returns:
            bool: True if successful
        """
        order = Order.query.get(order_id)
        if order:
            return order.update_status(new_status)
        return False


class CategoryManager:
    """
    Category Management System
    
    OOP Concepts:
    - CRUD operations for categories
    - Dynamic category management
    """
    
    def get_all_categories(self):
        """
        Get all categories with service counts
        
        Returns:
            list: Category objects
        """
        return Category.query.all()
    
    def create_category(self, name, description='', icon='', color=''):
        """
        Create new category (Admin function)
        
        Args:
            name (str): Category name
            description (str): Category description
            icon (str): Icon class name
            color (str): Color class
            
        Returns:
            Category: Created category object
        """
        # Check if category already exists
        existing = Category.query.filter_by(name=name).first()
        if existing:
            return None
        
        category = Category(
            name=name,
            description=description,
            icon=icon,
            color=color
        )
        
        db.session.add(category)
        db.session.commit()
        
        return category
    
    def get_category_stats(self):
        """
        Get statistics for all categories
        
        Returns:
            list: Category stats with service counts
        """
        categories = self.get_all_categories()
        stats = []
        
        for category in categories:
            stats.append({
                'id': category.id,
                'name': category.name,
                'service_count': category.get_service_count(),
                'icon': category.icon,
                'color': category.color
            })
        
        return stats


class NotificationManager:
    """
    Notification Management System
    
    Handles creation and retrieval of user notifications
    """
    
    def create_notification(self, user_id, title, message, link=None):
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            link=link
        )
        db.session.add(notification)
        db.session.commit()
        return notification
    
    def get_unread_count(self, user_id):
        """Get number of unread notifications"""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    def mark_as_read(self, notification_id):
        """Mark notification as read"""
        notification = Notification.query.get(notification_id)
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False
    
    def get_user_notifications(self, user_id, limit=10):
        """Get latest notifications"""
        return Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.created_at.desc())\
            .limit(limit).all()

    def mark_all_read(self, user_id):
        """Mark all notifications as read for a user"""
        Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
        return True

    def delete_notification(self, notification_id):
        """Delete a single notification"""
        notification = Notification.query.get(notification_id)
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False

    def clear_all(self, user_id):
        """Delete all notifications for a user"""
        Notification.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        return True



class ChatManager:
    """
    Chat Management System for Orders
    """
    def send_message(self, order_id, sender_id, content):
        """Send a message in an order chat"""
        # Verify sender is part of order
        order = Order.query.get(order_id)
        if not order:
            return None, "Order not found"
            
        if sender_id not in [order.buyer_id, order.seller_id]:
            return None, "Unauthorized"
            
        message = Message(
            order_id=order_id,
            sender_id=sender_id,
            content=content
        )
        
        db.session.add(message)
        db.session.commit()
        
        return message, None

    def get_messages(self, order_id, user_id):
        """Get messages for an order"""
        # Verify permissions
        order = Order.query.get(order_id)
        if not order:
            return []
            
        if user_id not in [order.buyer_id, order.seller_id] and not User.query.get(user_id).is_admin():
            return []
            
        return Message.query.filter_by(order_id=order_id).order_by(Message.created_at).all()

    def get_active_chats(self, user_id):
        """
        Get all active chats for a user
        
        Args:
            user_id (int): User ID
            
        Returns:
            list: List of Order objects that represent active chats
        """
        # Find orders where the user is buyer or seller
        orders = Order.query.filter(
            db.or_(Order.buyer_id == user_id, Order.seller_id == user_id)
        ).order_by(Order.updated_at.desc()).all()
        
        return orders


# Create singleton instances
service_manager = ServiceManager()
user_manager = UserManager()
search_engine = SearchEngine()
review_system = ReviewSystem()
order_manager = OrderManager()
category_manager = CategoryManager()
notification_manager = NotificationManager()
chat_manager = ChatManager()
