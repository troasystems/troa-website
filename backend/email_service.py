import boto3
import logging
import os
import asyncio
from typing import Optional
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        """Initialize AWS SES client with credentials"""
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.region = os.getenv('AWS_SES_REGION', 'ap-south-2')
        self.sender_email = os.getenv('AWS_SES_SENDER_EMAIL', 'noreply@troa.in')
        self.reply_to_email = os.getenv('AWS_SES_REPLY_TO_EMAIL', 'troa.systems@gmail.com')
        
        if not self.access_key or not self.secret_key:
            logger.warning("AWS credentials not configured. Email sending will be disabled.")
            self.ses_client = None
        else:
            self.ses_client = boto3.client(
                'ses',
                region_name=self.region,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key
            )

    async def send_verification_email(
        self,
        recipient_email: str,
        verification_link: str,
        user_name: Optional[str] = None,
        expiry_days: int = 14
    ) -> dict:
        """Send a verification email with HTML template"""
        if not self.ses_client:
            logger.error("SES client not initialized. Cannot send email.")
            return {'status': 'error', 'message': 'Email service not configured'}

        try:
            html_body = self._generate_verification_email_html(
                verification_link=verification_link,
                user_name=user_name,
                expiry_days=expiry_days
            )
            
            text_body = self._generate_verification_email_text(
                verification_link=verification_link,
                user_name=user_name,
                expiry_days=expiry_days
            )

            params = {
                'Source': self.sender_email,
                'Destination': {
                    'ToAddresses': [recipient_email]
                },
                'Message': {
                    'Subject': {
                        'Data': 'Verify Your TROA Account',
                        'Charset': 'UTF-8'
                    },
                    'Body': {
                        'Text': {
                            'Data': text_body,
                            'Charset': 'UTF-8'
                        },
                        'Html': {
                            'Data': html_body,
                            'Charset': 'UTF-8'
                        }
                    }
                },
                'ReplyToAddresses': [self.reply_to_email]
            }

            # Run sync SDK in thread to keep FastAPI non-blocking
            response = await asyncio.to_thread(self.ses_client.send_email, **params)

            logger.info(
                f"Verification email sent to {recipient_email}, "
                f"MessageId: {response.get('MessageId')}"
            )

            return {
                'status': 'sent',
                'message_id': response.get('MessageId'),
                'recipient_email': recipient_email,
                'sent_at': datetime.utcnow().isoformat()
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            
            logger.error(
                f"Failed to send verification email to {recipient_email}: "
                f"{error_code} - {error_message}"
            )
            
            # Check if it's a sandbox mode issue
            if 'not verified' in error_message.lower():
                logger.warning(
                    f"AWS SES Sandbox Mode: Cannot send to {recipient_email}. "
                    "Request production access in AWS SES console to send to any email."
                )
            
            return {
                'status': 'error',
                'message': f"Email sending failed: {error_message}"
            }
        except Exception as e:
            logger.error(f"Unexpected error sending email: {str(e)}")
            return {
                'status': 'error',
                'message': f"Email sending failed: {str(e)}"
            }

    def _generate_verification_email_html(
        self,
        verification_link: str,
        user_name: Optional[str] = None,
        expiry_days: int = 14
    ) -> str:
        """Generate HTML email template for verification"""
        name_greeting = f"Hi {user_name}," if user_name else "Hello,"
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 20px 40px; text-align: center; border-bottom: 3px solid #9333ea;">
                            <h1 style="color: #9333ea; margin: 0; font-size: 28px;">TROA</h1>
                            <p style="color: #666; margin: 10px 0 0 0; font-size: 14px;">The Retreat Owners Association</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <p style="margin: 0 0 20px 0; font-size: 16px;">{name_greeting}</p>
                            
                            <p style="margin: 0 0 20px 0; font-size: 16px;">Thank you for registering with TROA! Please verify your email address by clicking the button below to complete your account setup.</p>
                            
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 30px 0;">
                                        <a href="{verification_link}" style="display: inline-block; background: linear-gradient(to right, #9333ea, #ec4899, #f97316); color: #ffffff; padding: 16px 32px; text-decoration: none; border-radius: 8px; font-weight: bold; font-size: 16px;">Verify Email Address</a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="margin: 0 0 10px 0; font-size: 14px; color: #666;">Or copy and paste this link in your browser:</p>
                            <p style="margin: 0 0 20px 0; font-size: 12px; word-break: break-all; color: #9333ea;">{verification_link}</p>
                            
                            <div style="background-color: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 20px 0; border-radius: 4px;">
                                <p style="margin: 0; font-size: 14px; color: #92400e;"><strong>Important:</strong> This verification link will expire in <strong>{expiry_days} days</strong>. You can use the app during this grace period, but you must verify your email to continue accessing your account after the grace period ends.</p>
                            </div>
                            
                            <p style="margin: 20px 0 0 0; font-size: 14px; color: #666;">If you did not register for this account, please ignore this email.</p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
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
</body>
</html>
        """
        return html.strip()

    def _generate_verification_email_text(
        self,
        verification_link: str,
        user_name: Optional[str] = None,
        expiry_days: int = 14
    ) -> str:
        """Generate plain text version of verification email"""
        name_greeting = f"Hi {user_name}," if user_name else "Hello,"
        
        text = f"""
{name_greeting}

Thank you for registering with TROA! Please verify your email address by visiting the link below to complete your account setup.

{verification_link}

IMPORTANT: This verification link will expire in {expiry_days} days. You can use the app during this grace period, but you must verify your email to continue accessing your account after the grace period ends.

If you did not register for this account, please ignore this email.

---
Questions? Contact us at {self.reply_to_email}
(c) 2025 TROA - The Retreat Owners Association. All rights reserved.
        """
        return text.strip()


# Singleton instance
email_service = EmailService()
