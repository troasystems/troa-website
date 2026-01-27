import resend
import logging
import os
import asyncio
from typing import Optional, List
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# Super admin email
SUPER_ADMIN_EMAIL = 'troa.systems@gmail.com'


class EmailService:
    def __init__(self):
        """Initialize Resend client with credentials"""
        self.api_key = os.getenv('RESEND_API_KEY')
        self.sender_email = os.getenv('SENDER_EMAIL', 'noreply@troa.in')
        self.reply_to_email = os.getenv('REPLY_TO_EMAIL', 'troa.systems@gmail.com')
        self.frontend_url = os.getenv('REACT_APP_BACKEND_URL', 'https://emailbuzz.preview.emergentagent.com')
        
        if not self.api_key:
            logger.warning("Resend API key not configured. Email sending will be disabled.")
        else:
            resend.api_key = self.api_key
            logger.info("Resend email service initialized successfully")

    async def _send_email(self, recipient_email: str, subject: str, html_body: str, text_body: str) -> dict:
        """Base method to send an email using Resend"""
        if not self.api_key:
            logger.error("Resend API key not configured. Cannot send email.")
            return {'status': 'error', 'message': 'Email service not configured'}

        try:
            params = {
                "from": self.sender_email,
                "to": [recipient_email],
                "subject": subject,
                "html": html_body,
                "text": text_body,
                "reply_to": self.reply_to_email
            }

            # Run sync SDK in thread to keep FastAPI non-blocking
            response = await asyncio.to_thread(resend.Emails.send, params)

            logger.info(f"Email sent to {recipient_email}, ID: {response.get('id')}")

            return {
                'status': 'sent',
                'message_id': response.get('id'),
                'recipient_email': recipient_email,
                'sent_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
            return {
                'status': 'error',
                'message': f"Email sending failed: {str(e)}"
            }

    async def _send_to_multiple(self, recipients: List[str], subject: str, html_body: str, text_body: str):
        """Send email to multiple recipients"""
        results = []
        for recipient in recipients:
            result = await self._send_email(recipient, subject, html_body, text_body)
            results.append(result)
        return results

    def _get_email_header(self) -> str:
        """Common email header"""
        return """
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <tr>
                            <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 3px solid #9333ea;">
                                <h1 style="color: #9333ea; margin: 0; font-size: 28px;">TROA</h1>
                                <p style="color: #666; margin: 10px 0 0 0; font-size: 14px;">The Retreat Owners Association</p>
                            </td>
                        </tr>
        """

    def _get_email_footer(self) -> str:
        """Common email footer"""
        return f"""
                        <tr>
                            <td style="padding: 30px 40px; background-color: #f9fafb; border-top: 1px solid #e5e7eb; border-radius: 0 0 8px 8px;">
                                <p style="margin: 0; font-size: 12px; color: #666; text-align: center;">&copy; 2025 TROA - The Retreat Owners Association. All rights reserved.</p>
                                <p style="margin: 10px 0 0 0; font-size: 12px; color: #666; text-align: center;">Questions? Contact us at {self.reply_to_email}</p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
        """

    # ============ VERIFICATION EMAILS ============

    async def send_verification_email(
        self,
        recipient_email: str,
        verification_link: str,
        user_name: Optional[str] = None,
        expiry_days: int = 14
    ) -> dict:
        """Send email verification link"""
        name_greeting = f"Hi {user_name}," if user_name else "Hello,"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 20px 0; font-size: 16px;">{name_greeting}</p>
                                <p style="margin: 0 0 20px 0; font-size: 16px;">Please verify your email address by clicking the button below:</p>
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center" style="padding: 30px 0;">
                                            <a href="{verification_link}" style="display: inline-block; background: linear-gradient(to right, #9333ea, #ec4899, #f97316); color: #ffffff; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">Verify Email Address</a>
                                        </td>
                                    </tr>
                                </table>
                                <p style="margin: 0 0 10px 0; font-size: 14px; color: #666;">Or copy this link: <a href="{verification_link}" style="color: #9333ea;">{verification_link}</a></p>
                                <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                    <p style="margin: 0; font-size: 14px; color: #92400e;"><strong>Note:</strong> This link expires in {expiry_days} days.</p>
                                </div>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"{name_greeting}\n\nPlease verify your email: {verification_link}\n\nThis link expires in {expiry_days} days."
        
        return await self._send_email(recipient_email, "Verify Your TROA Account", html_body, text_body)

    # ============ WELCOME EMAIL ============

    async def send_welcome_email(self, recipient_email: str, user_name: Optional[str] = None) -> dict:
        """Send welcome email with website features"""
        name_greeting = f"Hi {user_name}," if user_name else "Hello,"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 20px 0; font-size: 16px;">{name_greeting}</p>
                                <h2 style="color: #9333ea; margin: 0 0 20px 0;">Welcome to The Retreat Owners Association!</h2>
                                <p style="margin: 0 0 20px 0; font-size: 16px;">We're thrilled to have you as part of our community. Here's what you can do on our website:</p>
                                
                                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <h3 style="color: #9333ea; margin: 0 0 15px 0; font-size: 16px;">🏠 Key Features</h3>
                                    <ul style="margin: 0; padding-left: 20px;">
                                        <li style="margin-bottom: 10px;"><strong>Book Amenities</strong> - Reserve community facilities like the clubhouse, sports areas, and more</li>
                                        <li style="margin-bottom: 10px;"><strong>Register for Events</strong> - Join community gatherings, festivals, and social events</li>
                                        <li style="margin-bottom: 10px;"><strong>View Gallery</strong> - Browse photos from community events and amenities</li>
                                        <li style="margin-bottom: 10px;"><strong>Meet the Committee</strong> - Learn about your community leaders</li>
                                        <li style="margin-bottom: 10px;"><strong>Help Desk</strong> - Get answers to common questions</li>
                                        <li style="margin-bottom: 0;"><strong>Provide Feedback</strong> - Share your thoughts to help us improve</li>
                                    </ul>
                                </div>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center" style="padding: 30px 0;">
                                            <a href="{self.frontend_url}" style="display: inline-block; background: linear-gradient(to right, #9333ea, #ec4899, #f97316); color: #ffffff; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">Explore TROA Website</a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="margin: 20px 0 0 0; font-size: 14px; color: #666;">Quick Links:</p>
                                <p style="margin: 10px 0 0 0; font-size: 14px;">
                                    <a href="{self.frontend_url}/amenities" style="color: #9333ea;">Book Amenities</a> | 
                                    <a href="{self.frontend_url}/events" style="color: #9333ea;">View Events</a> | 
                                    <a href="{self.frontend_url}/committee" style="color: #9333ea;">Meet Committee</a> | 
                                    <a href="{self.frontend_url}/contact" style="color: #9333ea;">Contact Us</a>
                                </p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"""{name_greeting}

Welcome to The Retreat Owners Association!

Here's what you can do:
- Book Amenities: {self.frontend_url}/amenities
- Register for Events: {self.frontend_url}/events
- View Gallery: {self.frontend_url}/gallery
- Meet the Committee: {self.frontend_url}/committee
- Get Help: {self.frontend_url}/help-desk
- Provide Feedback: {self.frontend_url}/feedback

Visit our website: {self.frontend_url}
"""
        
        return await self._send_email(recipient_email, "Welcome to TROA - The Retreat Owners Association!", html_body, text_body)

    # ============ AMENITY BOOKING EMAILS ============

    async def send_booking_confirmation(
        self,
        recipient_email: str,
        user_name: str,
        amenity_name: str,
        booking_date: str,
        start_time: str,
        end_time: str,
        booking_id: str,
        additional_guests: List[str] = None
    ) -> dict:
        """Send booking confirmation to user"""
        guests_text = ""
        if additional_guests and len(additional_guests) > 0:
            guests_text = f"<p style='margin: 10px 0; font-size: 14px;'><strong>Additional Guests:</strong> {', '.join(additional_guests)}</p>"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 20px 0; font-size: 16px;">Hi {user_name},</p>
                                <h2 style="color: #22c55e; margin: 0 0 20px 0;">✅ Booking Confirmed!</h2>
                                
                                <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <h3 style="color: #166534; margin: 0 0 15px 0;">{amenity_name}</h3>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Date:</strong> {booking_date}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Time:</strong> {start_time} - {end_time}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Booking ID:</strong> {booking_id}</p>
                                    {guests_text}
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px;">You can view or cancel your booking from <a href="{self.frontend_url}/my-bookings" style="color: #9333ea;">My Bookings</a>.</p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"Hi {user_name},\n\nYour booking for {amenity_name} is confirmed!\n\nDate: {booking_date}\nTime: {start_time} - {end_time}\nBooking ID: {booking_id}\n\nView your bookings: {self.frontend_url}/my-bookings"
        
        return await self._send_email(recipient_email, f"Booking Confirmed: {amenity_name} on {booking_date}", html_body, text_body)

    async def send_booking_cancellation(
        self,
        recipient_email: str,
        user_name: str,
        amenity_name: str,
        booking_date: str,
        start_time: str,
        end_time: str
    ) -> dict:
        """Send booking cancellation confirmation"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 20px 0; font-size: 16px;">Hi {user_name},</p>
                                <h2 style="color: #dc2626; margin: 0 0 20px 0;">❌ Booking Cancelled</h2>
                                
                                <div style="background-color: #fef2f2; border: 1px solid #fecaca; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <h3 style="color: #991b1b; margin: 0 0 15px 0;">{amenity_name}</h3>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Date:</strong> {booking_date}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Time:</strong> {start_time} - {end_time}</p>
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px;">Need to make a new booking? Visit <a href="{self.frontend_url}/amenities" style="color: #9333ea;">Amenities</a>.</p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"Hi {user_name},\n\nYour booking has been cancelled:\n\nAmenity: {amenity_name}\nDate: {booking_date}\nTime: {start_time} - {end_time}"
        
        return await self._send_email(recipient_email, f"Booking Cancelled: {amenity_name} on {booking_date}", html_body, text_body)

    async def send_booking_notification_to_admins(
        self,
        action: str,  # 'created', 'cancelled'
        user_name: str,
        user_email: str,
        amenity_name: str,
        booking_date: str,
        start_time: str,
        end_time: str,
        admin_emails: List[str]
    ) -> List[dict]:
        """Send booking notification to admins/managers"""
        action_color = "#22c55e" if action == "created" else "#dc2626"
        action_text = "New Booking" if action == "created" else "Booking Cancelled"
        action_emoji = "✅" if action == "created" else "❌"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: {action_color}; margin: 0 0 20px 0;">{action_emoji} {action_text}</h2>
                                
                                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>User:</strong> {user_name} ({user_email})</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Amenity:</strong> {amenity_name}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Date:</strong> {booking_date}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Time:</strong> {start_time} - {end_time}</p>
                                </div>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"{action_text}\n\nUser: {user_name} ({user_email})\nAmenity: {amenity_name}\nDate: {booking_date}\nTime: {start_time} - {end_time}"
        
        return await self._send_to_multiple(admin_emails, f"[TROA] {action_text}: {amenity_name}", html_body, text_body)

    # ============ EVENT REGISTRATION EMAILS ============

    async def send_event_registration(
        self,
        recipient_email: str,
        user_name: str,
        event_name: str,
        event_date: str,
        event_time: str,
        registrants: List[dict],
        total_amount: float,
        payment_status: str,
        registration_id: str
    ) -> dict:
        """Send event registration confirmation"""
        status_text = "Payment Completed" if payment_status == "completed" else "Payment Pending Approval"
        status_emoji = "✅" if payment_status == "completed" else "⏳"
        
        registrants_html = ""
        for i, reg in enumerate(registrants, 1):
            reg_type = reg.get('registrant_type', 'adult').capitalize()
            registrants_html += f"<li style='margin-bottom: 5px;'>{reg.get('name', 'Guest')} ({reg_type})</li>"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 20px 0; font-size: 16px;">Hi {user_name},</p>
                                <h2 style="color: #9333ea; margin: 0 0 20px 0;">🎉 Event Registration Received!</h2>
                                
                                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <h3 style="color: #374151; margin: 0 0 15px 0;">{event_name}</h3>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Date:</strong> {event_date}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Time:</strong> {event_time}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Registration ID:</strong> {registration_id}</p>
                                    <p style="margin: 15px 0 5px 0; font-size: 14px;"><strong>Registrants:</strong></p>
                                    <ul style="margin: 0; padding-left: 20px;">{registrants_html}</ul>
                                    <p style="margin: 15px 0 5px 0; font-size: 14px;"><strong>Total Amount:</strong> ₹{total_amount}</p>
                                </div>
                                
                                <div style="background-color: {'#f0fdf4' if payment_status == 'completed' else '#fefce8'}; border: 1px solid {'#bbf7d0' if payment_status == 'completed' else '#fef08a'}; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 0; font-size: 14px; color: {'#166534' if payment_status == 'completed' else '#854d0e'};">{status_emoji} <strong>{status_text}</strong></p>
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px;">View your registrations: <a href="{self.frontend_url}/my-events" style="color: #9333ea;">My Events</a></p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"Hi {user_name},\n\nYou've registered for {event_name}!\n\nDate: {event_date}\nTime: {event_time}\nTotal: ₹{total_amount}\nStatus: {status_text}\n\nView: {self.frontend_url}/my-events"
        
        return await self._send_email(recipient_email, f"Event Registration: {event_name}", html_body, text_body)

    async def send_event_withdrawal(
        self,
        recipient_email: str,
        user_name: str,
        event_name: str,
        event_date: str
    ) -> dict:
        """Send event withdrawal confirmation"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 20px 0; font-size: 16px;">Hi {user_name},</p>
                                <h2 style="color: #dc2626; margin: 0 0 20px 0;">❌ Event Registration Withdrawn</h2>
                                
                                <div style="background-color: #fef2f2; border: 1px solid #fecaca; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <h3 style="color: #991b1b; margin: 0 0 10px 0;">{event_name}</h3>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Date:</strong> {event_date}</p>
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px;">For refund requests, please email: troa.systems@gmail.com</p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"Hi {user_name},\n\nYou've withdrawn from {event_name} ({event_date}).\n\nFor refunds, contact: troa.systems@gmail.com"
        
        return await self._send_email(recipient_email, f"Event Withdrawal: {event_name}", html_body, text_body)

    async def send_event_notification_to_admins(
        self,
        action: str,  # 'registered', 'modified', 'withdrawn', 'payment_completed'
        user_name: str,
        user_email: str,
        event_name: str,
        event_date: str,
        registrants_count: int,
        total_amount: float,
        payment_method: str,
        admin_emails: List[str]
    ) -> List[dict]:
        """Send event notification to admins/managers"""
        action_emojis = {
            'registered': '🎉',
            'modified': '✏️',
            'withdrawn': '❌',
            'payment_completed': '💰'
        }
        action_colors = {
            'registered': '#9333ea',
            'modified': '#f59e0b',
            'withdrawn': '#dc2626',
            'payment_completed': '#22c55e'
        }
        
        emoji = action_emojis.get(action, '📋')
        color = action_colors.get(action, '#374151')
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: {color}; margin: 0 0 20px 0;">{emoji} Event {action.replace('_', ' ').title()}</h2>
                                
                                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Event:</strong> {event_name}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Date:</strong> {event_date}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>User:</strong> {user_name} ({user_email})</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Registrants:</strong> {registrants_count}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Amount:</strong> ₹{total_amount}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Payment:</strong> {payment_method}</p>
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px;"><a href="{self.frontend_url}/admin" style="color: #9333ea;">View in Admin Portal</a></p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"Event {action.title()}\n\nEvent: {event_name}\nDate: {event_date}\nUser: {user_name} ({user_email})\nRegistrants: {registrants_count}\nAmount: ₹{total_amount}"
        
        return await self._send_to_multiple(admin_emails, f"[TROA] Event {action.replace('_', ' ').title()}: {event_name}", html_body, text_body)

    # ============ MEMBERSHIP APPLICATION EMAIL ============

    async def send_membership_application_notification(
        self,
        applicant_name: str,
        applicant_email: str,
        applicant_phone: str,
        villa_no: str,
        message: Optional[str],
        admin_emails: List[str]
    ) -> List[dict]:
        """Send membership application notification to admins"""
        message_html = f"<p style='margin: 5px 0; font-size: 14px;'><strong>Message:</strong> {message}</p>" if message else ""
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #9333ea; margin: 0 0 20px 0;">📝 New Membership Application</h2>
                                
                                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Name:</strong> {applicant_name}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Email:</strong> {applicant_email}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Phone:</strong> {applicant_phone}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Villa No:</strong> {villa_no}</p>
                                    {message_html}
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px;"><a href="{self.frontend_url}/admin" style="color: #9333ea;">Review in Admin Portal</a></p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"New Membership Application\n\nName: {applicant_name}\nEmail: {applicant_email}\nPhone: {applicant_phone}\nVilla: {villa_no}\n\nReview: {self.frontend_url}/admin"
        
        return await self._send_to_multiple(admin_emails, "[TROA] New Membership Application", html_body, text_body)

    # ============ FEEDBACK EMAIL ============

    async def send_feedback_notification(
        self,
        user_name: str,
        user_email: str,
        rating: int,
        works_well: Optional[str],
        needs_improvement: Optional[str],
        feature_suggestions: Optional[str],
        admin_emails: List[str]
    ) -> List[dict]:
        """Send feedback notification to admins"""
        stars = "⭐" * rating + "☆" * (5 - rating)
        
        feedback_sections = ""
        if works_well:
            feedback_sections += f"<p style='margin: 10px 0; font-size: 14px;'><strong>What works well:</strong><br>{works_well}</p>"
        if needs_improvement:
            feedback_sections += f"<p style='margin: 10px 0; font-size: 14px;'><strong>Needs improvement:</strong><br>{needs_improvement}</p>"
        if feature_suggestions:
            feedback_sections += f"<p style='margin: 10px 0; font-size: 14px;'><strong>Feature suggestions:</strong><br>{feature_suggestions}</p>"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <h2 style="color: #9333ea; margin: 0 0 20px 0;">💬 New User Feedback</h2>
                                
                                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>From:</strong> {user_name} ({user_email})</p>
                                    <p style="margin: 15px 0 5px 0; font-size: 18px;"><strong>Rating:</strong> {stars}</p>
                                    {feedback_sections}
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px;"><a href="{self.frontend_url}/admin" style="color: #9333ea;">View All Feedback</a></p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"New Feedback from {user_name} ({user_email})\n\nRating: {rating}/5\n"
        if works_well:
            text_body += f"\nWorks well: {works_well}"
        if needs_improvement:
            text_body += f"\nNeeds improvement: {needs_improvement}"
        if feature_suggestions:
            text_body += f"\nSuggestions: {feature_suggestions}"
        
        return await self._send_to_multiple(admin_emails, f"[TROA] New Feedback ({rating}/5 stars)", html_body, text_body)

    # ============ INVOICE EMAILS ============

    async def send_invoice_raised(
        self,
        recipient_email: str,
        user_name: str,
        invoice_number: str,
        amenity_name: str,
        month_year: str,
        total_amount: float,
        due_date: str
    ) -> dict:
        """Send invoice raised notification to user"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 20px 0; font-size: 16px;">Hi {user_name},</p>
                                <h2 style="color: #9333ea; margin: 0 0 20px 0;">📄 New Invoice Raised</h2>
                                
                                <div style="background-color: #f3f4f6; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Invoice Number:</strong> {invoice_number}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Amenity:</strong> {amenity_name}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Period:</strong> {month_year}</p>
                                    <p style="margin: 15px 0 5px 0; font-size: 20px;"><strong>Amount Due:</strong> ₹{total_amount:.0f}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Due Date:</strong> {due_date}</p>
                                </div>
                                
                                <div style="background-color: #fef3c7; border: 1px solid #fcd34d; padding: 15px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 0; font-size: 14px; color: #92400e;">⚠️ Please pay this invoice by the due date to avoid any inconvenience.</p>
                                </div>
                                
                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td align="center" style="padding: 20px 0;">
                                            <a href="{self.frontend_url}/my-invoices" style="display: inline-block; background: linear-gradient(to right, #9333ea, #ec4899, #f97316); color: #ffffff; padding: 14px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 14px;">Pay Now</a>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"Hi {user_name},\n\nA new invoice has been raised:\n\nInvoice: {invoice_number}\nAmenity: {amenity_name}\nPeriod: {month_year}\nAmount: ₹{total_amount:.0f}\nDue Date: {due_date}\n\nPay now: {self.frontend_url}/my-invoices"
        
        return await self._send_email(recipient_email, f"[TROA] Invoice #{invoice_number} - ₹{total_amount:.0f} Due", html_body, text_body)

    async def send_invoice_payment_receipt(
        self,
        recipient_email: str,
        user_name: str,
        invoice_number: str,
        amenity_name: str,
        month_year: str,
        total_amount: float,
        payment_id: str,
        payment_date: str
    ) -> dict:
        """Send payment receipt to user"""
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head><meta charset="UTF-8"></head>
        <body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; line-height: 1.6; color: #333;">
        {self._get_email_header()}
                        <tr>
                            <td style="padding: 40px;">
                                <p style="margin: 0 0 20px 0; font-size: 16px;">Hi {user_name},</p>
                                <h2 style="color: #22c55e; margin: 0 0 20px 0;">✅ Payment Received</h2>
                                
                                <p style="margin: 0 0 20px 0; font-size: 16px;">Thank you! Your payment has been successfully processed.</p>
                                
                                <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 20px; border-radius: 8px; margin: 20px 0;">
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Invoice Number:</strong> {invoice_number}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Amenity:</strong> {amenity_name}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Period:</strong> {month_year}</p>
                                    <p style="margin: 15px 0 5px 0; font-size: 20px;"><strong>Amount Paid:</strong> ₹{total_amount:.0f}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Payment ID:</strong> {payment_id}</p>
                                    <p style="margin: 5px 0; font-size: 14px;"><strong>Payment Date:</strong> {payment_date}</p>
                                </div>
                                
                                <p style="margin: 20px 0; font-size: 14px;">View all your invoices: <a href="{self.frontend_url}/my-invoices" style="color: #9333ea;">My Invoices</a></p>
                            </td>
                        </tr>
        {self._get_email_footer()}
        </body></html>
        """
        
        text_body = f"Hi {user_name},\n\nPayment received!\n\nInvoice: {invoice_number}\nAmenity: {amenity_name}\nPeriod: {month_year}\nAmount: ₹{total_amount:.0f}\nPayment ID: {payment_id}\nDate: {payment_date}"
        
        return await self._send_email(recipient_email, f"[TROA] Payment Receipt - Invoice #{invoice_number}", html_body, text_body)


# Helper function to get admin and manager emails
async def get_admin_manager_emails() -> List[str]:
    """Get list of admin and manager emails from database"""
    from motor.motor_asyncio import AsyncIOMotorClient
    
    mongo_url = os.getenv('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.getenv('DB_NAME', 'test_database')
    
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    try:
        users = await db.users.find(
            {'role': {'$in': ['admin', 'manager']}},
            {'_id': 0, 'email': 1}
        ).to_list(100)
        
        emails = [user['email'] for user in users if user.get('email')]
        
        # Always include super admin
        if SUPER_ADMIN_EMAIL not in emails:
            emails.append(SUPER_ADMIN_EMAIL)
        
        return emails
    finally:
        client.close()


# Singleton instance
email_service = EmailService()
