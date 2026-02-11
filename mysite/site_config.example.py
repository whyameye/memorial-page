# Site Configuration
# Copy this file to site_config.py and customize for your memorial page

# SECURITY SETTINGS - CHANGE THESE IN PRODUCTION!
# Generate a new secret key: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY = "changeme"
DEBUG = True
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']

# Password to access the submission form (share with family/friends)
SUBMISSION_PASSWORD = "changeme"

SITE_TITLE = "Memorial Page"
SITE_SUBTITLE = "In Loving Memory"
SITE_DESCRIPTION = "Add a description here"

# Path to person's photo (relative to static files)
# Place your image in static/dist/images/ and reference it here
PERSON_IMAGE = "images/person.png"

# If True, submissions must be approved in admin before appearing
# If False, submissions appear immediately after submit (since form is password protected)
REQUIRE_APPROVAL = False

# Optional: Custom colors (CSS values)
# HEADER_GRADIENT_START = "#667eea"
# HEADER_GRADIENT_END = "#764ba2"

# Optional: Fixed background image (doesn't scroll with content)
# Place image in static/dist/images/ and reference it here
# BACKGROUND_IMAGE = "images/background.jpg"

# Theme: "default", "clean-minimal", or "warm-elegant"
THEME = "default"

# Footer text (supports HTML)
FOOTER_TEXT = "Photo uploads and texts by their respective authors."

# Contact email (displayed in footer, obfuscated against spam bots)
# CONTACT_EMAIL = "someone@example.com"
# CONTACT_PROMPT = "Questions?"


# Optional: Override server timezone (auto-detected by default)
# TIME_ZONE = "America/New_York"

# Optional: Donation text in footer (supports HTML for links)
# DONATION_TEXT = 'In lieu of flowers, please consider a <a href="https://example.com" target="_blank">donation to Example Charity</a>'

# Email notification when someone submits (no email sent if not set)
# NOTIFICATION_EMAIL = "you@example.com"
# NOTIFICATION_FROM = "memorial@example.com"
# SENDMAIL_COMMAND = "/usr/sbin/sendmail"  # or path to custom sendmail wrapper
