from fastapi import APIRouter
from email.message import EmailMessage
import ssl
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

PASSWORD = os.environ.get('MAIL_PASSWORD')
EMAIL = os.environ.get('MAIL_SENDER')

def send_mail(email_receiver: str, subject: str, message: str):
    em = EmailMessage()
    em['From'] = EMAIL
    em['To'] = email_receiver
    em['Subject'] = subject
    em.set_content(message)
    
    context = ssl.create_default_context()
    
    with smtplib.SMTP_SSL('smtp.gmail.com', '465', context=context) as smtp :
        smtp.login(EMAIL, PASSWORD)
        smtp.sendmail(EMAIL, email_receiver, em.as_string())