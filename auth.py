"""
Minimal HTTP Basic Auth -- deliberately simple, not a real user system.
Good enough to stop a random link-clicker from seeing incident data;
not good enough for multiple real users with different permissions.
That's a v2 problem, once there's more than one person using this.

Set PRAHARI_USER and PRAHARI_PASSWORD as environment variables on
whatever host you deploy to. If you don't, it falls back to
admin / changeme locally and prints a loud warning so you don't
accidentally ship the default.
"""

import os
import secrets
import sys

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()

PRAHARI_USER = os.environ.get("PRAHARI_USER", "admin")
PRAHARI_PASSWORD = os.environ.get("PRAHARI_PASSWORD", "changeme")

if PRAHARI_PASSWORD == "changeme":
    print(
        "\n"
        "!! WARNING: PRAHARI_PASSWORD is not set -- using the default "
        "'changeme'. Set PRAHARI_USER / PRAHARI_PASSWORD as environment "
        "variables before deploying anywhere reachable from the internet.\n",
        file=sys.stderr,
    )


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    correct_username = secrets.compare_digest(credentials.username, PRAHARI_USER)
    correct_password = secrets.compare_digest(credentials.password, PRAHARI_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
