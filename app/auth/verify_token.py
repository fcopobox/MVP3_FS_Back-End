import json
import requests
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError

AUTH0_DOMAIN = "dev-03m4as7kh6yeyoi1.us.auth0.com"
AUTH0_AUDIENCE = "https://weathermap-api"
ALGORITHMS = ["RS256"]

JWKS_URL = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
ISSUER = f"https://{AUTH0_DOMAIN}/"

_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        response = requests.get(JWKS_URL)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache

def verify_token(token: str):
    jwks = get_jwks()
    unverified_header = jwt.get_unverified_header(token)

    if "kid" not in unverified_header:
        raise JWTError("Token inválido: 'kid' ausente no header.")

    kid = unverified_header["kid"]

    rsa_key = {}
    for key in jwks["keys"]:
        if key["kid"] == kid:
            rsa_key = {
                "kty": key["kty"],
                "kid": key["kid"],
                "use": key["use"],
                "n": key["n"],
                "e": key["e"],
            }
            break

    if not rsa_key:
        raise JWTError("Chave pública correspondente ao 'kid' não encontrada.")

    try:
        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=ALGORITHMS,
            audience=AUTH0_AUDIENCE,
            issuer=ISSUER,
        )
        return payload

    except ExpiredSignatureError:
        raise JWTError("Token expirado.")

    except JWTError as e:
        raise JWTError(f"Token inválido: {str(e)}")
