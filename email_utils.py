"""
Email Utility Module for SkillBridge

This module handles all email sending functionality using Flask-Mail.
Provides utility functions to send HTML emails for various events.
"""

from flask import render_template, current_app
from flask_mail import Mail, Message
from threading import Thread

mail = Mail()


def send_async_email(app, msg):
    """
    Send email asynchronously in a separate thread
    
    Args:
        app: Flask application instance
        msg: Flask-Mail Message object
    """
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")


def send_email(subject, recipient, template, **kwargs):
    """
    Send HTML email using template
    
    Args:
        subject (str): Email subject line
        recipient (str): Recipient email address
        template (str): Template file name (without .html extension)
        **kwargs: Additional context variables for the template
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    try:
        app = current_app._get_current_object()
        
        msg = Message(
            subject=subject,
            recipients=[recipient],
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        
        # Render HTML template
        msg.html = render_template(f'emails/{template}.html', **kwargs)
        
        # Send asynchronously to avoid blocking
        Thread(target=send_async_email, args=(app, msg)).start()
        
        return True
    except Exception as e:
        current_app.logger.error(f"Error creating email: {str(e)}")
        return False


def send_welcome_email(user):
    """
    Send welcome email to new user
    
    Args:
        user: User object
    """
    return send_email(
        subject='Welcome to SkillBridge',
        recipient=user.email,
        template='welcome',
        user=user
    )


def send_order_placed_emails(order):
    """
    Send order placement confirmation emails to both customer and provider
    
    Args:
        order: Order object with buyer, seller, and service relationships loaded
    """
    # Email to customer
    send_email(
        subject='Your order has been sent successfully',
        recipient=order.buyer.email,
        template='order_placed_customer',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )
    
    # Email to provider
    send_email(
        subject='New order received',
        recipient=order.seller.email,
        template='order_placed_provider',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )


def send_order_accepted_emails(order):
    """
    Send order acceptance confirmation emails to both customer and provider
    
    Args:
        order: Order object
    """
    # Email to customer
    send_email(
        subject='Your order has been accepted',
        recipient=order.buyer.email,
        template='order_accepted_customer',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )
    
    # Email to provider
    send_email(
        subject='Order accepted successfully',
        recipient=order.seller.email,
        template='order_accepted_provider',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )


def send_order_completed_emails(order):
    """
    Send order completion emails to both customer and provider
    
    Args:
        order: Order object
    """
    # Email to customer
    send_email(
        subject='Your order has been completed',
        recipient=order.buyer.email,
        template='order_completed_customer',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )
    
    # Email to provider
    send_email(
        subject='Order marked as completed',
        recipient=order.seller.email,
        template='order_completed_provider',
        order=order,
        customer=order.buyer,
        provider=order.seller,
        service=order.service
    )
