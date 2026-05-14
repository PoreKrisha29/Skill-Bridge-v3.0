"""
Socket.IO Event Handlers for Real-Time Chat

This module handles WebSocket events for real-time messaging
"""

from flask import request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room
from models import db, Message, Order
from managers import chat_manager
import pytz

def register_socketio_events(socketio):
    """Register all socket.io event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        if current_user.is_authenticated:
            print(f'User {current_user.username} connected')
        
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        if current_user.is_authenticated:
            print(f'User {current_user.username} disconnected')
    
    @socketio.on('join')
    def handle_join(data):
        """Join a chat room (order-based)"""
        if not current_user.is_authenticated:
            print("❌ Anonymous user tried to join a room")
            return
        
        try:
            order_id = int(data.get('order_id'))
            if not order_id:
                return
            
            # Verify user is part of this order
            order = Order.query.get(order_id)
            if not order or current_user.id not in [order.buyer_id, order.seller_id]:
                print(f"❌ User {current_user.username} unauthorized for order {order_id}")
                return
            
            room = f'order_{order_id}'
            join_room(room)
            emit('joined', {'order_id': order_id, 'user': current_user.username}, room=room)
            print(f"✨ User {current_user.username} joined room: {room}")
        except Exception as e:
            print(f"❌ Error in handle_join: {str(e)}")
    
    @socketio.on('leave')
    def handle_leave(data):
        """Leave a chat room"""
        try:
            order_id = data.get('order_id')
            if not order_id:
                return
            
            room = f'order_{order_id}'
            leave_room(room)
            print(f"🚪 User {current_user.username} left room: {room}")
        except Exception as e:
            print(f"❌ Error in handle_leave: {str(e)}")
    
    @socketio.on('send_message')
    def handle_send_message(data):
        """Handle incoming chat message"""
        if not current_user.is_authenticated:
            return
        
        try:
            order_id = int(data.get('order_id'))
            content = data.get('content', '').strip()
            
            if not order_id or not content:
                return
            
            # Save message to database
            message, error = chat_manager.send_message(order_id, current_user.id, content)
            
            if error:
                print(f"❌ Chat Manager Error: {error}")
                emit('error', {'message': error})
                return
            
            # Convert to IST for display
            ist_tz = pytz.timezone('Asia/Kolkata')
            created_at = message.created_at
            if created_at.tzinfo is None:
                utc_tz = pytz.UTC
                created_at = utc_tz.localize(created_at)
            ist_time = created_at.astimezone(ist_tz)
            
            # Broadcast to room (including self)
            room = f'order_{order_id}'
            message_data = {
                'id': message.id,
                'sender_id': message.sender_id,
                'sender_name': current_user.username,
                'content': message.content,
                'created_at': ist_time.isoformat(),
                'time_display': ist_time.strftime('%I:%M %p')
            }
            emit('new_message', message_data, room=room)
            print(f"💬 Message from {current_user.username} in {room}: {content[:30]}...")
        except Exception as e:
            print(f"❌ Error in handle_send_message: {str(e)}")
            emit('error', {'message': 'Failed to send message'})

