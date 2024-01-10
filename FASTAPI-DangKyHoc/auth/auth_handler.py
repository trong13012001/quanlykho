import time
from typing import Dict

import jwt
from decouple import config


JWT_SECRET = config("secret")
JWT_ALGORITHM = config("algorithm")
REFRESH_TOKEN_SECRET = config("refresh_token_secret",default="refresh token secret.token_hex(10)")
REFRESH_TOKEN_ALGORITHM = config("refresh_token_algorithm")



def token_response(access_token: str, refresh_token: str):
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }


def signJWT(user_id: str) -> Dict[str, str]:
    access_token_payload = {
        "user_id": user_id,
        "expires": time.time() + 60*60*24
    }
    access_token = jwt.encode(access_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    refresh_token_payload = {
        "user_id": user_id,
        "expires": time.time() +  60*60*24*7
    }
    refresh_token = jwt.encode(refresh_token_payload, REFRESH_TOKEN_SECRET, algorithm=REFRESH_TOKEN_ALGORITHM)

    return token_response(access_token, refresh_token)


def decodeJWT(token: str) -> dict:
    try:
        decoded_token = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return decoded_token if decoded_token["expires"] >= time.time() else None
    except:
        return {}


def refresh_access_token(refresh_token: str) -> Dict[str, str]:
    try:
        decoded_token = jwt.decode(refresh_token, REFRESH_TOKEN_SECRET, algorithms=[REFRESH_TOKEN_ALGORITHM])
        user_id = decoded_token["user_id"]

        # Verify if the refresh token has expired
        if decoded_token["expires"] < time.time():
            return {}

        # Generate a new access token with a new expiration time
        access_token_payload = {
            "user_id": user_id,
            "expires": time.time() + 60*60*24*7
        }
        access_token = jwt.encode(access_token_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        return token_response(access_token, refresh_token)
    except:
        return {}
