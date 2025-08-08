"""
Import landing page content from DOCX files
"""
import re
from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from apps.content.models import LandingContent

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


class Command(BaseCommand):
    help = 'Import landing page content from DOCX file into LandingContent model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--docx', 
            required=True, 
            help='Path to DOCX file with landing content'
        )
        parser.add_argument(
            '--version', 
            default='2.0',
            help='Landing content version (default: 2.0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be imported without saving'
        )

    def handle(self, *args, **options):
        if not DOCX_AVAILABLE:
            self.stderr.write(
                self.style.ERROR('python-docx not available. Install: pip install python-docx')
            )
            return

        docx_path = Path(options['docx'])
        if not docx_path.exists():
            self.stderr.write(self.style.ERROR(f'DOCX file not found: {docx_path}'))
            return

        try:
            doc = Document(str(docx_path))
            content = self._extract_content(doc)
            
            if options['dry_run']:
                self._show_dry_run(content, options['version'])
            else:
                self._save_content(content, options['version'])
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error processing DOCX: {e}'))

    def _extract_content(self, doc):
        """Extract content sections from DOCX"""
        # Get all text paragraphs
        paragraphs = []
        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                paragraphs.append(text)
        
        full_text = '\n'.join(paragraphs)
        
        # Section extraction patterns (adjust to your DOCX structure)
        sections = {
            'hero_title': self._extract_section(
                full_text, 
                patterns=[r'AI Fitness Coach[^\n]*', r'Заголовок[^\n]*'],
                single_line=True
            ),
            'hero_subtitle': self._extract_section(
                full_text,
                patterns=[r'подзаголовок.*?\n(.+)', r'subtitle.*?\n(.+)']
            ),
            'for_whom': self._extract_section(
                full_text,
                patterns=[r'(для кого.*?)(?=как|безопасность|персонализация|$)', 
                         r'(кому подходит.*?)(?=как|безопасность|персонализация|$)']
            ),
            'how_it_works': self._extract_section(
                full_text,
                patterns=[r'(как это работает.*?)(?=безопасность|персонализация|кейсы|$)',
                         r'(как все устроено.*?)(?=безопасность|персонализация|кейсы|$)']
            ),
            'safety': self._extract_section(
                full_text,
                patterns=[r'(безопасность.*?)(?=персонализация|кейсы|cta|$)',
                         r'(приватность.*?)(?=персонализация|кейсы|cta|$)']
            ),
            'personalization': self._extract_section(
                full_text,
                patterns=[r'(персонализация.*?)(?=кейсы|cta|примеры|$)']
            )
        }
        
        return sections

    def _extract_section(self, text, patterns, single_line=False):
        """Extract section using regex patterns"""
        text_lower = text.lower()
        
        for pattern in patterns:
            match = re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            if match:
                result = match.group(1) if match.groups() else match.group(0)
                if single_line:
                    result = result.split('\n')[0]
                return result.strip()
        
        return ''

    def _show_dry_run(self, content, version):
        """Show what would be imported"""
        self.stdout.write(self.style.WARNING(f'DRY RUN - Landing Content v{version}:'))
        self.stdout.write('-' * 50)
        
        total_chars = 0
        empty_fields = []
        
        for field, value in content.items():
            self.stdout.write(f'\n{field.upper()}: ({len(value)} chars)')
            if value:
                self.stdout.write(value[:200] + ('...' if len(value) > 200 else ''))
                total_chars += len(value)
            else:
                empty_fields.append(field)
                self.stdout.write(self.style.ERROR('  [EMPTY]'))
                
        self.stdout.write(f'\nSummary: {total_chars} total characters')
        if empty_fields:
            self.stdout.write(self.style.WARNING(f'Empty fields: {", ".join(empty_fields)}'))
            
    def _save_content(self, content, version):
        """Save content to database"""
        content['version'] = version
        
        obj, created = LandingContent.objects.update_or_create(
            version=version,
            defaults=content
        )
        
        status = 'created' if created else 'updated'
        self.stdout.write(
            self.style.SUCCESS(f'LandingContent v{version} {status} successfully')
        )