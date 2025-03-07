from fastapi import APIRouter
from email.message import EmailMessage
import ssl
import smtplib
import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

load_dotenv()

# PASSWORD = os.environ.get('MAIL_PASSWORD')
# EMAIL = os.environ.get('MAIL_SENDER')

PASSWORD = "ngtlatwsrywvauwh"
EMAIL = "heangs770@gmail.com"

# def send_mail(email_receiver: str, subject: str, message: str):
#     em = EmailMessage()
#     em['From'] = EMAIL
#     em['To'] = email_receiver
#     em['Subject'] = subject
#     em.set_content(message)
    
#     context = ssl.create_default_context()
    
#     with smtplib.SMTP_SSL('smtp.gmail.com', '465', context=context) as smtp :
#         smtp.login(EMAIL, PASSWORD)
#         smtp.sendmail(EMAIL, email_receiver, em.as_string())

def send_mail(email_receiver: str, subject: str, message: str):
    try:
        message = MIMEText(message,'plain')
        message["From"] = EMAIL
        message["To"] = email_receiver
        message["Subject"] = subject
        
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(EMAIL, PASSWORD)
            server.sendmail(EMAIL, email_receiver, message.as_string())
    except Exception as e:
        raise e