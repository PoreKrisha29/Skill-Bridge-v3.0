"""
Flask Routes (Controllers) for SkillBridge Application

This module contains all route handlers organized into blueprints.
Demonstrates MVC Pattern: Routes act as Controllers

Blueprints:
- main_bp: Main pages (home, about, etc.)
- auth_bp: Authentication (login, register, logout)
- service_bp: Service operations (create, view, edit, delete)
- user_bp: User profile and dashboard
- admin_bp: Admin panel
- api_bp: JSON API endpoints

Author: SkillBridge Team
Purpose: Handle HTTP requests and responses
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from datetime import datetime
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from models import db, User, Service, Category, Review, Order, Favorite, Notification, Message, ProjectShowcase
from managers import (service_manager, user_manager, search_engine, 
                     review_system, order_manager, category_manager, notification_manager, chat_manager)
from werkzeug.utils import secure_filename
import os
from flask import current_app

def save_uploaded_file(file_storage, folder='images'):
    """
    Save uploaded file to static folder
    """
    if not file_storage:
        return None
        
    filename = secure_filename(file_storage.filename)
    if not filename:
        return None
        
    # Generate unique filename to prevent overwrites
    import uuid
    name, ext = os.path.splitext(filename)
    unique_filename = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    
    # Ensure directory exists
    upload_path = os.path.join(current_app.root_path, 'static', folder)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save file
    file_storage.save(os.path.join(upload_path, unique_filename))
    return unique_filename

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)
service_bp = Blueprint('service', __name__)
user_bp = Blueprint('user', __name__)
admin_bp = Blueprint('admin', __name__)
api_bp = Blueprint('api', __name__)


# ============================================================================
# DECORATORS
# ============================================================================

def admin_required(f):
    """
    Decorator to require admin privileges
    
    OOP Concept: DECORATOR PATTERN
    - Wraps route functions to add authentication check
    - Reusable across multiple routes
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


def provider_required(f):
    """
    Decorator to require provider account
    
    Args:
        f: Function to wrap
        
    Returns:
        Wrapped function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'info')
            return redirect(url_for('auth.login'))
        if current_user.user_type not in ['provider', 'admin']:
            flash('You need a provider account to access this page.', 'warning')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# MAIN ROUTES
# ============================================================================

@main_bp.route('/')
def index():
    """
    Landing page route
    
    Displays:
    - Hero section
    - Categories
    - Featured services
    - How it works
    - Testimonials
    - CTA
    
    Returns:
        Rendered template
    """
    # Get featured services using ServiceManager
    featured_services = service_manager.get_featured_services(limit=4)
    
    # Get all categories
    categories = category_manager.get_all_categories()
    
    # Get category stats
    category_stats = category_manager.get_category_stats()
    
    # Get communities for homepage (limit to 4)
    from models import Community
    communities = Community.query.filter_by(is_active=True).limit(4).all()
    for community in communities:
        community.members_count = community.get_members_count()
    
    # Get stats for home page
    # Get stats for home page
    # Calculate satisfaction rate from Website Reviews
    from models import WebsiteReview
    website_reviews = WebsiteReview.query.filter_by(is_approved=True).all()
    satisfaction_rate = 100  # Default to 100% if no reviews
    if website_reviews:
        total_rating = sum(review.rating for review in website_reviews)
        satisfaction_rate = int((total_rating / len(website_reviews)) / 5 * 100)

    stats_data = {
        'total_users': User.query.count(),
        'total_services': Service.query.filter_by(is_active=True).count(),
        'total_reviews': Review.query.count(),
        'satisfaction_rate': satisfaction_rate
    }
    
    return render_template('index.html',
                         featured_services=featured_services,
                         categories=categories,
                         category_stats=category_stats,
                         communities=communities,
                         stats_data=stats_data)



@main_bp.route('/about')
def about():
    """About page"""
    # Get stats for about page
    # Calculate average rating from website reviews (user feedback about SkillBridge)
    from models import WebsiteReview
    website_reviews = WebsiteReview.query.filter_by(is_approved=True).all()
    if website_reviews:
        total_rating = sum(review.rating for review in website_reviews)
        average_rating = round(total_rating / len(website_reviews), 1)
    else:
        average_rating = 0.0
    
    stats_data = {
        'total_users': User.query.count(),
        'total_services': Service.query.filter_by(is_active=True).count(),
        'total_reviews': WebsiteReview.query.filter_by(is_approved=True).count(),
        'average_rating': average_rating
    }
    return render_template('about.html', stats_data=stats_data)


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    """Contact page"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # In a real app, you might save this to a ContactMessage model
        # For now, we'll notify the admin using NotificationManager
        
        # specific admin user or general admin notification
        # Assuming admin has id 1 or we find the first admin
        admin = User.query.filter_by(user_type='admin').first()
        if admin:
            notification_manager.create_notification(
                user_id=admin.id,
                title=f'New Contact: {subject}',
                message=f'From: {name} ({email})\n\n{message}',
                link='#' # or link to a dedicated admin message view
            )
            
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
        
    return render_template('contact.html')


@main_bp.route('/terms')
def terms():
    """Terms of Service page"""
    return render_template('terms.html')


@main_bp.route('/privacy')
def privacy():
    """Privacy Policy page"""
    return render_template('privacy.html')


@main_bp.route('/reviews', methods=['GET', 'POST'])
def reviews():
    """Website reviews and suggestions page"""
    from models import WebsiteReview, db
    from flask import request, flash, redirect, url_for
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        suggestion = request.form.get('suggestion')
        rating = int(request.form.get('rating', 5))
        
        if not name or not suggestion:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('main.reviews'))
        
        # Create review
        review = WebsiteReview(
            name=name,
            email=email,
            suggestion=suggestion,
            rating=rating,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Thank you for your feedback! Your suggestion has been submitted.', 'success')
        return redirect(url_for('main.reviews'))
    
    # Get all approved reviews, newest first
    all_reviews = WebsiteReview.query.filter_by(is_approved=True)\
        .order_by(WebsiteReview.created_at.desc()).all()
    
    return render_template('reviews.html', reviews=all_reviews)


@main_bp.route('/communities')
def communities():
    """Communities listing page"""
    from models import Community
    all_communities = Community.query.filter_by(is_active=True).all()
    
    # Add member count and membership status for each community
    for community in all_communities:
        community.members_count = community.get_members_count()
        if current_user.is_authenticated:
            community.is_joined = community.is_member(current_user.id)
        else:
            community.is_joined = False
    
    return render_template('communities.html', communities=all_communities)


@main_bp.route('/community/<int:community_id>')
def community_detail(community_id):
    """Individual community page"""
    from models import Community
    community = Community.query.get_or_404(community_id)
    
    # Get community members
    members = community.members.order_by(db.text('joined_at desc')).limit(20).all()
    members_count = community.get_members_count()
    
    # Check if current user is a member
    is_member = False
    if current_user.is_authenticated:
        is_member = community.is_member(current_user.id)
    
    return render_template('community_detail.html', 
                         community=community,
                         members=members,
                         members_count=members_count,
                         is_member=is_member)


@main_bp.route('/community/<int:community_id>/join', methods=['POST'])
@login_required
def join_community(community_id):
    """Join a community"""
    from models import Community, CommunityMember
    
    community = Community.query.get_or_404(community_id)
    
    # Check if already a member
    if community.is_member(current_user.id):
        flash('You are already a member of this community.', 'info')
        return redirect(url_for('main.community_detail', community_id=community_id))
    
    # Create membership
    membership = CommunityMember(
        user_id=current_user.id,
        community_id=community_id
    )
    db.session.add(membership)
    db.session.commit()
    
    flash(f'Successfully joined {community.name}!', 'success')
    return redirect(url_for('main.community_detail', community_id=community_id))


@main_bp.route('/community/<int:community_id>/leave', methods=['POST'])
@login_required
def leave_community(community_id):
    """Leave a community"""
    from models import Community, CommunityMember
    
    community = Community.query.get_or_404(community_id)
    
    # Find membership
    membership = CommunityMember.query.filter_by(
        user_id=current_user.id,
        community_id=community_id
    ).first()
    
    if not membership:
        flash('You are not a member of this community.', 'warning')
        return redirect(url_for('main.community_detail', community_id=community_id))
    
    # Remove membership
    db.session.delete(membership)
    db.session.commit()
    
    flash(f'You have left {community.name}.', 'info')
    return redirect(url_for('main.communities'))


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    User login route
    
    GET: Display login form
    POST: Process login credentials
    
    Returns:
        Rendered template or redirect
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        # Authenticate user using UserManager
        user = user_manager.authenticate(email, password)
        
        if user:
            # Check if account is active
            if not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Log in user
            login_user(user, remember=remember)
            flash(f'Welcome back, {user.full_name or user.username}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            # Redirect based on user type
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            elif user.user_type == 'provider':
                return redirect(url_for('user.dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Invalid email or password. Please try again.', 'danger')
    
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    User registration route
    
    GET: Display registration form
    POST: Create new user account
    
    Returns:
        Rendered template or redirect
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        # Get form data
        data = {
            'username': request.form.get('username'),
            'email': request.form.get('email'),
            'password': request.form.get('password'),
            'user_type': request.form.get('user_type', 'client'),
            'full_name': request.form.get('full_name', '')
        }
        
        # Validate password confirmation
        password_confirm = request.form.get('password_confirm')
        if data['password'] != password_confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')
        
        # Create user using UserManager
        user, error = user_manager.create_user(data)
        
        if user:
            # Send welcome email
            from email_utils import send_welcome_email
            send_welcome_email(user)
            
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(error, 'danger')
    
    return render_template('auth/register.html')



@auth_bp.route('/login/google')
def google_login():
    """Initiate Google OAuth login"""
    from extensions import oauth
    redirect_uri = url_for('auth.google_callback', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/google/callback')
def google_callback():
    """Handle Google OAuth callback"""
    from extensions import oauth
    from werkzeug.security import generate_password_hash
    import os
    
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.parse_id_token(token, nonce=None)
        
        # Check if user exists
        user = User.query.filter_by(email=user_info['email']).first()
        
        if not user:
            # Create new user
            username = user_info['email'].split('@')[0]
            # Ensure unique username
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User(
                username=username,
                email=user_info['email'],
                full_name=user_info.get('name', username),
                user_type='client',  # Default to client
                password_hash=generate_password_hash(os.urandom(24).hex()),
                is_active=True,
                is_verified=True  # Google verified
            )
            db.session.add(user)
            db.session.commit()
            
            # Send welcome email
            from email_utils import send_welcome_email
            send_welcome_email(user)
            
            flash('Account created successfully via Google!', 'success')
        
        # Refresh user from database to ensure proper session
        db.session.refresh(user)
        
        # Log in user
        login_user(user, remember=True)
        flash(f'Welcome back, {user.full_name or user.username}!', 'success')
        return redirect(url_for('user.dashboard'))
        
    except Exception as e:
        flash(f'Google login failed: {str(e)}', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/logout')
@login_required
def logout():
    """
    User logout route
    
    Returns:
        Redirect to home page
    """
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('main.index'))


# ============================================================================
# SERVICE ROUTES
# ============================================================================

@service_bp.route('/browse')
def browse():
    """
    Browse all services with filters
    
    Query Parameters:
    - q: Search query
    - category: Category ID
    - min_price: Minimum price
    - max_price: Maximum price
    - sort: Sort option (price_asc, price_desc, rating, newest)
    
    Returns:
        Rendered template with services
    """
    # Get query parameters
    query = request.args.get('q', '')
    category_id = request.args.get('category', type=int)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'rating')
    
    # Auto-detect category from search query if not explicitly set
    # If query matches a category name, use category filter instead of text search
    if query and not category_id:
        # Try to match query with category name
        matching_category = Category.query.filter(
            Category.name.ilike(f'%{query.strip()}%')
        ).first()
        
        if matching_category:
            category_id = matching_category.id
            # Clear the query so we only filter by category, not search text
            query = ''
    
    # Build filters dictionary
    filters = {}
    if category_id:
        filters['category_id'] = category_id
    if min_price:
        filters['min_price'] = min_price
    if max_price:
        filters['max_price'] = max_price
    
    # Search services
    if query or filters:
        services = service_manager.search_services(query, filters)
    else:
        # Get all services
        services = Service.query.filter_by(is_active=True).all()
    
    # Sort services
    if sort_by == 'price_asc':
        services.sort(key=lambda s: s.price)
    elif sort_by == 'price_desc':
        services.sort(key=lambda s: s.price, reverse=True)
    elif sort_by == 'rating':
        services.sort(key=lambda s: s.get_average_rating(), reverse=True)
    elif sort_by == 'newest':
        services.sort(key=lambda s: s.created_at, reverse=True)
    
    # Get categories for filter
    categories = category_manager.get_all_categories()
    
    return render_template('services.html',
                         services=services,
                         categories=categories,
                         query=query,
                         selected_category=category_id,
                         min_price=min_price,
                         max_price=max_price,
                         sort_by=sort_by)



@service_bp.route('/<int:service_id>')
def detail(service_id):
    """
    Service detail page
    
    Args:
        service_id: Service ID
        
    Returns:
        Rendered template with service details
    """
    service = Service.query.get_or_404(service_id)
    
    # Increment view count
    service.increment_views()
    
    # Get reviews
    reviews = review_system.get_service_reviews(service_id, limit=10)
    
    # Get rating distribution
    rating_dist = review_system.calculate_rating_distribution(service_id)
    
    # Get related services (same category)
    related_services = Service.query.filter(
        Service.category_id == service.category_id,
        Service.id != service_id,
        Service.is_active == True
    ).limit(4).all()
    
    # Check if user has favorited this service
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = service.is_favorited_by(current_user)
    
    return render_template('service_detail.html',
                         service=service,
                         reviews=reviews,
                         rating_dist=rating_dist,
                         related_services=related_services,
                         is_favorited=is_favorited)


@service_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """
    Create new service (All logged-in users except admins)
    
    Automatically converts user to 'provider' type when creating first service
    
    GET: Display service creation form
    POST: Create service
    
    Returns:
        Rendered template or redirect
    """
    # Prevent admins from creating services
    if current_user.is_admin():
        flash('Administrators cannot create or sell services.', 'danger')
        return redirect(url_for('service.browse'))
    
    if request.method == 'POST':
        # Automatically convert user to provider if they're a client
        if current_user.user_type == 'client':
            current_user.user_type = 'provider'
            db.session.commit()
            flash('Welcome to SkillBridge as a service provider!', 'success')
        
        # Get form data
        data = {
            'title': request.form.get('title'),
            'description': request.form.get('description'),
            'price': float(request.form.get('price', 0)),
            'delivery_time': request.form.get('delivery_time'),
            'category_id': int(request.form.get('category_id')),
            'category_id': int(request.form.get('category_id')),
            'tags': request.form.get('tags', '')
        }
        
        # Handle Image Upload (REQUIRED)
        image_uploaded = False
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = save_uploaded_file(file)
                if filename:
                    data['image_url'] = filename
                    image_uploaded = True
        
        # Validate that image was uploaded
        if not image_uploaded:
            flash('Service image is required! Please upload an image for your service.', 'danger')
            categories = category_manager.get_all_categories()
            return render_template('service_create.html', categories=categories)
        
        # Create service using ServiceManager
        service = service_manager.create_service(current_user.id, data)
        
        if service:
            flash('Service created successfully!', 'success')
            return redirect(url_for('service.detail', service_id=service.id))
        else:
            flash('Error creating service. Please try again.', 'danger')
    
    # Get categories for form
    categories = category_manager.get_all_categories()
    
    return render_template('service_create.html', categories=categories)


@service_bp.route('/<int:service_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(service_id):
    """
    Edit service (Owner only)
    
    Args:
        service_id: Service ID
        
    Returns:
        Rendered template or redirect
    """
    service = Service.query.get_or_404(service_id)
    
    # Check ownership - only the owner can edit (not even admins)
    if service.user_id != current_user.id:
        flash('You do not have permission to edit this service.', 'danger')
        return redirect(url_for('service.detail', service_id=service_id))
    
    if request.method == 'POST':
        # Update service
        service.title = request.form.get('title')
        service.description = request.form.get('description')
        service.price = float(request.form.get('price', 0))
        service.delivery_time = request.form.get('delivery_time')
        service.category_id = int(request.form.get('category_id'))
        service.tags = request.form.get('tags', '')
        
        # Handle Image Upload
        if 'image' in request.files:
            file = request.files['image']
            if file and file.filename != '':
                filename = save_uploaded_file(file)
                if filename:
                    service.image_url = filename
        
        db.session.commit()
        flash('Service updated successfully!', 'success')
        return redirect(url_for('service.detail', service_id=service_id))
    
    categories = category_manager.get_all_categories()
    return render_template('service_edit.html', service=service, categories=categories)


@service_bp.route('/<int:service_id>/delete', methods=['POST'])
@login_required
def delete(service_id):
    """
    Delete service (Owner or Admin only)
    
    For Admin: Permanently deletes the service from database (including related records)
    For Owner: Soft delete (sets is_active to False)
    
    Args:
        service_id: Service ID
        
    Returns:
        Redirect
    """
    service = Service.query.get_or_404(service_id)
    
    # Check ownership
    if service.user_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to delete this service.', 'danger')
        return redirect(url_for('service.detail', service_id=service_id))
    
    # Admin: Permanent delete from database
    if current_user.is_admin():
        service_title = service.title
        
        try:
            # Delete related orders and their messages first
            orders = Order.query.filter_by(service_id=service_id).all()
            for order in orders:
                # Delete messages associated with this order
                Message.query.filter_by(order_id=order.id).delete()
                db.session.delete(order)
            
            # Delete related reviews
            Review.query.filter_by(service_id=service_id).delete()
            
            # Delete related favorites
            Favorite.query.filter_by(service_id=service_id).delete()
            
            # Now delete the service
            db.session.delete(service)
            db.session.commit()
            
            flash(f'Service "{service_title}" and all related data permanently deleted.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting service: {str(e)}', 'danger')
        
        return redirect(url_for('admin.services'))
    else:
        # Regular user: Soft delete (set is_active to False)
        service.is_active = False
        db.session.commit()
        flash('Service deleted successfully.', 'success')
        return redirect(url_for('user.dashboard'))


@service_bp.route('/<int:service_id>/review', methods=['POST'])
@login_required
def add_review(service_id):
    """
    Add review to service
    
    Args:
        service_id: Service ID
        
    Returns:
        Redirect
    """
    rating = int(request.form.get('rating', 0))
    comment = request.form.get('comment', '')
    
    # Add review using ReviewSystem
    review, error = review_system.add_review(service_id, current_user.id, rating, comment)
    
    if review:
        flash('Review submitted successfully!', 'success')
    else:
        flash(error, 'danger')
    
    return redirect(url_for('service.detail', service_id=service_id))


@service_bp.route('/<int:service_id>/favorite', methods=['POST'])
@login_required
def toggle_favorite(service_id):
    """
    Toggle favorite status for service
    
    Args:
        service_id: Service ID
        
    Returns:
        JSON response
    """
    service = Service.query.get_or_404(service_id)
    
    # Check if already favorited
    favorite = Favorite.query.filter_by(
        user_id=current_user.id,
        service_id=service_id
    ).first()
    
    if favorite:
        # Remove from favorites
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'removed', 'message': 'Removed from favorites'})
    else:
        # Add to favorites
        favorite = Favorite(user_id=current_user.id, service_id=service_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'added', 'message': 'Added to favorites'})


@service_bp.route('/<int:service_id>/order', methods=['POST'])
@login_required
def place_order(service_id):
    """
    Place order for service (clients and providers only, not admins)
    
    Args:
        service_id: Service ID
        
    Returns:
        Redirect
    """
    # Prevent admins from purchasing services
    if current_user.is_admin():
        flash('Administrators cannot purchase services.', 'danger')
        return redirect(url_for('service.detail', service_id=service_id))
    
    requirements = request.form.get('requirements', '')
    scope = request.form.get('scope', '')
    budget_tier = request.form.get('budget_tier', 'Standard')
    deadline_str = request.form.get('deadline')
    
    deadline = None
    if deadline_str:
        try:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%d')
        except:
            pass
    
    # Create order using OrderManager
    order = order_manager.create_order(service_id, current_user.id, requirements, scope, budget_tier, deadline)
    
    if order:
        # Create notification for the provider
        notification_manager.create_notification(
            user_id=order.seller_id,
            title='New Order Received',
            message=f'You have a new order for {order.service.title} from {current_user.username}',
            link=url_for('user.orders')
        )
        
        # Send emails to both customer and provider
        from email_utils import send_order_placed_emails
        send_order_placed_emails(order)
        
        flash('Order placed successfully! The provider will contact you soon.', 'success')
        return redirect(url_for('user.orders'))
    else:
        flash('Error placing order. Please try again.', 'danger')
        return redirect(url_for('service.detail', service_id=service_id))


# ============================================================================
# USER ROUTES
# ============================================================================

@user_bp.route('/dashboard')
@login_required
def dashboard():
    """
    User dashboard
    
    Shows different content based on user type:
    - Provider: Services, orders, earnings
    - Client: Orders, favorites
    - Admin: Redirect to admin panel
    
    Returns:
        Rendered template
    """
    if current_user.is_admin():
        return redirect(url_for('admin.dashboard'))
    
    # Get user stats
    stats = user_manager.get_user_stats(current_user.id)
    
    if current_user.user_type == 'provider':
        # Provider dashboard
        services = current_user.get_services()
        orders = order_manager.get_user_orders(current_user.id, as_buyer=False)
        
        return render_template('user/provider_dashboard.html',
                             stats=stats,
                             services=services,
                             orders=orders)
    else:
        # Client dashboard
        orders = order_manager.get_user_orders(current_user.id, as_buyer=True)
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        recommendations = service_manager.get_recommendations(current_user, limit=6)
        
        return render_template('user/client_dashboard.html',
                             stats=stats,
                             orders=orders,
                             favorites=favorites,
                             recommendations=recommendations)


@user_bp.route('/notifications/mark-read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    notification_manager.mark_as_read(notification_id)
    return jsonify({'status': 'success'})


@user_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    notification_manager.mark_all_read(current_user.id)
    return jsonify({'status': 'success'})


@user_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
def delete_notification(notification_id):
    """Delete a notification"""
    notification_manager.delete_notification(notification_id)
    return jsonify({'status': 'success'})


@user_bp.route('/notifications/clear-all', methods=['POST'])
@login_required
def clear_all_notifications():
    """Clear all notifications"""
    notification_manager.clear_all(current_user.id)
    return jsonify({'status': 'success'})



@user_bp.route('/chats')
@login_required
def chats():
    """User chats page"""
    active_chats = chat_manager.get_active_chats(current_user.id)
    return render_template('user/chats.html', chats=active_chats)


@user_bp.route('/contact_provider/<int:service_id>')
@login_required
def contact_provider(service_id):
    """
    Redirect to chat with provider for a specific service
    """
    service = Service.query.get_or_404(service_id)
    
    # 1. Check for existing order for this specific service
    order = Order.query.filter_by(
        buyer_id=current_user.id,
        service_id=service_id
    ).order_by(Order.created_at.desc()).first()
    
    if order:
        return redirect(url_for('user.order_detail', order_id=order.id))
        
    # 2. Check for any active order with this provider
    # This allows continuing conversation even if for a different service
    provider_orders = Order.query.filter(
        Order.buyer_id == current_user.id,
        Order.seller_id == service.user_id
    ).order_by(Order.created_at.desc()).first()
    
    if provider_orders:
        return redirect(url_for('user.order_detail', order_id=provider_orders.id))

    # 3. If no chat capability exists (no orders), inform user
    # In this system, chat is tied to orders
    flash('You need to place an order to start a chat with this provider.', 'info')
    return redirect(url_for('service.detail', service_id=service_id))



@user_bp.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    """Order detail with chat"""
    order = Order.query.get_or_404(order_id)
    
    # Check permission
    if current_user.id not in [order.buyer_id, order.seller_id] and not current_user.is_admin():
        flash('Unauthorized access', 'danger')
        return redirect(url_for('user.dashboard'))
        
    messages = chat_manager.get_messages(order_id, current_user.id)
    return render_template('user/order_detail.html', order=order, messages=messages)

@user_bp.route('/order/<int:order_id>/action/<action>', methods=['POST'])
@login_required
def order_action(order_id, action):
    """Handle order actions (accept/complete)"""
    order = Order.query.get_or_404(order_id)
    
    if current_user.id != order.seller_id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('user.order_detail', order_id=order_id))
        
    if action == 'accept':
        if order_manager.accept_order(order_id):
            flash('Order accepted! You can now chat with the client.', 'success')
            notification_manager.create_notification(order.buyer_id, f"Order #{order.id} Accepted", f"Your order for {order.service.title} has been accepted.", url_for('user.order_detail', order_id=order.id))
            
            # Send acceptance emails
            from email_utils import send_order_accepted_emails
            send_order_accepted_emails(order)

    elif action == 'reject':
        if order.status == 'pending':
            order.status = 'cancelled'
            db.session.commit()
            
            flash('Order rejected.', 'info')
            notification_manager.create_notification(order.buyer_id, f"Order #{order.id} Rejected", f"Your order for {order.service.title} has been rejected. The amount of ₹{order.total_price} has been refunded.", url_for('user.order_detail', order_id=order.id))
            
        else:
            flash('Cannot reject order in current status.', 'warning')
            
    elif action == 'complete':
        if order_manager.complete_order(order_id):
            flash('Order marked as complete!', 'success')
            notification_manager.create_notification(order.buyer_id, f"Order #{order.id} Completed", f"Your order for {order.service.title} is ready!", url_for('user.order_detail', order_id=order.id))
            
            # Send completion emails
            from email_utils import send_order_completed_emails
            send_order_completed_emails(order)
            
    return redirect(url_for('user.order_detail', order_id=order_id))

@user_bp.route('/order/<int:order_id>/message', methods=['POST'])
@login_required
def send_message(order_id):
    """Send chat message"""
    content = request.form.get('content')
    if content:
        msg, error = chat_manager.send_message(order_id, current_user.id, content)
        if error:
            flash(error, 'danger')
        else:
            # Notify receiver
            order = Order.query.get(order_id)
            receiver_id = order.buyer_id if current_user.id == order.seller_id else order.seller_id
            notification_manager.create_notification(receiver_id, "New Message", f"New message from {current_user.username}", url_for('user.order_detail', order_id=order_id))
            
    return redirect(url_for('user.order_detail', order_id=order_id))


@user_bp.route('/profile/<username>')
def profile(username):
    """
    Public user profile
    
    Args:
        username: Username
        
    Returns:
        Rendered template
    """
    user = User.query.filter_by(username=username).first_or_404()
    
    # Get user's services
    services = user.get_services()
    
    # Get user stats
    stats = user_manager.get_user_stats(user.id)
    
    return render_template('user/profile.html',
                         user=user,
                         services=services,
                         stats=stats)


@user_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    User settings page
    
    GET: Display settings form
    POST: Update user settings
    
    Returns:
        Rendered template or redirect
    """
    if request.method == 'POST':
        # Update profile
        current_user.full_name = request.form.get('full_name', '')
        current_user.bio = request.form.get('bio', '')
        current_user.phone = request.form.get('phone', '')
        
        # Handle Avatar Upload
        if 'avatar' in request.files:
            file = request.files['avatar']
            if file and file.filename != '':
                filename = save_uploaded_file(file, folder='avatars')
                # Update user avatar field (assuming model has avatar_url or similar)
                # Checking models.py next, but applying common pattern
                if filename:
                    current_user.avatar_url = filename
        
        # Update password if provided
        new_password = request.form.get('new_password')
        if new_password:
            current_password = request.form.get('current_password')
            if current_user.check_password(current_password):
                current_user.set_password(new_password)
                flash('Password updated successfully!', 'success')
            else:
                flash('Current password is incorrect.', 'danger')
                return render_template('user/settings.html')
        
        db.session.commit()
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('user.settings'))
    
    return render_template('user/settings.html')


@user_bp.route('/portfolio/add', methods=['POST'])
@login_required
def add_portfolio():
    """Add a portfolio project"""
    title = request.form.get('title')
    description = request.form.get('description')
    link = request.form.get('link')
    
    image_url = None
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            image_url = save_uploaded_file(file, folder='portfolio')
            
    if not title:
        flash('Project title is required', 'danger')
        return redirect(url_for('user.settings'))
    
    project = ProjectShowcase(
        user_id=current_user.id,
        title=title,
        description=description,
        image_url=image_url,
        link=link
    )
    
    db.session.add(project)
    db.session.commit()
    
    flash('Project added to your portfolio!', 'success')
    return redirect(url_for('user.settings'))


@user_bp.route('/portfolio/delete/<int:project_id>', methods=['POST'])
@login_required
def delete_portfolio(project_id):
    """Delete a portfolio project"""
    project = ProjectShowcase.query.get_or_404(project_id)
    
    if project.user_id != current_user.id:
        flash('Unauthorized', 'danger')
        return redirect(url_for('user.settings'))
    
    db.session.delete(project)
    db.session.commit()
    
    flash('Project removed from portfolio', 'success')
    return redirect(url_for('user.settings'))



@user_bp.route('/orders')
@login_required
def orders():
    """
    User orders page
    
    Returns:
        Rendered template
    """
    # Get orders as buyer and seller
    orders_as_buyer = order_manager.get_user_orders(current_user.id, as_buyer=True)
    orders_as_seller = order_manager.get_user_orders(current_user.id, as_buyer=False)
    
    return render_template('user/orders.html',
                         orders_as_buyer=orders_as_buyer,
                         orders_as_seller=orders_as_seller)


# ============================================================================
# CONTRACT ROUTES  
# ============================================================================

@user_bp.route('/order/<int:order_id>/contract')
@login_required
def view_contract(order_id):
    """
    View contract for an order
    
    Args:
        order_id: Order ID
        
    Returns:
        Rendered contract template
    """
    order = Order.query.get_or_404(order_id)
    
    # Check if user is part of this order
    if order.buyer_id != current_user.id and order.seller_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to view this contract.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Get or create contract
    contract = Contract.query.filter_by(order_id=order_id).first()
    
    if not contract:
        # Generate contract automatically
        contract = generate_contract_for_order(order)
        if not contract:
            flash('Error generating contract. Please contact support.', 'danger')
            return redirect(url_for('user.orders'))
    
    # Determine user role
    user_role = 'provider' if current_user.id == order.seller_id else 'client'
    can_sign = (user_role == 'provider' and not contract.provider_signed) or \
               (user_role == 'client' and not contract.client_signed)
    
    return render_template('user/contract.html',
                         contract=contract,
                         order=order,
                         user_role=user_role,
                         can_sign=can_sign)


@user_bp.route('/order/<int:order_id>/contract/generate', methods=['POST'])
@login_required
def generate_contract(order_id):
    """
    Generate contract for an order
    
    Args:
        order_id: Order ID
        
    Returns:
        Redirect to contract view
    """
    order = Order.query.get_or_404(order_id)
    
    # Check permissions
    if order.seller_id != current_user.id and not current_user.is_admin():
        flash('Only the service provider can generate the contract.', 'danger')
        return redirect(url_for('user.orders'))
    
    # Check if contract already exists
    if order.contract:
        flash('Contract already exists for this order.', 'info')
        return redirect(url_for('user.view_contract', order_id=order_id))
    
    # Generate contract
    contract = generate_contract_for_order(order)
    
    if contract:
        # Notify client
        notification_manager.create_notification(
            user_id=order.buyer_id,
            title='Contract Ready for Signature',
            message=f'Contract for {order.service.title} is ready for your review and signature.',
            link=url_for('user.view_contract', order_id=order_id)
        )
        
        flash('Contract generated successfully! Please review and sign.', 'success')
        return redirect(url_for('user.view_contract', order_id=order_id))
    else:
        flash('Error generating contract. Please try again.', 'danger')
        return redirect(url_for('user.orders'))


@user_bp.route('/contract/<int:contract_id>/sign', methods=['POST'])
@login_required  
def sign_contract(contract_id):
    """
    Sign a contract
    
    Args:
        contract_id: Contract ID
        
    Returns:
        Redirect to contract view
    """
    contract = Contract.query.get_or_404(contract_id)
    order = contract.order
    
    # Check permissions
    if order.buyer_id != current_user.id and order.seller_id != current_user.id:
        flash('You do not have permission to sign this contract.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Get user's IP address
    ip_address = request.remote_addr
    
    # Sign based on role
    success = False
    if current_user.id == order.seller_id:
        success = contract.sign_as_provider(current_user.id, ip_address)
        role = 'provider'
    elif current_user.id == order.buyer_id:
        success = contract.sign_as_client(current_user.id, ip_address)
        role = 'client'
    
    if success:
        db.session.commit()
        
        # Notify other party
        if role == 'provider':
            notification_manager.create_notification(
                user_id=order.buyer_id,
                title='Provider Signed Contract',
                message=f'The provider has signed the contract for {order.service.title}. Please review and sign.',
                link=url_for('user.view_contract', order_id=order.id)
            )
        else:
            notification_manager.create_notification(
                user_id=order.seller_id,
                title='Client Signed Contract',
                message=f'The client has signed the contract for {order.service.title}.',
                link=url_for('user.view_contract', order_id=order.id)
            )
        
        # If both signed, update order status
        if contract.is_fully_signed():
            if order.status == 'pending':
                order.status = 'in_progress'
                db.session.commit()
            
            flash('Contract signed successfully! Work can now begin.', 'success')
        else:
            flash('Contract signed successfully! Waiting for other party to sign.', 'success')
    else:
        flash('Error signing contract. You may have already signed or lack permission.', 'danger')
    
    return redirect(url_for('user.view_contract', order_id=order.id))


@user_bp.route('/contract/<int:contract_id>/download')
@login_required
def download_contract(contract_id):
    """
    Download contract as PDF
    
    Args:
        contract_id: Contract ID
        
    Returns:
        PDF file download
    """
    contract = Contract.query.get_or_404(contract_id)
    order = contract.order
    
    # Check permissions
    if order.buyer_id != current_user.id and order.seller_id != current_user.id and not current_user.is_admin():
        flash('You do not have permission to download this contract.', 'danger')
        return redirect(url_for('user.dashboard'))
    
    # Generate PDF
    try:
        from flask import make_response
        from reportlab.lib.pagesizes import letter
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from io import BytesIO
        
        # Create PDF in memory
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=72, leftMargin=72,
                              topMargin=72, bottomMargin=18)
        
        # Container for the 'Flowable' objects
        elements = []
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=30,
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12,
            spaceBefore=12,
        )
        
        # Add content
        elements.append(Paragraph('SERVICE CONTRACT', title_style))
        elements.append(Paragraph(f'Contract No: {contract.contract_number}', styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Contract parties
        elements.append(Paragraph('PARTIES TO THIS AGREEMENT', heading_style))
        elements.append(Paragraph(f'<b>Provider:</b> {order.seller.full_name or order.seller.username} ({order.seller.email})', styles['Normal']))
        elements.append(Paragraph(f'<b>Client:</b> {order.buyer.full_name or order.buyer.username} ({order.buyer.email})', styles['Normal']))
        elements.append(Spacer(1, 20))
        
        # Service description
        elements.append(Paragraph('SERVICE DESCRIPTION', heading_style))
        elements.append(Paragraph(contract.service_description.replace('\n', '<br/>'), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Deliverables
        elements.append(Paragraph('DELIVERABLES', heading_style))
        elements.append(Paragraph(contract.deliverables.replace('\n', '<br/>'), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Timeline
        elements.append(Paragraph('TIMELINE', heading_style))
        elements.append(Paragraph(f'<b>Delivery Time:</b> {contract.timeline}', styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Payment
        elements.append(Paragraph('PAYMENT TERMS', heading_style))
        elements.append(Paragraph(contract.payment_terms.replace('\n', '<br/>'), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Revision Policy
        elements.append(Paragraph('REVISION POLICY', heading_style))
        elements.append(Paragraph(contract.revision_policy.replace('\n', '<br/>'), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # IP Ownership
        elements.append(Paragraph('INTELLECTUAL PROPERTY', heading_style))
        elements.append(Paragraph(contract.ip_ownership.replace('\n', '<br/>'), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Cancellation
        elements.append(Paragraph('CANCELLATION POLICY', heading_style))
        elements.append(Paragraph(contract.cancellation_policy.replace('\n', '<br/>'), styles['Normal']))
        elements.append(Spacer(1, 12))
        
        # Additional Terms
        if contract.additional_terms:
            elements.append(Paragraph('ADDITIONAL TERMS', heading_style))
            elements.append(Paragraph(contract.additional_terms.replace('\n', '<br/>'), styles['Normal']))
            elements.append(Spacer(1, 20))
        
        # Signatures
        elements.append(Paragraph('SIGNATURES', heading_style))
        
        # Signature table
        sig_data = [
            ['Party', 'Signed', 'Date', 'IP Address'],
            ['Provider', 
             '✓' if contract.provider_signed else '✗',
             contract.provider_signed_at.strftime('%Y-%m-%d %H:%M') if contract.provider_signed_at else 'Not signed',
             contract.provider_ip or 'N/A'],
            ['Client', 
             '✓' if contract.client_signed else '✗',
             contract.client_signed_at.strftime('%Y-%m-%d %H:%M') if contract.client_signed_at else 'Not signed',
             contract.client_ip or 'N/A']
        ]
        
        sig_table = Table(sig_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 2*inch])
        sig_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(sig_table)
        elements.append(Spacer(1, 20))
        
        # Footer
        elements.append(Paragraph(
            f'<i>This contract was generated electronically via SkillBridge on {contract.created_at.strftime("%B %d, %Y")} and is legally binding upon digital signature by both parties.</i>',
            styles['Normal']
        ))
        
        # Build PDF
        doc.build(elements)
        
        # Prepare response
        buffer.seek(0)
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=Contract_{contract.contract_number}.pdf'
        
        return response
        
    except ImportError:
        flash('PDF generation requires reportlab library. Please install it.', 'warning')
        return redirect(url_for('user.view_contract', order_id=order.id))
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'danger')
        return redirect(url_for('user.view_contract', order_id=order.id))


def generate_contract_for_order(order):
    """
    Helper function to generate contract for an order
    
    Args:
        order: Order object
        
    Returns:
        Contract object or None
    """
    try:
        service = order.service
        provider = order.seller
        client = order.buyer
        
        # Generate contract content using template generator
        contract_data = ContractTemplateGenerator.generate_contract(
            order, service, provider, client
        )
        
        # Create contract
        contract = Contract(
            order_id=order.id,
            contract_type=contract_data['contract_type'],
            service_description=contract_data['service_description'],
            deliverables=contract_data['deliverables'],
            timeline=contract_data['timeline'],
            payment_amount=contract_data['payment_amount'],
            payment_terms=contract_data['payment_terms'],
            revision_policy=contract_data['revision_policy'],
            ip_ownership=contract_data['ip_ownership'],
            cancellation_policy=contract_data['cancellation_policy'],
            additional_terms=contract_data.get('additional_terms', ''),
            status='draft'
        )
        
        # Generate contract number
        contract.contract_number = contract.generate_contract_number()
        
        # Save to database
        db.session.add(contract)
        db.session.commit()
        
        return contract
    except Exception as e:
        print(f"Error generating contract: {e}")
        db.session.rollback()
        return None


# ============================================================================
# ADMIN ROUTES
# ============================================================================

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """
    Admin dashboard
    
    Shows:
    - Total users, services, orders
    - Recent activity
    - Statistics
    
    Returns:
        Rendered template
    """
    # Get statistics
    total_users = User.query.count()
    total_services = Service.query.filter_by(is_active=True).count()
    total_orders = Order.query.count()
    total_reviews = Review.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Get recent services
    recent_services = Service.query.order_by(Service.created_at.desc()).limit(10).all()
    
    # Get recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    stats = {
        'total_users': total_users,
        'total_services': total_services,
        'total_orders': total_orders,
        'total_reviews': total_reviews
    }
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users,
                         recent_services=recent_services,
                         recent_orders=recent_orders)


@admin_bp.route('/users')
@admin_required
def users():
    """
    Manage users
    
    Returns:
        Rendered template
    """
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    """
    Toggle user active status
    
    Args:
        user_id: User ID
        
    Returns:
        Redirect
    """
    user = User.query.get_or_404(user_id)
    
    # Prevent admin from deactivating themselves
    if user.id == current_user.id:
        flash('You cannot deactivate your own account!', 'danger')
        return redirect(url_for('admin.users'))
    
    # Prevent deactivating other admin accounts
    if user.is_admin():
        flash('Admin accounts cannot be deactivated!', 'danger')
        return redirect(url_for('admin.users'))
    
    user.is_active = not user.is_active
    db.session.commit()
    
    status = 'activated' if user.is_active else 'deactivated'
    flash(f'User {user.username} has been {status}.', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/services')
@admin_required
def services():
    """
    Manage services
    
    Returns:
        Rendered template
    """
    services = Service.query.order_by(Service.created_at.desc()).all()
    return render_template('admin/services.html', services=services)


@admin_bp.route('/services/\u003cint:service_id\u003e/toggle-status', methods=['POST'])
@admin_required
def toggle_service_status(service_id):
    """
    Toggle service active status
    
    Args:
        service_id: Service ID
        
    Returns:
        Redirect
    """
    service = Service.query.get_or_404(service_id)
    
    service.is_active = not service.is_active
    db.session.commit()
    
    status = 'activated' if service.is_active else 'deactivated'
    flash(f'Service "{service.title}" has been {status}.', 'success')
    return redirect(url_for('admin.services'))


@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    """
    Manage categories
    
    GET: Display categories
    POST: Create new category
    
    Returns:
        Rendered template or redirect
    """
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description', '')
        icon = request.form.get('icon', '')
        color = request.form.get('color', '')
        
        category = category_manager.create_category(name, description, icon, color)
        
        if category:
            flash('Category created successfully!', 'success')
        else:
            flash('Category already exists.', 'danger')
        
        return redirect(url_for('admin.categories'))
    
    categories = category_manager.get_all_categories()
    return render_template('admin/categories.html', categories=categories)


@admin_bp.route('/orders')
@admin_required
def orders():
    """
    Manage orders
    
    Returns:
        Rendered template
    """
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)


# ============================================================================
# API ROUTES (JSON)
# ============================================================================

@api_bp.route('/search/autocomplete')
def search_autocomplete():
    """
    Autocomplete API for search
    
    Query Parameters:
    - q: Search query
    
    Returns:
        JSON: List of suggestions
    """
    query = request.args.get('q', '')
    suggestions = search_engine.get_autocomplete_suggestions(query, limit=5)
    
    return jsonify({'suggestions': suggestions})


@api_bp.route('/categories')
def get_categories():
    """
    Get all categories
    
    Returns:
        JSON: List of categories with stats
    """
    category_stats = category_manager.get_category_stats()
    return jsonify({'categories': category_stats})


@api_bp.route('/services/featured')
def get_featured_services():
    """
    Get featured services
    
    Returns:
        JSON: List of featured services
    """
    limit = request.args.get('limit', 4, type=int)
    services = service_manager.get_featured_services(limit)
    
    services_data = [{
        'id': s.id,
        'title': s.title,
        'price': s.price,
        'rating': s.get_average_rating(),
        'provider': s.provider.username,
        'image_url': s.image_url
    } for s in services]
    
    return jsonify({'services': services_data})


@api_bp.route('/services/<int:service_id>/stats')
def get_service_stats(service_id):
    """
    Get service statistics
    
    Args:
        service_id: Service ID
        
    Returns:
        JSON: Service stats
    """
    service = Service.query.get_or_404(service_id)
    
    stats = {
        'views': service.view_count,
        'rating': service.get_average_rating(),
        'reviews': service.get_review_count(),
        'favorites': service.favorited_by.count()
    }
    
    return jsonify(stats)


@api_bp.route('/notifications')
@login_required
def get_notifications():
    """
    Get user notifications for real-time polling
    
    Returns:
        JSON: List of notifications with unread count
    """
    import pytz
    from datetime import datetime
    
    notifications = current_user.get_recent_notifications(10)
    unread_count = current_user.get_unread_notifications_count()
    
    # Convert to IST for display
    ist_tz = pytz.timezone('Asia/Kolkata')
    
    notifications_data = []
    for n in notifications:
        # Convert created_at to IST
        created_at = n.created_at
        if created_at.tzinfo is None:
            utc_tz = pytz.UTC
            created_at = utc_tz.localize(created_at)
        ist_time = created_at.astimezone(ist_tz)
        
        notifications_data.append({
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'link': n.link or '#',
            'is_read': n.is_read,
            'time': ist_time.strftime('%I:%M %p')
        })
    
    return jsonify({
        'notifications': notifications_data,
        'unread_count': unread_count
    })

