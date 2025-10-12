from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
import logging

logger = logging.getLogger("payments")


def send_payment_success_email(order):
    """Send email notification for successful payment"""
    try:
        subject = f"Payment Successful - Order #{order.id}"
        
        # Prepare context for email template
        context = {
            'order': order,
            'plan': order.plan,
            'workspace_id': order.workspace_id,
            'amount': order.amount,
            'transaction_id': order.paytabs_transaction_id,
        }
        
        # Render HTML email
        html_message = render_to_string('payments/emails/payment_success.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email to customer
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.owner_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Send notification to admin
        admin_subject = f"New Payment Received - Order #{order.id}"
        admin_html_message = render_to_string('payments/emails/admin_payment_notification.html', context)
        admin_plain_message = strip_tags(admin_html_message)
        
        send_mail(
            subject=admin_subject,
            message=admin_plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=admin_html_message,
            fail_silently=False,
        )
        
        logger.info(f"Payment success emails sent for order #{order.id}")
        
    except Exception as e:
        logger.error(f"Failed to send payment success email for order #{order.id}: {str(e)}")


def send_payment_failed_email(order):
    """Send email notification for failed payment"""
    try:
        subject = f"Payment Failed - Order #{order.id}"
        
        context = {
            'order': order,
            'plan': order.plan,
            'workspace_id': order.workspace_id,
            'amount': order.amount,
            'transaction_id': order.paytabs_transaction_id,
        }
        
        html_message = render_to_string('payments/emails/payment_failed.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.owner_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Payment failed email sent for order #{order.id}")
        
    except Exception as e:
        logger.error(f"Failed to send payment failed email for order #{order.id}: {str(e)}")


def send_subscription_cancelled_email(owner_email, workspace_id):
    """Send email notification for subscription cancellation"""
    try:
        subject = "Subscription Cancelled"
        
        context = {
            'owner_email': owner_email,
            'workspace_id': workspace_id,
        }
        
        html_message = render_to_string('payments/emails/subscription_cancelled.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[owner_email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Send notification to admin
        admin_subject = f"Subscription Cancelled - Workspace {workspace_id}"
        admin_html_message = render_to_string('payments/emails/admin_subscription_cancelled.html', context)
        admin_plain_message = strip_tags(admin_html_message)
        
        send_mail(
            subject=admin_subject,
            message=admin_plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=admin_html_message,
            fail_silently=False,
        )
        
        logger.info(f"Subscription cancelled emails sent for workspace {workspace_id}")
        
    except Exception as e:
        logger.error(f"Failed to send subscription cancelled email for workspace {workspace_id}: {str(e)}")


def send_new_order_email(order):
    """Send email notification for new order creation"""
    try:
        subject = f"New Order Created - Order #{order.id}"
        
        context = {
            'order': order,
            'plan': order.plan,
            'workspace_id': order.workspace_id,
            'amount': order.amount,
        }
        
        html_message = render_to_string('payments/emails/new_order.html', context)
        plain_message = strip_tags(html_message)
        
        # Send to admin only
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_EMAIL],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"New order email sent for order #{order.id}")
        
    except Exception as e:
        logger.error(f"Failed to send new order email for order #{order.id}: {str(e)}")
