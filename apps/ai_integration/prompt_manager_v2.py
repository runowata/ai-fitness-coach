"""
Enhanced PromptManager v2 with versioning and schema validation support
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple


logger = logging.getLogger(__name__)

Configuration - with Django settings fallback
def get_prompts_profile():
    try:
        from django.conf import settings
        return getattr(settings, 'PROMPTS_PROFILE', 'v2')
    except ImportError:
        return os.getenv('PROMPTS_PROFILE', 'v2')

PROMPTS_PROFILE = get_prompts_profile()
BASE_DIR = Path(__file__).resolve().parents[2]
PROMPTS_DIR = BASE_DIR / 'prompts' / PROMPTS_PROFILE
INTRO_PATH = PROMPTS_DIR / '_intro.txt'
SCHEMAS_DIR = PROMPTS_DIR / 'schemas'

Default archetype mapping
DEFAULT_ARCHETYPE_ALIASES = {
    'bro': 'peer',
    'sergeant': 'professional',
    'intellectual': 'mentor'
}


class PromptManagerV2:
    """
    Enhanced PromptManager with support for:
    - Versioned prompts (v1, v2)  
    - JSON schema validation
    - Automatic intro injection
    - Archetype normalization
    """
    
    def __init__(self, profile: str = None):
        self.profile = profile or get_prompts_profile()
        self.prompts_dir = BASE_DIR / 'prompts' / self.profile
        self.intro_path = self.prompts_dir / '_intro.txt'
        self.schemas_dir = self.prompts_dir / 'schemas'
        
    @staticmethod
    def normalize_archetype(slug: Optional[str]) -> Optional[str]:
        """
        Normalize archetype from old to new naming convention
        
        Args:
            slug: Original archetype slug (bro/sergeant/intellectual)
            
        Returns:
            Normalized archetype (peer/professional/mentor)
        """
        if not slug:
            return slug
            
        # Lazy load settings to avoid Django initialization issues in tests
        try:
            from django.conf import settings
            aliases = getattr(settings, 'ARCHETYPE_ALIASES', DEFAULT_ARCHETYPE_ALIASES)
        except:
            aliases = DEFAULT_ARCHETYPE_ALIASES
            
        return aliases.get(slug, slug)
    
    def _read_file(self, path: Path) -> str:
        """Safely read text file with UTF-8 encoding"""
        try:
            return path.read_text(encoding='utf-8') if path.exists() else ''
        except Exception as e:
            logger.error(f"Error reading file {path}: {e}")
            return ''
    
    def get_system_prompt(self, kind: str, archetype: Optional[str] = None) -> str:
        """
        Get system prompt for specified kind and archetype
        
        Args:
            kind: Prompt type (master, onboarding, weekly_adaptation)
            archetype: Trainer archetype (mentor, professional, peer)
            
        Returns:
            System prompt text
        """
        if archetype:
            path = self.prompts_dir / 'system' / f"{kind}_{archetype}.system.md"
        else:
            path = self.prompts_dir / 'system' / f"{kind}.system.md"
            
        return self._read_file(path)
    
    def get_user_prompt(self, kind: str, archetype: Optional[str] = None) -> str:
        """
        Get user prompt for specified kind and archetype
        
        Args:
            kind: Prompt type (master, onboarding, weekly_adaptation)  
            archetype: Trainer archetype (mentor, professional, peer)
            
        Returns:
            User prompt text
        """
        if archetype:
            path = self.prompts_dir / 'user' / f"{kind}_{archetype}.user.md"
        else:
            path = self.prompts_dir / 'user' / f"{kind}.user.md"
            
        return self._read_file(path)
    
    def render_with_intro(self, system_text: str, user_text: str) -> Tuple[str, str]:
        """
        Prepend intro text to both system and user prompts
        
        Args:
            system_text: System prompt
            user_text: User prompt
            
        Returns:
            Tuple of (system_with_intro, user_with_intro)
        """
        intro = self._read_file(self.intro_path)
        
        if intro:
            system_with_intro = f"{intro}\n\n{system_text}".strip()
            user_with_intro = f"{intro}\n\n{user_text}".strip()
        else:
            system_with_intro = system_text
            user_with_intro = user_text
            
        return system_with_intro, user_with_intro
    
    def load_schema(self, name: str) -> Dict[str, Any]:
        """
        Load JSON schema for validation
        
        Args:
            name: Schema name (without .json extension)
            
        Returns:
            Parsed JSON schema
            
        Raises:
            FileNotFoundError: If schema file doesn't exist
            json.JSONDecodeError: If schema is invalid JSON
        """
        schema_path = self.schemas_dir / f"{name}.json"
        
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema not found: {schema_path}")
            
        try:
            return json.loads(schema_path.read_text(encoding='utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON schema {schema_path}: {e}")
            raise
    
    def validate_response(self, data: Dict[str, Any], schema_name: str) -> bool:
        """
        Validate AI response against JSON schema
        
        Args:
            data: Response data to validate
            schema_name: Schema name to validate against
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            FileNotFoundError: If schema file not found
        """
        try:
            from jsonschema import validate
            schema = self.load_schema(schema_name)
            validate(instance=data, schema=schema)
            return True
        except FileNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Validation error for {schema_name}: {e}")
            return False
    
    def find_placeholders(self, text: str) -> Set[str]:
        """
        Find all placeholders in text (format: {{variable_name}})
        
        Args:
            text: Text to search
            
        Returns:
            Set of placeholder names
        """
        return set(re.findall(r'\{\{(\w+)\}\}', text))
    
    def assert_placeholders_filled(self, text: str, provided_vars: Dict[str, Any]) -> List[str]:
        """
        Check for unfilled placeholders and return missing variables
        
        Args:
            text: Rendered text to check
            provided_vars: Variables that were provided
            
        Returns:
            List of missing variable names
        """
        placeholders = self.find_placeholders(text)
        missing = []
        
        for placeholder in placeholders:
            if placeholder not in provided_vars:
                missing.append(placeholder)
                
        if missing:
            logger.warning(f"Missing placeholders: {missing}")
            
        return missing
    
    def redact_for_logs(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact/mask PII in payload for safe logging
        
        Args:
            payload: Original payload
            
        Returns:
            Redacted payload safe for logs
        """
        # Create a copy to avoid modifying original
        safe_payload = payload.copy()
        
        # Fields to redact (add more as needed)
        pii_fields = {'email', 'phone', 'full_name', 'address', 'birth_date'}
        
        for field in pii_fields:
            if field in safe_payload:
                value = str(safe_payload[field])
                if len(value) > 3:
                    safe_payload[field] = value[:2] + '*' * (len(value) - 2)
                else:
                    safe_payload[field] = '*' * len(value)
                    
        return safe_payload
    
    def dry_run(self, kind: str, archetype: Optional[str], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dry run prompt rendering without actual AI call
        
        Args:
            kind: Prompt type
            archetype: Trainer archetype
            user_data: User data for template rendering
            
        Returns:
            Dict with render results and validation info
        """
        try:
            system, user = self.get_prompt_pair(kind, archetype)
            
            # Try to render user prompt with provided data
            rendered_user = user.format(**user_data)
            
            # Check for missing placeholders
            missing = self.assert_placeholders_filled(rendered_user, user_data)
            
            return {
                'success': True,
                'system_length': len(system),
                'user_length': len(user),
                'rendered_user_length': len(rendered_user),
                'missing_placeholders': missing,
                'placeholders_found': list(self.find_placeholders(user)),
                'safe_payload': self.redact_for_logs(user_data)
            }
            
        except Exception as e:
            logger.error(f"Dry run failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': e.__class__.__name__
            }

    def get_prompt_pair(self, kind: str, archetype: Optional[str] = None, 
                       with_intro: bool = True) -> Tuple[str, str]:
        """
        Get complete system+user prompt pair
        
        Args:
            kind: Prompt type
            archetype: Trainer archetype  
            with_intro: Whether to include intro text
            
        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # Normalize archetype
        norm_archetype = self.normalize_archetype(archetype)
        
        # Get prompts
        system = self.get_system_prompt(kind, norm_archetype)
        user = self.get_user_prompt(kind, norm_archetype)
        
        # Add intro if requested
        if with_intro:
            system, user = self.render_with_intro(system, user)
            
        return system, user


Convenience instance for backward compatibility
prompt_manager = PromptManagerV2()

Convenience functions
def get_system_prompt(kind: str, archetype: Optional[str] = None) -> str:
    return prompt_manager.get_system_prompt(kind, archetype)

def get_user_prompt(kind: str, archetype: Optional[str] = None) -> str:
    return prompt_manager.get_user_prompt(kind, archetype)

def render_with_intro(system_text: str, user_text: str) -> Tuple[str, str]:
    return prompt_manager.render_with_intro(system_text, user_text)

def normalize_archetype(slug: Optional[str]) -> Optional[str]:
    return PromptManagerV2.normalize_archetype(slug)

def load_schema(name: str) -> Dict[str, Any]:
    return prompt_manager.load_schema(name)

