"""
Configuration management for FLYO agent.
Centralizes all settings and provides easy customization.
"""

import os
from dataclasses import dataclass
from typing import Optional
import json
from pathlib import Path


@dataclass
class OllamaConfig:
    """Ollama LLM configuration"""
    base_url: str = "http://localhost:11434"
    model: str = "qwen2.5-coder:7b"
    temperature: float = 0.1
    timeout: int = 120
    max_retries: int = 3


@dataclass
class BrowserConfig:
    """Browser automation configuration"""
    headless: bool = False
    timeout: int = 30000  # 30 seconds
    viewport_width: int = 1920
    viewport_height: int = 1080
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Performance settings
    disable_images: bool = False  # Set to True to speed up
    disable_javascript: bool = False  # Usually keep False


@dataclass
class CacheConfig:
    """UI cache configuration"""
    enabled: bool = True
    cache_file: str = "ui_cache.json"
    max_entries: int = 100
    max_age_hours: int = 24
    
    # Validation settings
    validate_hash: bool = True  # Check if UI changed
    auto_invalidate_on_error: bool = True


@dataclass
class SecurityConfig:
    """Security and approval settings"""
    require_approval: bool = True
    credentials_file: str = "credentials.json"
    
    # Risky actions that require approval
    risky_actions: list = None
    
    def __post_init__(self):
        if self.risky_actions is None:
            self.risky_actions = [
                "submit_form",
                "proceed_to_checkout",
                "auto_login",
                "delete",
                "confirm_purchase",
                "make_payment"
            ]


@dataclass
class RecoveryConfig:
    """Error recovery configuration"""
    max_self_heal_attempts: int = 2
    retry_delay_seconds: float = 1.0
    
    # When to trigger recovery
    recover_on_timeout: bool = True
    recover_on_selector_error: bool = True
    recover_on_network_error: bool = True
    
    # Fresh UI fetch on recovery
    force_fresh_ui: bool = True
    invalidate_cache_on_error: bool = True


@dataclass
class FlyoConfig:
    """Complete FLYO agent configuration"""
    ollama: OllamaConfig
    browser: BrowserConfig
    cache: CacheConfig
    security: SecurityConfig
    recovery: RecoveryConfig
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_file(cls, config_path: str = "config.json") -> 'FlyoConfig':
        """Load configuration from JSON file"""
        path = Path(config_path)
        
        if not path.exists():
            # Create default config
            config = cls.default()
            config.save(config_path)
            return config
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        return cls(
            ollama=OllamaConfig(**data.get('ollama', {})),
            browser=BrowserConfig(**data.get('browser', {})),
            cache=CacheConfig(**data.get('cache', {})),
            security=SecurityConfig(**data.get('security', {})),
            recovery=RecoveryConfig(**data.get('recovery', {})),
            log_level=data.get('log_level', 'INFO'),
            log_file=data.get('log_file')
        )
    
    @classmethod
    def default(cls) -> 'FlyoConfig':
        """Create default configuration"""
        return cls(
            ollama=OllamaConfig(),
            browser=BrowserConfig(),
            cache=CacheConfig(),
            security=SecurityConfig(),
            recovery=RecoveryConfig()
        )
    
    def save(self, config_path: str = "config.json") -> None:
        """Save configuration to JSON file"""
        data = {
            'ollama': {
                'base_url': self.ollama.base_url,
                'model': self.ollama.model,
                'temperature': self.ollama.temperature,
                'timeout': self.ollama.timeout,
                'max_retries': self.ollama.max_retries
            },
            'browser': {
                'headless': self.browser.headless,
                'timeout': self.browser.timeout,
                'viewport_width': self.browser.viewport_width,
                'viewport_height': self.browser.viewport_height,
                'disable_images': self.browser.disable_images,
                'disable_javascript': self.browser.disable_javascript
            },
            'cache': {
                'enabled': self.cache.enabled,
                'cache_file': self.cache.cache_file,
                'max_entries': self.cache.max_entries,
                'max_age_hours': self.cache.max_age_hours,
                'validate_hash': self.cache.validate_hash,
                'auto_invalidate_on_error': self.cache.auto_invalidate_on_error
            },
            'security': {
                'require_approval': self.security.require_approval,
                'credentials_file': self.security.credentials_file,
                'risky_actions': self.security.risky_actions
            },
            'recovery': {
                'max_self_heal_attempts': self.recovery.max_self_heal_attempts,
                'retry_delay_seconds': self.recovery.retry_delay_seconds,
                'recover_on_timeout': self.recovery.recover_on_timeout,
                'recover_on_selector_error': self.recovery.recover_on_selector_error,
                'recover_on_network_error': self.recovery.recover_on_network_error,
                'force_fresh_ui': self.recovery.force_fresh_ui,
                'invalidate_cache_on_error': self.recovery.invalidate_cache_on_error
            },
            'log_level': self.log_level,
            'log_file': self.log_file
        }
        
        with open(config_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def setup_logging(self) -> None:
        """Configure logging based on settings"""
        import logging
        
        handlers = []
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, self.log_level))
        console_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        handlers.append(console_handler)
        
        # File handler (if specified)
        if self.log_file:
            file_handler = logging.FileHandler(self.log_file)
            file_handler.setLevel(logging.DEBUG)  # Always log everything to file
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            handlers.append(file_handler)
        
        # Configure root logger
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=handlers
        )


# Quick access functions
def load_config(config_path: str = "config.json") -> FlyoConfig:
    """Load configuration from file"""
    return FlyoConfig.from_file(config_path)


def create_default_config(config_path: str = "config.json") -> FlyoConfig:
    """Create and save default configuration"""
    config = FlyoConfig.default()
    config.save(config_path)
    print(f"✓ Created default configuration: {config_path}")
    return config


def print_config(config: FlyoConfig) -> None:
    """Pretty print configuration"""
    print("\n" + "="*70)
    print("FLYO CONFIGURATION")
    print("="*70)
    
    print("\n🤖 Ollama LLM:")
    print(f"   URL: {config.ollama.base_url}")
    print(f"   Model: {config.ollama.model}")
    print(f"   Temperature: {config.ollama.temperature}")
    
    print("\n🌐 Browser:")
    print(f"   Headless: {config.browser.headless}")
    print(f"   Timeout: {config.browser.timeout}ms")
    print(f"   Viewport: {config.browser.viewport_width}x{config.browser.viewport_height}")
    
    print("\n💾 Cache:")
    print(f"   Enabled: {config.cache.enabled}")
    print(f"   File: {config.cache.cache_file}")
    print(f"   Max entries: {config.cache.max_entries}")
    
    print("\n🔒 Security:")
    print(f"   Require approval: {config.security.require_approval}")
    print(f"   Risky actions: {len(config.security.risky_actions)}")
    
    print("\n🔄 Recovery:")
    print(f"   Max heal attempts: {config.recovery.max_self_heal_attempts}")
    print(f"   Force fresh UI: {config.recovery.force_fresh_ui}")
    
    print("="*70 + "\n")


# Example usage
if __name__ == "__main__":
    # Create default config
    config = create_default_config()
    
    # Print it
    print_config(config)
    
    # Customize
    config.ollama.model = "llama3.2:latest"
    config.browser.headless = True
    config.security.require_approval = False
    
    # Save customized config
    config.save("config_custom.json")
    print("✓ Saved customized configuration: config_custom.json")