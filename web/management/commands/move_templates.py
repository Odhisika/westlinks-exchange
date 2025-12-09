import os
import shutil
from pathlib import Path
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Copy all HTML templates from frontend/ into cvp_django/templates/'

    def handle(self, *args, **kwargs):
        project_root = Path(__file__).resolve().parents[3]
        frontend_dir = project_root / 'frontend'
        templates_dir = project_root / 'cvp_django' / 'templates'
        templates_dir.mkdir(parents=True, exist_ok=True)

        if not frontend_dir.exists():
            self.stdout.write(self.style.ERROR(f'Frontend directory not found: {frontend_dir}'))
            return

        count = 0
        for src in frontend_dir.glob('*.html'):
            dst = templates_dir / src.name
            shutil.copy2(src, dst)
            count += 1
            self.stdout.write(self.style.SUCCESS(f'Copied {src.name}'))

        self.stdout.write(self.style.SUCCESS(f'Total templates copied: {count}'))