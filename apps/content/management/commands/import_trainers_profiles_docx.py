"""
Import trainer personas from DOCX files
"""
import re
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.content.models import TrainerPersona

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


# Mapping of sections in DOCX to our archetypes
PERSONA_MAPPING = {
    'mentor': [
        'мудрый наставник',
        'наставник', 
        'mentor',
        'wise mentor'
    ],
    'professional': [
        'успешный профессионал',
        'профессионал',
        'professional',
        'successful professional'
    ],
    'peer': [
        'близкий по духу ровесник',
        'ровесник',
        'peer',
        'close peer'
    ]
}


class Command(BaseCommand):
    help = 'Import trainer personas from DOCX file into TrainerPersona model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--docx',
            required=True,
            help='Path to DOCX file with trainer personas'
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
            personas = self._extract_personas(doc)
            
            if options['dry_run']:
                self._show_dry_run(personas)
            else:
                self._save_personas(personas)
                
        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Error processing DOCX: {e}'))

    def _extract_personas(self, doc):
        """Extract persona information from DOCX"""
        # Get all text content
        full_text = '\n'.join([p.text for p in doc.paragraphs if p.text.strip()])
        text_lower = full_text.lower()
        
        personas = {}
        
        for archetype, keywords in PERSONA_MAPPING.items():
            persona_text = self._find_persona_section(text_lower, full_text, keywords)
            if persona_text:
                title, description, tone_guidelines = self._parse_persona_content(persona_text)
                personas[archetype] = {
                    'slug': archetype,
                    'archetype': archetype,
                    'title': title or keywords[0].title(),
                    'description': description,
                    'tone_guidelines': tone_guidelines,
                    'motivational_style': '',  # Could be extracted if present in DOCX
                    'display_order': list(PERSONA_MAPPING.keys()).index(archetype)
                }
        
        return personas

    def _find_persona_section(self, text_lower, full_text, keywords):
        """Find section for specific persona"""
        start_pos = -1
        matched_keyword = None
        
        # Find the start position of this persona section
        for keyword in keywords:
            pos = text_lower.find(keyword.lower())
            if pos != -1:
                start_pos = pos
                matched_keyword = keyword
                break
        
        if start_pos == -1:
            return None
        
        # Find end position (start of next persona section)
        end_pos = len(full_text)
        
        for other_archetype, other_keywords in PERSONA_MAPPING.items():
            for other_keyword in other_keywords:
                other_pos = text_lower.find(other_keyword.lower(), start_pos + 1)
                if other_pos != -1 and other_pos < end_pos:
                    end_pos = other_pos
        
        return full_text[start_pos:end_pos].strip()

    def _parse_persona_content(self, content):
        """Parse persona content into structured data"""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            return '', '', ''
        
        # First line is usually the title
        title = lines[0]
        
        # Look for specific sections
        description_lines = []
        tone_lines = []
        current_section = 'description'
        
        for line in lines[1:]:
            line_lower = line.lower()
            
            # Check if this line indicates a new section
            if any(keyword in line_lower for keyword in ['тон:', 'стиль:', 'подход:', 'tone:', 'style:']):
                current_section = 'tone'
                tone_lines.append(line)
            elif any(keyword in line_lower for keyword in ['описание:', 'description:']):
                current_section = 'description'
            else:
                if current_section == 'description':
                    description_lines.append(line)
                elif current_section == 'tone':
                    tone_lines.append(line)
        
        description = '\n'.join(description_lines).strip()
        tone_guidelines = '\n'.join(tone_lines).strip()
        
        return title, description, tone_guidelines

    def _show_dry_run(self, personas):
        """Show what would be imported"""
        self.stdout.write(self.style.WARNING('DRY RUN - Trainer Personas:'))
        self.stdout.write('-' * 50)
        
        for archetype, data in personas.items():
            self.stdout.write(f'\n{archetype.upper()}:')
            self.stdout.write(f'  Title: {data["title"]}')
            self.stdout.write(f'  Description: {data["description"][:100]}...')
            self.stdout.write(f'  Tone Guidelines: {data["tone_guidelines"][:100]}...')

    def _save_personas(self, personas):
        """Save personas to database"""
        created_count = 0
        updated_count = 0
        
        for archetype, data in personas.items():
            obj, created = TrainerPersona.objects.update_or_create(
                slug=archetype,
                defaults=data
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
                
        self.stdout.write(
            self.style.SUCCESS(
                f'TrainerPersona: {created_count} created, {updated_count} updated'
            )
        )