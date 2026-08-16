import os

import requests


SITE_KEY = os.environ.get("TURNSTILE_SITE_KEY", "0x4AAAAAAEROzj3AR98iyioK")
EXPECTED_ACTION = "upload"
VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"


def expected_hostnames():
    return {
        hostname.strip()
        for hostname in os.environ.get("TURNSTILE_HOSTNAMES", "").split(",")
        if hostname.strip()
    }


def verify(token, remote_ip=None):
    if not isinstance(token, str) or not token or len(token) > 2048:
        return False

    hostnames = expected_hostnames()
    secret = os.environ.get("TURNSTILE_SECRET", "")
    if not secret or not hostnames:
        return False

    try:
        response = requests.post(
            VERIFY_URL,
            data={
                "secret": secret,
                "response": token,
                "remoteip": remote_ip or "",
            },
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()
    except (requests.RequestException, ValueError):
        return False

    return (
        result.get("success") is True
        and result.get("action") == EXPECTED_ACTION
        and result.get("hostname") in hostnames
    )