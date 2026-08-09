#!/bin/python3

import os


class reCAPTCHAv3:
    site_key = os.environ.get("RECAPTCHA_SITE_KEY", "")
    secret_key = os.environ.get("RECAPTCHA_SECRET_KEY", "")
