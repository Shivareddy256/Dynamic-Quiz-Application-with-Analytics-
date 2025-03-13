import os

class Config:
    SECRET_KEY = "your_secret_key"
    
    # MySQL Database Configuration
    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:Reddy%400108@localhost/dynamic_quiz"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Configurations for password reset and verification
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = 'youremail@gmail.com'  # Your email address
    MAIL_PASSWORD = 'yourpassword'        # App-specific password from Google
