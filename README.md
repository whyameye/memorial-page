# Memorial Page

A simple, customizable online memorial/condolence book that allows communities to share memories and celebrate a loved one.

If you're in a position in which you need this, first of all: I'm sorry. This sucks. Thanks for doing this anyway.

## Features

- Password-protected submissions (keeps spam out while allowing easy access for friends/family)
- Image upload with drag & drop (dropzone.js)
- Video and link embedding (YouTube, Vimeo auto-embed)
- No account required for submitters (session-based)
- Optional moderation/approval workflow
- Private "message to the family" field (not published)
- Configurable site title, subtitle, colors, and background image
- Three design themes available (see Branches below)
- Mobile responsive (Bootstrap 5)

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set up the database
./manage.py migrate

# Collect static files
./manage.py collectstatic --noinput

# Create admin user
./manage.py createsuperuser

# Run development server
./manage.py runserver
```

Visit `http://localhost:8000` to see the site.

## Configuration

Copy `mysite/site_config.example.py` to `mysite/site_config.py` and customize:

```python
# SECURITY - Change these for production!
SECRET_KEY = "generate-a-new-key-see-below"
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Site content
SITE_TITLE = "Remembering John"
SITE_SUBTITLE = "1950 - 2024"
SITE_DESCRIPTION = "Share your favorite memories"

# Person's photo (place in static/dist/images/)
PERSON_IMAGE = "images/john.jpg"

# Password for submission form
# Set via environment variable: export SUBMISSION_PASSWORD="secret"
# Or set in site_config.py (not recommended for production)

# Optional: Require admin approval before submissions appear
REQUIRE_APPROVAL = False  # True = must approve in admin, False = appears immediately

# Optional: Fixed background image
BACKGROUND_IMAGE = "images/background.jpg"

# Optional: Custom header colors (default theme only)
HEADER_GRADIENT_START = "#667eea"
HEADER_GRADIENT_END = "#764ba2"

# Theme: "default", "clean-minimal", or "warm-elegant"
THEME = "default"
```

### Generating a Secret Key

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### Setting the Submission Password

```bash
export SUBMISSION_PASSWORD="your-secret-password"
```

Or add to `site_config.py` (note: this file is gitignored for security).

## Design Themes

Three themes are available, configured via `THEME` in `site_config.py`:

- `default` - Simple Bootstrap 5 with purple gradient header (customizable colors)
- `clean-minimal` - White background, Inter font, minimal shadows
- `warm-elegant` - Cream tones, Playfair Display serif headings

Set theme in `site_config.py`:
```python
THEME = "warm-elegant"  # or "clean-minimal", or "default"
```

## Administration

### Creating an Admin User

```bash
./manage.py createsuperuser
```

### Moderating Submissions

Visit `/admin/submissions/submission/` to:
- View all submissions
- Approve pending submissions (if REQUIRE_APPROVAL = True)
- Delete inappropriate content

### Approving Submissions

If `REQUIRE_APPROVAL = True`, submissions won't appear until approved:
1. Go to `/admin/submissions/submission/`
2. Click on a submission
3. Click "Approve" button

## Adding Images

Place images in `static/dist/images/` then run:

```bash
./manage.py collectstatic --noinput
```

Reference them in `site_config.py`:
```python
PERSON_IMAGE = "images/person.jpg"
BACKGROUND_IMAGE = "images/background.jpg"
```

## Production Deployment

1. **Update `site_config.py`:**
   ```python
   SECRET_KEY = "your-generated-secret-key"
   DEBUG = False
   ALLOWED_HOSTS = ['yourdomain.com']
   ```

2. **Set submission password:**
   ```bash
   export SUBMISSION_PASSWORD="share-this-with-family"
   ```

3. **Use a production database** (PostgreSQL recommended):
   ```python
   # In settings.py or site_config.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'memorial',
           'USER': 'dbuser',
           'PASSWORD': 'dbpass',
           'HOST': 'localhost',
       }
   }
   ```

4. **Collect static files:**
   ```bash
   ./manage.py collectstatic --noinput
   ```

5. **Run with gunicorn:**
   ```bash
   gunicorn mysite.wsgi:application
   ```

## File Structure

```
mysite/
  site_config.py          # Your configuration (gitignored)
  site_config.example.py  # Template for configuration
  settings.py             # Django settings (reads from site_config)
  templates/              # HTML templates
static/
  dist/images/            # Place your images here
submissions/              # Submission app
```

## Customizing Templates

Templates are in `mysite/templates/`. Key files:
- `_person_header.html` - Header with photo and title
- `theme_bootstrap/base.html` - Base layout and styles
- `submissions/submission_list.html` - Homepage listing
- `submissions/submission_form.html` - Submission form

## Legacy: Asset Compilation

If you need to modify the original LESS/JS assets:

```bash
npm install
npm run-script build
```

See `static/STATIC_README.md` for details. (Note: Bootstrap is now loaded from CDN, so this is only needed for custom JS/CSS.)
