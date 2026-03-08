import os
from python_jose import JWTError, jwt

class Config:
    def __init__(self):
        self.IOAS_TOKEN = os.getenv('IOAS_TOKEN', '')
        self.IOAS_ENDPOINT = os.getenv('IOAS_ENDPOINT', 'https://api.ioas.io')
        self.JWT_SECRET = os.getenv('JWT_SECRET', 'default_secret')

    def validate_token(self, token):
        try:
            jwt.decode(token, self.JWT_SECRET, algorithms=['HS256'])
            return True
        except JWTError:
            return False