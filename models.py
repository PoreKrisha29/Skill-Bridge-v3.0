"""
Database Models for SkillBridge Application

This module demonstrates multiple OOP concepts:
1. INHERITANCE - All models inherit from db.Model
2. ENCAPSULATION - Private methods and password hashing
3. ABSTRACTION - Clean interfaces for complex operations
4. POLYMORPHISM - Different models with similar methods

DBMS Concepts Demonstrated:
- Primary Keys (id fields)
- Foreign Keys (user_id, service_id, etc.)
- One-to-Many Relationships (User -> Services, Service -> Reviews)
- Many-to-Many Relationships (via association tables)
- Indexes for query optimization
- Constraints (UNIQUE, NOT NULL)

Author: SkillBridge Team
Purpose: Define database schema and model behavior
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy database object
# This will be configured in app.py
db = SQLAlchemy()


class User(UserMixin, db.Model):
    """
    User Model - Represents both service providers and clients
    
    OOP Concepts:
    - INHERITANCE: Inherits from db.Model and UserMixin
    - ENCAPSULATION: Password is hashed and never stored in plain text
    - METHODS: Custom methods for password handling and relationships
    
    DBMS Concepts:
    - Primary Key: id
    - Unique Constraints: username, email
    - One-to-Many: User has many Services
    - One-to-Many: User has many Reviews
    """
    
    # Table name in database
    __tablename__ = 'users'
    
    # Primary Key - Unique identifier for each user
    id = db.Column(db.Integer, primary_key=True)
    
    # User credentials and basic info
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # User type: 'client', 'provider', or 'admin'
    user_type = db.Column(db.String(20), nullable=False, default='client')
    
    # Profile information
    full_name = db.Column(db.String(100))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(255), default='default-avatar.png')
    phone = db.Column(db.String(20))
    
    # Account status
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (One-to-Many)
    # One user can have many services
    services = db.relationship('Service', backref='provider', lazy='dynamic', 
                              foreign_keys='Service.user_id')
    
    # One user can write many reviews
    reviews = db.relationship('Review', backref='reviewer', lazy='dynamic',
                             foreign_keys='Review.user_id')
    
    # One user can have many orders as buyer
    orders_as_buyer = db.relationship('Order', backref='buyer', lazy='dynamic',
                                     foreign_keys='Order.buyer_id')
    
    # One user can have many orders as seller
    orders_as_seller = db.relationship('Order', backref='seller', lazy='dynamic',
                                      foreign_keys='Order.seller_id')
    
    # One user can have many favorites
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic',
                               cascade='all, delete-orphan')

    # One user can have many notifications
    notifications = db.relationship('Notification', backref='user', lazy='dynamic',
                                   cascade='all, delete-orphan')
    
    def set_password(self, password):
        """
        Hash and set user password
        
        OOP Concept: ENCAPSULATION - Password is never stored in plain text
        Security: Uses Werkzeug's generate_password_hash with strong algorithm
        
        Args:
            password (str): Plain text password
        """
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """
        Verify password against stored hash
        
        OOP Concept: ENCAPSULATION - Password checking without exposing hash
        
        Args:
            password (str): Plain text password to check
            
        Returns:
            bool: True if password matches, False otherwise
        """
        return check_password_hash(self.password_hash, password)
    
    def get_services(self):
        """
        Get all services offered by this user
        
        Returns:
            list: List of Service objects
        """
        return self.services.filter_by(is_active=True).all()
    
    def get_average_rating(self):
        """
        Calculate average rating for user's services based on all reviews received
        
        Returns:
            float: Average rating (0.0 to 5.0)
        """
        services = self.get_services()
        if not services:
            return 0.0
        
        total_rating_sum = 0
        total_review_count = 0
        
        for service in services:
            reviews = service.reviews.all()
            for review in reviews:
                total_rating_sum += review.rating
                total_review_count += 1
        
        if total_review_count == 0:
            return 0.0
            
        return round(total_rating_sum / total_review_count, 1)
    
    def get_total_reviews(self):
        """
        Get total number of reviews across all services
        
        Returns:
            int: Total review count
        """
        return sum(service.reviews.count() for service in self.get_services())
    
    def is_admin(self):
        """
        Check if user is an administrator
        
        Returns:
            bool: True if user is admin
        """
        return self.user_type == 'admin'
    
    def get_unread_notifications_count(self):
        """Get count of unread notifications"""
        return self.notifications.filter_by(is_read=False).count()
    
    def get_recent_notifications(self, limit=5):
        """Get recent notifications ordered by date"""
        return self.notifications.order_by(db.text('created_at desc')).limit(limit)

    def get_avatar_url(self):
        """
        Get resolved avatar URL
        
        Returns:
            str: Full URL to avatar image
        """
        from flask import url_for
        
        if not self.avatar_url or self.avatar_url == 'default-avatar.png':
            return f"https://ui-avatars.com/api/?name={self.username}&background=random&color=fff&size=128"
        
        if self.avatar_url.startswith('http'):
            return self.avatar_url
            
        return url_for('static', filename='avatars/' + self.avatar_url)


    def __repr__(self):
        """String representation of User object"""
        return f'<User {self.username}>'


class Category(db.Model):
    """
    Category Model - Represents service categories
    
    OOP Concepts:
    - ENCAPSULATION: Service count is calculated dynamically
    - METHODS: Helper methods for category operations
    
    DBMS Concepts:
    - Primary Key: id
    - Unique Constraint: name
    - One-to-Many: Category has many Services
    """
    
    __tablename__ = 'categories'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Category details
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50))  # Icon class name (e.g., 'bi-code')
    color = db.Column(db.String(50))  # Color class for styling
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    # One category can have many services
    services = db.relationship('Service', backref='category', lazy='dynamic')
    
    def get_service_count(self):
        """
        Get number of active services in this category
        
        OOP Concept: ENCAPSULATION - Calculated property
        
        Returns:
            int: Number of active services
        """
        return self.services.filter_by(is_active=True).count()
    
    def get_top_services(self, limit=4):
        """
        Get top-rated services in this category
        
        Data Structure: Uses Python's sorted() with custom key
        Algorithm: Sort by average rating descending
        
        Args:
            limit (int): Maximum number of services to return
            
        Returns:
            list: Top-rated Service objects
        """
        services = self.services.filter_by(is_active=True).all()
        # Sort by average rating (highest first)
        sorted_services = sorted(services, 
                                key=lambda s: s.get_average_rating(), 
                                reverse=True)
        return sorted_services[:limit]
    
    def __repr__(self):
        """String representation of Category object"""
        return f'<Category {self.name}>'


class Service(db.Model):
    """
    Service Model - Represents services offered by providers
    
    OOP Concepts:
    - INHERITANCE: Inherits from db.Model
    - ENCAPSULATION: Rating calculation is internal
    - ABSTRACTION: Clean interface for service operations
    
    DBMS Concepts:
    - Primary Key: id
    - Foreign Keys: user_id, category_id
    - Many-to-One: Service belongs to User
    - Many-to-One: Service belongs to Category
    - One-to-Many: Service has many Reviews
    """
    
    __tablename__ = 'services'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Service details
    title = db.Column(db.String(200), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    delivery_time = db.Column(db.String(50))  # e.g., "3 days", "1 week"
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False, index=True)
    
    # Relationships
    favorited_by = db.relationship('Favorite', backref='service', lazy='dynamic', cascade='all, delete-orphan')
    
    # Media
    image_url = db.Column(db.String(255), default='default-service.jpg')
    
    # Tags for search (stored as comma-separated string)
    tags = db.Column(db.String(255))
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Statistics
    view_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    # One service can have many reviews
    reviews = db.relationship('Review', backref='service', lazy='dynamic',
                             cascade='all, delete-orphan')
    
    # One service can have many orders
    orders = db.relationship('Order', backref='service', lazy='dynamic')
    
    # One service can be favorited by many users
    favorited_by = db.relationship('Favorite', backref='service', lazy='dynamic',
                                   cascade='all, delete-orphan')
    
    def get_average_rating(self):
        """
        Calculate average rating for this service
        
        Algorithm:
        1. Get all reviews for this service
        2. Calculate sum of ratings
        3. Divide by count
        
        Returns:
            float: Average rating (0.0 to 5.0)
        """
        reviews = self.reviews.all()
        if not reviews:
            return 0.0
        
        total_rating = sum(review.rating for review in reviews)
        return round(total_rating / len(reviews), 1)
    
    def get_review_count(self):
        """
        Get total number of reviews
        
        Returns:
            int: Review count
        """
        return self.reviews.count()
    
    def get_tags_list(self):
        """
        Convert tags string to list
        
        Data Structure: Converts comma-separated string to LIST
        
        Returns:
            list: List of tag strings
        """
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def increment_views(self):
        """
        Increment view count for this service
        
        OOP Concept: ENCAPSULATION - Internal state modification
        Updated to handle potential database locks gracefully
        """
        try:
            self.view_count += 1
            db.session.commit()
        except Exception:
            # If database is locked or error occurs, rollback and continue
            # View count update is not critical enough to crash the application
            db.session.rollback()
    
    def is_favorited_by(self, user):
        """
        Check if service is favorited by given user
        
        Args:
            user (User): User object to check
            
        Returns:
            bool: True if favorited
        """
        if not user or not user.is_authenticated:
            return False
        return self.favorited_by.filter_by(user_id=user.id).first() is not None
    
    def __repr__(self):
        """String representation of Service object"""
        return f'<Service {self.title}>'


class Review(db.Model):
    """
    Review Model - Represents user reviews for services
    
    OOP Concepts:
    - VALIDATION: Rating must be between 1 and 5
    - ENCAPSULATION: Validation logic is internal
    
    DBMS Concepts:
    - Primary Key: id
    - Foreign Keys: service_id, user_id
    - Many-to-One: Review belongs to Service
    - Many-to-One: Review belongs to User
    - Composite Index: (service_id, user_id) for faster lookups
    """
    
    __tablename__ = 'reviews'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Review content
    rating = db.Column(db.Integer, nullable=False)  # 1 to 5
    comment = db.Column(db.Text)
    
    # Foreign Keys
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite index for faster queries
    __table_args__ = (
        db.Index('idx_service_user', 'service_id', 'user_id'),
    )
    
    def validate_rating(self):
        """
        Validate that rating is between 1 and 5
        
        OOP Concept: VALIDATION - Data integrity check
        
        Returns:
            bool: True if valid, False otherwise
        """
        return 1 <= self.rating <= 5
    
    def __repr__(self):
        """String representation of Review object"""
        return f'<Review for Service {self.service_id} by User {self.user_id}>'


class Order(db.Model):
    """
    Order Model - Represents service orders/transactions
    
    OOP Concepts:
    - STATE MANAGEMENT: Order status changes
    - ENCAPSULATION: Status update logic
    
    DBMS Concepts:
    - Primary Key: id
    - Foreign Keys: service_id, buyer_id, seller_id
    - Many-to-One relationships
    - Index on status for filtering
    """
    
    __tablename__ = 'orders'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False, index=True)
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    
    # Order details
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    # Status values: 'pending', 'in_progress', 'completed', 'cancelled'
    
    # Additional details
    requirements = db.Column(db.Text)  # Buyer's requirements
    scope = db.Column(db.Text)  # Detailed scope
    budget_tier = db.Column(db.String(20)) # Basic, Standard, Premium
    deadline = db.Column(db.DateTime)  # Agreed deadline
    delivery_note = db.Column(db.Text)  # Seller's delivery note
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def update_status(self, new_status):
        """
        Update order status with validation
        
        OOP Concept: STATE MANAGEMENT
        
        Args:
            new_status (str): New status value
            
        Returns:
            bool: True if update successful
        """
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if new_status in valid_statuses:
            self.status = new_status
            if new_status == 'completed':
                self.completed_at = datetime.utcnow()
            return True
        return False
    
    def calculate_platform_fee(self, fee_percentage=10):
        """
        Calculate platform fee
        
        Args:
            fee_percentage (float): Platform fee percentage
            
        Returns:
            float: Platform fee amount
        """
        return round(self.total_price * (fee_percentage / 100), 2)
    
    def __repr__(self):
        """String representation of Order object"""
        return f'<Order {self.id} - {self.status}>'


class Favorite(db.Model):
    """
    Favorite Model - Represents user's favorite services
    
    DBMS Concepts:
    - Many-to-Many relationship between Users and Services
    - Composite unique constraint to prevent duplicates
    """
    
    __tablename__ = 'favorites'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'), nullable=False, index=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Ensure a user can't favorite the same service twice
    __table_args__ = (
        db.UniqueConstraint('user_id', 'service_id', name='unique_user_service_favorite'),
    )
    
    def __repr__(self):
        """String representation of Favorite object"""
        return f'<Favorite User {self.user_id} - Service {self.service_id}>'


class Notification(db.Model):
    """
    Notification Model - Represents user notifications
    """
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    link = db.Column(db.String(255))
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Notification {self.title}>'


class Message(db.Model):
    """
    Message Model - Chat messages for orders
    """
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', backref=db.backref('messages', lazy='dynamic'))
    sender = db.relationship('User', backref='sent_messages')


class ProjectShowcase(db.Model):
    """
    Project Showcase Model - Portfolio items for users
    """
    __tablename__ = 'project_showcase'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    link = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('portfolio', lazy='dynamic', cascade='all, delete-orphan'))

    
    def __repr__(self):
        return f'<ProjectShowcase {self.title}>'


class Contract(db.Model):
    """
    Contract Model - Legal-grade contracts for orders
    
    OOP Concepts:
    - ENCAPSULATION: Contract generation logic
    - STATE MANAGEMENT: Signature status tracking
    
    DBMS Concepts:
    - Primary Key: id
    - Foreign Key: order_id
    - One-to-One: Contract belongs to Order
    - Unique constraint on order_id (one contract per order)
    """
    
    __tablename__ = 'contracts'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key - One-to-One with Order
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, unique=True, index=True)
    
    # Contract Details
    contract_type = db.Column(db.String(50), nullable=False)  # 'web_development', 'graphic_design', etc.
    contract_number = db.Column(db.String(50), unique=True, nullable=False, index=True)  # e.g., SB-2026-001
    
    # Contract Content
    service_description = db.Column(db.Text, nullable=False)
    deliverables = db.Column(db.Text, nullable=False)  # JSON or text list
    timeline = db.Column(db.String(100), nullable=False)
    payment_amount = db.Column(db.Float, nullable=False)
    payment_terms = db.Column(db.Text, nullable=False)
    revision_policy = db.Column(db.Text, nullable=False)
    ip_ownership = db.Column(db.Text, nullable=False)  # Who owns the intellectual property
    
    # Additional Terms
    additional_terms = db.Column(db.Text)  # Custom clauses
    cancellation_policy = db.Column(db.Text, nullable=False)
    
    # Signature Status
    provider_signed = db.Column(db.Boolean, default=False)
    provider_signed_at = db.Column(db.DateTime)
    provider_signature = db.Column(db.Text)  # Digital signature (hash)
    provider_ip = db.Column(db.String(50))  # IP address for verification
    
    client_signed = db.Column(db.Boolean, default=False)
    client_signed_at = db.Column(db.DateTime)
    client_signature = db.Column(db.Text)  # Digital signature (hash)
    client_ip = db.Column(db.String(50))  # IP address for verification
    
    # Contract Status
    status = db.Column(db.String(20), default='draft', index=True)
    # Status values: 'draft', 'pending_signatures', 'active', 'completed', 'terminated'
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    activated_at = db.Column(db.DateTime)  # When both parties signed
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    order = db.relationship('Order', backref=db.backref('contract', uselist=False))
    
    def generate_contract_number(self):
        """
        Generate unique contract number
        Format: SB-YYYY-XXXX (SkillBridge-Year-Number)
        
        OOP Concept: ENCAPSULATION
        """
        from datetime import datetime
        year = datetime.utcnow().year
        
        # Count contracts created this year
        count = Contract.query.filter(
            db.extract('year', Contract.created_at) == year
        ).count() + 1
        
        return f"SB-{year}-{count:04d}"
    
    def is_fully_signed(self):
        """
        Check if both parties have signed
        
        Returns:
            bool: True if both signed
        """
        return self.provider_signed and self.client_signed
    
    def sign_as_provider(self, user_id, ip_address):
        """
        Provider signs the contract
        
        Args:
            user_id (int): Provider user ID
            ip_address (str): IP address of signer
        
        Returns:
            bool: True if signature successful
        """
        if self.order.seller_id != user_id:
            return False
        
        self.provider_signed = True
        self.provider_signed_at = datetime.utcnow()
        self.provider_signature = self._generate_signature_hash(user_id, 'provider')
        self.provider_ip = ip_address
        
        # Check if contract is now fully signed
        if self.is_fully_signed():
            self.status = 'active'
            self.activated_at = datetime.utcnow()
        else:
            self.status = 'pending_signatures'
        
        return True
    
    def sign_as_client(self, user_id, ip_address):
        """
        Client signs the contract
        
        Args:
            user_id (int): Client user ID
            ip_address (str): IP address of signer
        
        Returns:
            bool: True if signature successful
        """
        if self.order.buyer_id != user_id:
            return False
        
        self.client_signed = True
        self.client_signed_at = datetime.utcnow()
        self.client_signature = self._generate_signature_hash(user_id, 'client')
        self.client_ip = ip_address
        
        # Check if contract is now fully signed
        if self.is_fully_signed():
            self.status = 'active'
            self.activated_at = datetime.utcnow()
        else:
            self.status = 'pending_signatures'
        
        return True
    
    def _generate_signature_hash(self, user_id, role):
        """
        Generate cryptographic signature hash
        
        OOP Concept: ENCAPSULATION - Private method
        
        Args:
            user_id (int): User ID
            role (str): 'provider' or 'client'
        
        Returns:
            str: Signature hash
        """
        import hashlib
        from datetime import datetime
        
        # Combine contract details with timestamp and user
        signature_data = f"{self.contract_number}:{user_id}:{role}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(signature_data.encode()).hexdigest()
    
    def get_status_display(self):
        """
        Get human-readable status
        
        Returns:
            str: Status display text
        """
        status_map = {
            'draft': 'Draft',
            'pending_signatures': 'Pending Signatures',
            'active': 'Active',
            'completed': 'Completed',
            'terminated': 'Terminated'
        }
        return status_map.get(self.status, 'Unknown')
    
    def get_signature_progress(self):
        """
        Get signature completion percentage
        
        Returns:
            int: Percentage (0, 50, or 100)
        """
        if self.provider_signed and self.client_signed:
            return 100
        elif self.provider_signed or self.client_signed:
            return 50
        return 0
    
    def __repr__(self):
        """String representation of Contract object"""
        return f'<Contract {self.contract_number}>'


class WebsiteReview(db.Model):
    """
    Website Review Model - User reviews and suggestions about the website
    
    DBMS Concepts:
    - Primary Key: id
    - Foreign Key: user_id (optional, can be anonymous)
    - Timestamps for ordering
    """
    
    __tablename__ = 'website_reviews'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Review content
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    suggestion = db.Column(db.Text, nullable=False)
    rating = db.Column(db.Integer, default=5)  # 1-5 rating
    
    # Foreign Key (optional - can be anonymous)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    
    # Status
    is_approved = db.Column(db.Boolean, default=True)  # Auto-approve for now
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        """String representation of WebsiteReview object"""
        return f'<WebsiteReview by {self.name}>'


class Community(db.Model):
    """
    Community Model - Represents skill-based communities
    
    DBMS Concepts:
    - Primary Key: id
    - One-to-Many: Community has many members
    - Timestamps for ordering
    """
    
    __tablename__ = 'communities'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Community details
    name = db.Column(db.String(100), nullable=False, unique=True, index=True)
    description = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(255))
    category = db.Column(db.String(50))  # e.g., 'Web Development', 'Design', etc.
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    members = db.relationship('CommunityMember', backref='community', lazy='dynamic', 
                             cascade='all, delete-orphan')
    
    def get_members_count(self):
        """Get total number of members in this community"""
        return self.members.count()
    
    def is_member(self, user_id):
        """Check if user is a member of this community"""
        return self.members.filter_by(user_id=user_id).first() is not None
    
    def __repr__(self):
        return f'<Community {self.name}>'


class CommunityMember(db.Model):
    """
    CommunityMember Model - Represents membership in communities
    
    DBMS Concepts:
    - Many-to-Many relationship between Users and Communities
    - Composite unique constraint to prevent duplicate memberships
    """
    
    __tablename__ = 'community_members'
    
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Keys
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    community_id = db.Column(db.Integer, db.ForeignKey('communities.id'), nullable=False, index=True)
    
    # Membership details
    role = db.Column(db.String(20), default='member')  # 'member', 'moderator', 'admin'
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('community_memberships', lazy='dynamic'))
    
    # Ensure a user can't join the same community twice
    __table_args__ = (
        db.UniqueConstraint('user_id', 'community_id', name='unique_user_community'),
    )
    
    def __repr__(self):
        return f'<CommunityMember User {self.user_id} - Community {self.community_id}>'