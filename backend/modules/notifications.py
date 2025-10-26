"""
Notification Module
Sends SMS and email alerts using Twilio and SendGrid
"""

import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class NotificationService:
    """Send SMS and email notifications"""
    
    def __init__(self):
        # SMS Configuration (Twilio)
        self.twilio_enabled = all([
            os.getenv('TWILIO_ACCOUNT_SID'),
            os.getenv('TWILIO_AUTH_TOKEN'),
            os.getenv('TWILIO_PHONE_NUMBER')
        ])
        
        if self.twilio_enabled:
            try:
                from twilio.rest import Client
                self.twilio_client = Client(
                    os.getenv('TWILIO_ACCOUNT_SID'),
                    os.getenv('TWILIO_AUTH_TOKEN')
                )
                self.twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
                print("✓ Twilio SMS enabled")
            except ImportError:
                print("⚠ Twilio not installed. SMS disabled.")
                self.twilio_enabled = False
        else:
            print("⚠ Twilio credentials not found. SMS disabled.")
        
        # Email Configuration (SendGrid)
        self.sendgrid_enabled = all([
            os.getenv('SENDGRID_API_KEY'),
            os.getenv('SENDGRID_FROM_EMAIL')
        ])
        
        if self.sendgrid_enabled:
            try:
                from sendgrid import SendGridAPIClient
                from sendgrid.helpers.mail import Mail
                self.sendgrid_client = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
                self.from_email = os.getenv('SENDGRID_FROM_EMAIL')
                print("✓ SendGrid email enabled")
            except ImportError:
                print("⚠ SendGrid not installed. Email disabled.")
                self.sendgrid_enabled = False
        else:
            print("⚠ SendGrid credentials not found. Email disabled.")
        
        # Get recipient lists
        self.sms_recipients = self._parse_recipients(os.getenv('ALERT_RECIPIENTS_SMS', ''))
        self.email_recipients = self._parse_recipients(os.getenv('ALERT_RECIPIENTS_EMAIL', ''))
    
    def send_sms(self, message: str, recipients: List[str] = None) -> dict:
        """
        Send SMS alert
        
        Args:
            message: Text message to send
            recipients: List of phone numbers (defaults to env config)
        
        Returns:
            dict: {'success': bool, 'sent': int, 'errors': List}
        """
        if not self.twilio_enabled:
            print("SMS not configured. Message:", message)
            return {'success': False, 'sent': 0, 'errors': ['Twilio not configured']}
        
        recipients = recipients or self.sms_recipients
        
        if not recipients:
            return {'success': False, 'sent': 0, 'errors': ['No recipients configured']}
        
        sent_count = 0
        errors = []
        
        for phone_number in recipients:
            try:
                message_obj = self.twilio_client.messages.create(
                    body=message,
                    from_=self.twilio_number,
                    to=phone_number
                )
                sent_count += 1
                print(f"✓ SMS sent to {phone_number}: {message_obj.sid}")
            except Exception as e:
                error_msg = f"Failed to send SMS to {phone_number}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
        
        return {
            'success': sent_count > 0,
            'sent': sent_count,
            'errors': errors
        }
    
    def send_email(self, subject: str, html_content: str, 
                   recipients: List[str] = None) -> dict:
        """
        Send email alert
        
        Args:
            subject: Email subject line
            html_content: HTML email body
            recipients: List of email addresses (defaults to env config)
        
        Returns:
            dict: {'success': bool, 'sent': int, 'errors': List}
        """
        if not self.sendgrid_enabled:
            print("Email not configured. Subject:", subject)
            return {'success': False, 'sent': 0, 'errors': ['SendGrid not configured']}
        
        from sendgrid.helpers.mail import Mail
        
        recipients = recipients or self.email_recipients
        
        if not recipients:
            return {'success': False, 'sent': 0, 'errors': ['No recipients configured']}
        
        sent_count = 0
        errors = []
        
        for email_address in recipients:
            try:
                message = Mail(
                    from_email=self.from_email,
                    to_emails=email_address,
                    subject=subject,
                    html_content=html_content
                )
                
                response = self.sendgrid_client.send(message)
                
                if response.status_code in [200, 202]:
                    sent_count += 1
                    print(f"✓ Email sent to {email_address}")
                else:
                    error_msg = f"Failed to send email to {email_address}: Status {response.status_code}"
                    errors.append(error_msg)
                    print(f"✗ {error_msg}")
            
            except Exception as e:
                error_msg = f"Failed to send email to {email_address}: {str(e)}"
                errors.append(error_msg)
                print(f"✗ {error_msg}")
        
        return {
            'success': sent_count > 0,
            'sent': sent_count,
            'errors': errors
        }
    
    def send_alert(self, sms_message: str, email_subject: str, 
                   email_html: str) -> dict:
        """
        Send both SMS and email alerts
        
        Args:
            sms_message: SMS text
            email_subject: Email subject
            email_html: Email HTML body
        
        Returns:
            dict: Combined results from SMS and email
        """
        sms_result = self.send_sms(sms_message)
        email_result = self.send_email(email_subject, email_html)
        
        return {
            'sms': sms_result,
            'email': email_result,
            'overall_success': sms_result['success'] or email_result['success']
        }
    
    def _parse_recipients(self, recipient_string: str) -> List[str]:
        """Parse comma-separated recipient list"""
        if not recipient_string:
            return []
        return [r.strip() for r in recipient_string.split(',') if r.strip()]
    
    def test_notifications(self):
        """Send test notifications to verify configuration"""
        print("\n=== Testing Notification Configuration ===\n")
        
        test_sms = "GridGuard Test: SMS notifications are working! 🎉"
        test_email_subject = "GridGuard Test: Email Configuration"
        test_email_html = """
        <html>
        <body>
            <h2>GridGuard Email Test</h2>
            <p>If you're reading this, email notifications are working correctly! 🎉</p>
            <p>Your alert system is ready to notify you of transmission line issues.</p>
        </body>
        </html>
        """
        
        results = self.send_alert(test_sms, test_email_subject, test_email_html)
        
        print("\n=== Test Results ===")
        print(f"SMS: {'✓ Sent' if results['sms']['success'] else '✗ Failed'} "
              f"({results['sms']['sent']} messages)")
        print(f"Email: {'✓ Sent' if results['email']['success'] else '✗ Failed'} "
              f"({results['email']['sent']} messages)")
        
        if results['sms']['errors']:
            print("\nSMS Errors:")
            for error in results['sms']['errors']:
                print(f"  - {error}")
        
        if results['email']['errors']:
            print("\nEmail Errors:")
            for error in results['email']['errors']:
                print(f"  - {error}")
        
        return results

    def send_emergency_coordination_alert(self, coordination_plan: dict, critical_lines_count: int) -> dict:
        """
        Send emergency coordination alert with LLM-generated action plan

        Args:
            coordination_plan: Result from LLMCoordinator.generate_coordination_plan()
            critical_lines_count: Number of critical lines

        Returns:
            dict: {'success': bool, 'sms_sent': int, 'email_sent': int, 'errors': List}
        """
        import pandas as pd

        if not coordination_plan['success']:
            return {
                'success': False,
                'sms_sent': 0,
                'email_sent': 0,
                'errors': [f"Coordination plan generation failed: {coordination_plan['error']}"]
            }

        # Import here to avoid circular dependency
        from modules.llm_coordinator import LLMCoordinator
        coordinator = LLMCoordinator()

        # Format SMS message with emergency header
        sms_message = coordinator.format_sms_message(coordination_plan)

        # Send SMS to all configured recipients
        sms_result = self.send_sms(sms_message)

        # Build detailed HTML email
        email_subject = f"⚡ EMERGENCY: {critical_lines_count} Critical Lines - Coordination Required"

        email_html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px;">
            <div style="background-color: #DC2626; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 24px;">⚡ EMERGENCY GRID ALERT</h1>
                <p style="margin: 10px 0 0 0; font-size: 16px;">Critical Transmission Line Overload</p>
            </div>

            <div style="background-color: #FEF2F2; padding: 20px; border-left: 4px solid #DC2626;">
                <h2 style="color: #991B1B; margin-top: 0;">Situation Summary</h2>
                <p style="font-size: 16px; margin: 0;">{coordination_plan['summary']}</p>
            </div>

            <div style="padding: 20px; background-color: white;">
                <h2 style="color: #374151;">Coordinated Action Plan</h2>
                <p style="color: #6B7280; margin-bottom: 20px;">
                    The following steps have been generated using AI analysis to optimize response and minimize cascading failures.
                    Execute in order:
                </p>

                <div style="background-color: #F9FAFB; padding: 15px; border-radius: 6px; border-left: 3px solid #3B82F6;">
                    <pre style="font-family: monospace; white-space: pre-wrap; margin: 0; color: #1F2937;">{coordination_plan['plan']}</pre>
                </div>

                <div style="margin-top: 30px; padding: 15px; background-color: #FEF3C7; border-radius: 6px; border-left: 3px solid #F59E0B;">
                    <p style="margin: 0; color: #92400E;"><strong>⚠ Critical Safety Notes:</strong></p>
                    <ul style="color: #92400E; margin: 10px 0 0 0;">
                        <li>Coordinate all actions via dispatch before execution</li>
                        <li>Verify line status in real-time before any switching</li>
                        <li>Follow all safety protocols and PPE requirements</li>
                        <li>Report completion status immediately after each step</li>
                    </ul>
                </div>
            </div>

            <div style="background-color: #F3F4F6; padding: 15px; text-align: center; border-radius: 0 0 8px 8px;">
                <p style="margin: 0; color: #6B7280; font-size: 12px;">
                    Generated by LineLink Emergency Coordination System | {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
                </p>
            </div>
        </div>
        """

        # Send email to all configured recipients
        email_result = self.send_email(email_subject, email_html)

        return {
            'success': sms_result['success'] or email_result['success'],
            'sms_sent': sms_result['sent'],
            'email_sent': email_result['sent'],
            'errors': sms_result.get('errors', []) + email_result.get('errors', [])
        }


# Alternative: Email-to-SMS Gateway (Completely Free)
class FreeEmailToSMS:
    """
    Use email-to-SMS gateways (completely free alternative to Twilio)
    Requires knowing recipient's carrier
    """
    
    CARRIER_GATEWAYS = {
        'att': '@txt.att.net',
        'tmobile': '@tmomail.net',
        'verizon': '@vtext.com',
        'sprint': '@messaging.sprintomail.com',
        'boost': '@sms.myboostmobile.com',
        'cricket': '@sms.cricketwireless.net',
        'uscellular': '@email.uscc.net'
    }
    
    def __init__(self, smtp_server: str = 'smtp.gmail.com', 
                 smtp_port: int = 587,
                 email: str = None, 
                 password: str = None):
        """
        Initialize with email credentials
        For Gmail: use an App Password, not your regular password
        https://support.google.com/accounts/answer/185833
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email or os.getenv('SMTP_EMAIL')
        self.password = password or os.getenv('SMTP_PASSWORD')
    
    def send_sms_via_email(self, phone: str, carrier: str, message: str) -> bool:
        """
        Send SMS via email gateway
        
        Args:
            phone: 10-digit phone number (no formatting)
            carrier: Carrier name (e.g., 'att', 'verizon')
            message: Message text
        
        Returns:
            bool: Success status
        """
        import smtplib
        from email.mime.text import MIMEText
        
        if carrier.lower() not in self.CARRIER_GATEWAYS:
            print(f"Unknown carrier: {carrier}")
            return False
        
        to_email = phone + self.CARRIER_GATEWAYS[carrier.lower()]
        
        msg = MIMEText(message)
        msg['From'] = self.email
        msg['To'] = to_email
        msg['Subject'] = ''  # Keep empty for SMS
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            print(f"✓ SMS sent to {phone} via {carrier}")
            return True
        except Exception as e:
            print(f"✗ Failed to send SMS: {e}")
            return False


# Example usage
if __name__ == "__main__":
    # Test notification service
    notifier = NotificationService()
    notifier.test_notifications()
    
    # Example: Send a real alert
    # sms_msg = "🔴 CRITICAL: Line L5 at 102% loading at 5:00 PM"
    # email_subject = "GridGuard CRITICAL Alert"
    # email_html = "<h2>Critical Line Overload Detected</h2><p>Line L5 is predicted to reach 102% loading at 5:00 PM today.</p>"
    # notifier.send_alert(sms_msg, email_subject, email_html)