import dj_database_url
import os
import sys

# Only add PostgreSQL config if DATABASE_URL is set (Render provides it)
if 'DATABASE_URL' in os.environ:
    DATABASES = {
        'default': dj_database_url.config(
            default=os.environ.get('DATABASE_URL'),
            conn_max_age=600
        )
    }
    print("🗄️ Using PostgreSQL database from DATABASE_URL", file=sys.stderr)
else:
    # Fallback to SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(os.path.dirname(__file__), '../db.sqlite3'),
        }
    }
    print("⚠️ Using SQLite database (DATABASE_URL not found)", file=sys.stderr)
