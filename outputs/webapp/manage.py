import os, sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR.parent))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ml_site.settings")
from django.core.management import execute_from_command_line
execute_from_command_line(sys.argv)
