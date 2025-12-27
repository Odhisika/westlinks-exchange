"""
Email service for sending verification codes and notifications
"""
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_verification_email(recipient_email: str, code: str, vendor_name: str) -> bool:
    """
    Send verification code email to user
    
    Args:
        recipient_email: Recipient's email address
        code: 6-digit verification code
        vendor_name: Name of the vendor/user
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "Verify Your Payment Method - WestLinks Exchange"
    
    message = f"""
Hello {vendor_name},

You have requested to add a new payment method to your WestLinks Exchange account.

Your verification code is: {code}

This code will expire in 10 minutes.

If you did not request this, please ignore this email and contact support immediately.

Best regards,
WestLinks Exchange Team
    """.strip()
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #fbbf24, #06b6d4); padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ color: white; margin: 0; font-size: 24px; }}
        .content {{ background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px; }}
        .code-box {{ background: white; border: 2px solid #06b6d4; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }}
        .code {{ font-size: 32px; font-weight: bold; color: #06b6d4; letter-spacing: 5px; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
        .warning {{ background: #fef3c7; border-left: 4px solid #fbbf24; padding: 15px; margin: 20px 0; border-radius: 4px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>WestLinks Exchange</h1>
        </div>
        <div class="content">
            <h2>Hello {vendor_name},</h2>
            <p>You have requested to add a new payment method to your WestLinks Exchange account.</p>
            
            <div class="code-box">
                <p style="margin: 0; color: #666; font-size: 14px;">Your Verification Code</p>
                <div class="code">{code}</div>
                <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">Valid for 10 minutes</p>
            </div>
            
            <div class="warning">
                <strong>⚠️ Security Notice:</strong> If you did not request this verification code, please ignore this email and contact our support team immediately.
            </div>
            
            <p>Best regards,<br>
            <strong>WestLinks Exchange Team</strong></p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    try:
        # Check if email is configured
        if not settings.EMAIL_HOST_USER:
            logger.warning("Email not configured. Verification code would be: %s", code)
            # For development: print to console
            print(f"\n{'='*60}")
            print(f"VERIFICATION CODE FOR {recipient_email}: {code}")
            print(f"{'='*60}\n")
            return True
        
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Verification email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {recipient_email}: {str(e)}")
        # For development: still show code in console
        print(f"\n{'='*60}")
        print(f"EMAIL FAILED - VERIFICATION CODE FOR {recipient_email}: {code}")
        print(f"ERROR: {str(e)}")
        print(f"{'='*60}\n")
        return False


def send_welcome_email(recipient_email: str, vendor_name: str) -> bool:
    """
    Send welcome/onboarding email to newly registered users
    
    Args:
        recipient_email: User's email address
        vendor_name: Name of the new user
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = "Welcome to WestLinks Exchange! 🎉"
    
    message = f"""
Hello {vendor_name},

Welcome to WestLinks Exchange!

We're thrilled to have you join our community. Your account has been successfully created and you're ready to start trading cryptocurrency with ease.

What You Can Do:
• Buy Crypto: Purchase USDT, BTC, and other cryptocurrencies with Ghana Cedis
• Sell Crypto: Convert your crypto holdings to GHS instantly
• Exchange Currencies: Swap between NGN and GHS seamlessly
• Manage Payment Methods: Save your preferred bank and mobile money accounts
• Track Transactions: Monitor all your trading activities in one place

Getting Started:
1. Log in to your account at {settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'https://westlinks.exchange'}
2. Complete your profile setup
3. Add your payment methods for faster transactions
4. Start trading!

Security Tips:
• Never share your password with anyone
• Enable two-factor authentication (coming soon)
• Always verify wallet addresses before sending crypto

Need Help?
Our support team is ready to assist you 24/7. Contact us anytime through the support page or email us directly.

Thank you for choosing WestLinks Exchange. We're committed to providing you with the best crypto trading experience in Ghana and beyond!

Best regards,
The WestLinks Exchange Team
    """.strip()
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
        .header {{ background: linear-gradient(135deg, #fbbf24, #06b6d4); padding: 40px 20px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 28px; }}
        .header p {{ color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px; }}
        .content {{ background: #f9fafb; padding: 40px 30px; }}
        .welcome-box {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 30px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .welcome-box h2 {{ color: #06b6d4; margin-top: 0; font-size: 24px; }}
        .features {{ background: white; border-radius: 12px; padding: 30px; margin-bottom: 20px; }}
        .feature-item {{ display: flex; align-items: start; margin-bottom: 20px; }}
        .feature-icon {{ width: 40px; height: 40px; background: linear-gradient(135deg, #fbbf24, #06b6d4); border-radius: 8px; display: flex; align-items: center; justify-content: center; margin-right: 15px; flex-shrink: 0; }}
        .feature-icon span {{ color: white; font-size: 20px; font-weight: bold; }}
        .feature-content h3 {{ margin: 0 0 5px 0; color: #1f2937; font-size: 16px; }}
        .feature-content p {{ margin: 0; color: #6b7280; font-size: 14px; }}
        .cta-section {{ text-align: center; padding: 30px 20px; }}
        .cta-button {{ display: inline-block; background: linear-gradient(135deg, #fbbf24, #06b6d4); color: white; text-decoration: none; padding: 15px 40px; border-radius: 8px; font-weight: 600; font-size: 16px; }}
        .tips-box {{ background: #fef3c7; border-left: 4px solid #fbbf24; padding: 20px; margin: 20px 0; border-radius: 4px; }}
        .tips-box h3 {{ margin: 0 0 10px 0; color: #92400e; font-size: 16px; }}
        .tips-box ul {{ margin: 5px 0 0 0; padding-left: 20px; color: #78350f; }}
        .footer {{ text-align: center; padding: 30px 20px; color: #6b7280; font-size: 12px; }}
        .footer p {{ margin: 5px 0; }}
        .social-links {{ margin-top: 15px; }}
        .social-links a {{ display: inline-block; margin: 0 10px; color: #06b6d4; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Welcome to WestLinks Exchange!</h1>
            <p>Your account is ready. Let's get started!</p>
        </div>
        
        <div class="content">
            <div class="welcome-box">
                <h2>Hello {vendor_name}!</h2>
                <p>Thank you for joining WestLinks Exchange. We're excited to be part of your cryptocurrency journey. Your account has been successfully created and verified.</p>
            </div>
            
            <div class="features">
                <h3 style="margin-top: 0; color: #1f2937; font-size: 20px; margin-bottom: 25px;">What You Can Do:</h3>
                
                <div class="feature-item">
                    <div class="feature-icon"><span>💰</span></div>
                    <div class="feature-content">
                        <h3>Buy Cryptocurrency</h3>
                        <p>Purchase USDT, BTC, and other cryptocurrencies using Ghana Cedis with instant delivery</p>
                    </div>
                </div>
                
                <div class="feature-item">
                    <div class="feature-icon"><span>💵</span></div>
                    <div class="feature-content">
                        <h3>Sell Cryptocurrency</h3>
                        <p>Convert your crypto holdings to GHS and receive payments via mobile money or bank transfer</p>
                    </div>
                </div>
                
                <div class="feature-item">
                    <div class="feature-icon"><span>🔄</span></div>
                    <div class="feature-content">
                        <h3>Currency Exchange</h3>
                        <p>Seamlessly swap between Nigerian Naira (NGN) and Ghana Cedis (GHS)</p>
                    </div>
                </div>
                
                <div class="feature-item">
                    <div class="feature-icon"><span>💳</span></div>
                    <div class="feature-content">
                        <h3>Payment Methods</h3>
                        <p>Save your preferred bank and mobile money accounts for faster transactions</p>
                    </div>
                </div>
                
                <div class="feature-item">
                    <div class="feature-icon"><span>📊</span></div>
                    <div class="feature-content">
                        <h3>Transaction History</h3>
                        <p>Track all your trading activities with detailed transaction records</p>
                    </div>
                </div>
            </div>
            
            <div class="cta-section">
                <p style="margin-bottom: 20px; color: #6b7280;">Ready to start trading?</p>
                <a href="https://westlinks.exchange/login" class="cta-button">Access Your Dashboard</a>
            </div>
            
            <div class="tips-box">
                <h3>🔒 Security Tips</h3>
                <ul>
                    <li>Never share your password with anyone</li>
                    <li>Always verify wallet addresses before sending crypto</li>
                    <li>Enable email notifications for all transactions</li>
                    <li>Contact support immediately if you notice suspicious activity</li>
                </ul>
            </div>
            
            <div style="background: white; border-radius: 12px; padding: 25px; text-align: center; margin-top: 20px;">
                <h3 style="margin: 0 0 10px 0; color: #1f2937;">Need Help?</h3>
                <p style="margin: 0; color: #6b7280;">Our support team is available 24/7 to assist you with any questions or concerns.</p>
                <div class="social-links">
                    <a href="mailto:support@westlinks.exchange">Email Support</a> • 
                    <a href="https://westlinks.exchange/support">Help Center</a>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p><strong>WestLinks Exchange</strong></p>
            <p>Ghana's Premier Cryptocurrency Trading Platform</p>
            <p style="margin-top: 15px;">This is an automated message. Please do not reply to this email.</p>
            <p>© 2024 WestLinks Exchange. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    try:
        # Check if email is configured
        if not settings.EMAIL_HOST_USER:
            logger.warning("Email not configured. Welcome email would be sent to: %s", recipient_email)
            print(f"\n{'='*60}")
            print(f"WELCOME EMAIL FOR {recipient_email}")
            print(f"Welcome, {vendor_name}!")
            print(f"{'='*60}\n")
            return True
        
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Welcome email sent to {recipient_email}")
        return True
    except Exception as e:
        return False


def send_buy_order_email(recipient_email: str, order_details: dict) -> bool:
    """
    Send email notification for a new buy order
    
    Args:
        recipient_email: User's email address
        order_details: Dictionary containing order info (id, amount, asset, etc.)
    
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    subject = f"Order Received - {order_details.get('order_id')} - WestLinks Exchange"
    
    message = f"""
Hello,

We have successfully received your order {order_details.get('order_id')}.

Order Details:
Order ID: {order_details.get('order_id')}
Amount: {order_details.get('amount_ghs')} GHS
Asset: {order_details.get('asset_symbol')}
Network: {order_details.get('network')}
Wallet Address: {order_details.get('recipient_address')}

We will verify your payment and process the delivery to your wallet as soon as possible.

If you have any questions, please contact our support team.

Best regards,
WestLinks Exchange Team
    """.strip()
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
        .header {{ background: linear-gradient(135deg, #fbbf24, #06b6d4); padding: 30px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 24px; }}
        .content {{ background: #f9fafb; padding: 30px; }}
        .order-box {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e5e7eb; }}
        .order-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #f3f4f6; padding-bottom: 10px; }}
        .order-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        .label {{ color: #6b7280; font-size: 14px; }}
        .value {{ font-weight: 600; color: #1f2937; font-size: 14px; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Order Received</h1>
        </div>
        
        <div class="content">
            <h2>Hello,</h2>
            <p>We have successfully received your order. We will verify your payment and process the delivery to your wallet as soon as possible.</p>
            
            <div class="order-box">
                <div class="order-row">
                    <span class="label">Order ID</span>
                    <span class="value">{order_details.get('order_id')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Amount</span>
                    <span class="value">₵{order_details.get('amount_ghs')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Asset</span>
                    <span class="value">{order_details.get('asset_symbol')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Network</span>
                    <span class="value">{order_details.get('network')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Wallet Address</span>
                    <span class="value" style="font-family: monospace; font-size: 12px;">{order_details.get('recipient_address')}</span>
                </div>
            </div>
            
            <p>Thank you for choosing WestLinks Exchange!</p>
        </div>
        
        <div class="footer">
            <p>WestLinks Exchange Team</p>
            <p>This is an automated message. Please do not reply.</p>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    try:
        if not settings.EMAIL_HOST_USER:
            logger.warning("Email not configured. Order email would be sent to: %s", recipient_email)
            print(f"\n{'='*60}")
            print(f"ORDER EMAIL FOR {recipient_email}")
            print(f"Order ID: {order_details.get('order_id')}")
            print(f"{'='*60}\n")
            return True
            
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Order email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send order email to {recipient_email}: {str(e)}")
        return False


def send_sell_order_email(recipient_email: str, order_details: dict) -> bool:
    """
    Send email notification for a new sell order
    """
    subject = f"Sell Order Received - {order_details.get('payment_id')} - WestLinks Exchange"
    
    message = f"""
Hello,

We have successfully received your sell order {order_details.get('payment_id')}.

Order Details:
Order ID: {order_details.get('payment_id')}
Crypto Amount: {order_details.get('crypto_amount')} {order_details.get('crypto_symbol')}
Fiat Amount: {order_details.get('fiat_amount')} GHS
Network: {order_details.get('network')}
Wallet Address: {order_details.get('wallet_address')}

Please send your crypto to the wallet address provided on the confirmation page.
Once we confirm receipt, we will process your payment.

Best regards,
WestLinks Exchange Team
    """.strip()
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
        .header {{ background: linear-gradient(135deg, #fbbf24, #06b6d4); padding: 30px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 24px; }}
        .content {{ background: #f9fafb; padding: 30px; }}
        .order-box {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e5e7eb; }}
        .order-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #f3f4f6; padding-bottom: 10px; }}
        .order-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        .label {{ color: #6b7280; font-size: 14px; }}
        .value {{ font-weight: 600; color: #1f2937; font-size: 14px; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Sell Order Received</h1>
        </div>
        
        <div class="content">
            <h2>Hello,</h2>
            <p>We have successfully received your sell order. Please send your crypto to the wallet address provided.</p>
            
            <div class="order-box">
                <div class="order-row">
                    <span class="label">Order ID</span>
                    <span class="value">{order_details.get('payment_id')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Crypto Amount</span>
                    <span class="value">{order_details.get('crypto_amount')} {order_details.get('crypto_symbol')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Fiat Amount</span>
                    <span class="value">₵{order_details.get('fiat_amount')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Network</span>
                    <span class="value">{order_details.get('network')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Wallet Address</span>
                    <span class="value" style="font-family: monospace; font-size: 12px;">{order_details.get('wallet_address')}</span>
                </div>
            </div>
            
            <p>Once we confirm receipt, we will process your payment.</p>
        </div>
        
        <div class="footer">
            <p>WestLinks Exchange Team</p>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    try:
        if not settings.EMAIL_HOST_USER:
            logger.warning("Email not configured. Sell order email would be sent to: %s", recipient_email)
            print(f"\n{'='*60}")
            print(f"SELL ORDER EMAIL FOR {recipient_email}")
            print(f"Order ID: {order_details.get('payment_id')}")
            print(f"{'='*60}\n")
            return True
            
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Sell order email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send sell order email to {recipient_email}: {str(e)}")
        return False


def send_exchange_order_email(recipient_email: str, order_details: dict) -> bool:
    """
    Send email notification for a new exchange order
    """
    subject = f"Exchange Order Received - {order_details.get('exchange_id')} - WestLinks Exchange"
    
    message = f"""
Hello,

We have successfully received your exchange order {order_details.get('exchange_id')}.

Order Details:
Order ID: {order_details.get('exchange_id')}
From: {order_details.get('from_amount')} {order_details.get('from_currency')}
To: {order_details.get('to_amount')} {order_details.get('to_currency')}
Rate: {order_details.get('exchange_rate')}

We will process your exchange as soon as possible.

Best regards,
WestLinks Exchange Team
    """.strip()
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
        .header {{ background: linear-gradient(135deg, #fbbf24, #06b6d4); padding: 30px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 24px; }}
        .content {{ background: #f9fafb; padding: 30px; }}
        .order-box {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e5e7eb; }}
        .order-row {{ display: flex; justify-content: space-between; margin-bottom: 10px; border-bottom: 1px solid #f3f4f6; padding-bottom: 10px; }}
        .order-row:last-child {{ border-bottom: none; margin-bottom: 0; padding-bottom: 0; }}
        .label {{ color: #6b7280; font-size: 14px; }}
        .value {{ font-weight: 600; color: #1f2937; font-size: 14px; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Exchange Order Received</h1>
        </div>
        
        <div class="content">
            <h2>Hello,</h2>
            <p>We have successfully received your exchange order.</p>
            
            <div class="order-box">
                <div class="order-row">
                    <span class="label">Order ID</span>
                    <span class="value">{order_details.get('exchange_id')}</span>
                </div>
                <div class="order-row">
                    <span class="label">From</span>
                    <span class="value">{order_details.get('from_amount')} {order_details.get('from_currency')}</span>
                </div>
                <div class="order-row">
                    <span class="label">To</span>
                    <span class="value">{order_details.get('to_amount')} {order_details.get('to_currency')}</span>
                </div>
                <div class="order-row">
                    <span class="label">Rate</span>
                    <span class="value">{order_details.get('exchange_rate')}</span>
                </div>
            </div>
            
            <p>We will process your exchange as soon as possible.</p>
        </div>
        
        <div class="footer">
            <p>WestLinks Exchange Team</p>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    try:
        if not settings.EMAIL_HOST_USER:
            logger.warning("Email not configured. Exchange order email would be sent to: %s", recipient_email)
            print(f"\n{'='*60}")
            print(f"EXCHANGE ORDER EMAIL FOR {recipient_email}")
            print(f"Order ID: {order_details.get('exchange_id')}")
            print(f"{'='*60}\n")
            return True
            
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Exchange order email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send exchange order email to {recipient_email}: {str(e)}")
        return False


def send_order_status_email(recipient_email: str, order_details: dict, order_type: str) -> bool:
    """
    Send email notification for order status update
    """
    status = order_details.get('status', '').upper()
    order_id = order_details.get('id')
    
    subject = f"Order Update: {status} - {order_id} - WestLinks Exchange"
    
    message = f"""
Hello,

Your {order_type} order {order_id} has been updated to: {status}.

{f"Admin Note: {order_details.get('admin_notes')}" if order_details.get('admin_notes') else ""}

If you have any questions, please contact support.

Best regards,
WestLinks Exchange Team
    """.strip()
    
    html_message = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 0; }}
        .header {{ background: linear-gradient(135deg, #fbbf24, #06b6d4); padding: 30px; text-align: center; }}
        .header h1 {{ color: white; margin: 0; font-size: 24px; }}
        .content {{ background: #f9fafb; padding: 30px; }}
        .status-box {{ background: white; border-radius: 8px; padding: 20px; margin: 20px 0; border: 1px solid #e5e7eb; text-align: center; }}
        .status {{ font-size: 24px; font-weight: bold; color: #06b6d4; }}
        .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Order Update</h1>
        </div>
        
        <div class="content">
            <h2>Hello,</h2>
            <p>Your {order_type} order <strong>{order_id}</strong> has been updated.</p>
            
            <div class="status-box">
                <p style="margin: 0; color: #6b7280;">New Status</p>
                <div class="status">{status}</div>
            </div>
            
            {f'<p><strong>Note from Admin:</strong><br>{order_details.get("admin_notes")}</p>' if order_details.get('admin_notes') else ''}
            
            <p>If you have any questions, please contact support.</p>
        </div>
        
        <div class="footer">
            <p>WestLinks Exchange Team</p>
        </div>
    </div>
</body>
</html>
    """.strip()
    
    try:
        if not settings.EMAIL_HOST_USER:
            logger.warning("Email not configured. Status update email would be sent to: %s", recipient_email)
            print(f"\n{'='*60}")
            print(f"STATUS UPDATE EMAIL FOR {recipient_email}")
            print(f"Order ID: {order_id}")
            print(f"New Status: {status}")
            print(f"{'='*60}\n")
            return True
            
        send_mail(
            subject=subject,
            message=message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL or settings.EMAIL_HOST_USER,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info(f"Status update email sent to {recipient_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send status update email to {recipient_email}: {str(e)}")
        return False
