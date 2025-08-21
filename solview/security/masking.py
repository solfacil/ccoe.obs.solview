"""
Enhanced Data Masking for Solview.

Extended pattern matching for:
- Credit cards, bank accounts
- API keys, tokens, passwords
- IP addresses (optional)
- Custom sensitive patterns
- GDPR/LGPD compliance patterns
"""

import re
import hashlib
from typing import Any, Dict, List, Union, Pattern
from dataclasses import dataclass

@dataclass
class MaskingRule:
    """Configuration for a masking rule."""
    name: str
    pattern: Union[str, Pattern]
    replacement: str
    description: str = ""
    enabled: bool = True
    compliance: List[str] = None  # GDPR, LGPD, PCI-DSS, etc.

class EnhancedDataMasking:
    """Enhanced data masking with enterprise compliance patterns."""
    
    def __init__(self, enable_all: bool = True):
        self.rules: Dict[str, MaskingRule] = {}
        self.enable_all = enable_all
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default masking rules."""
        
        # Brazilian Documents (existing)
        self.add_rule(MaskingRule(
            name="cpf",
            pattern=r"\b(\d{3})\d{6}(\d{2})\b",
            replacement=r"\1.XXX.XXX-\2",
            description="Brazilian CPF masking",
            compliance=["LGPD"]
        ))
        
        self.add_rule(MaskingRule(
            name="cpf_formatted",
            pattern=r"\b(\d{3})\.\d{3}\.\d{3}-(\d{2})\b",
            replacement=r"\1.XXX.XXX-\2",
            description="Brazilian CPF formatted masking",
            compliance=["LGPD"]
        ))
        
        self.add_rule(MaskingRule(
            name="cnpj",
            pattern=r"\b(\d{2})\d{10}(\d{2})\b",
            replacement=r"\1.XXX.XXX/XXXX-\2",
            description="Brazilian CNPJ masking",
            compliance=["LGPD"]
        ))
        
        # Credit Cards (PCI-DSS)
        self.add_rule(MaskingRule(
            name="credit_card",
            pattern=r"\b(\d{4})\s?-?\s?(\d{4})\s?-?\s?(\d{4})\s?-?\s?(\d{4})\b",
            replacement=r"\1-XXXX-XXXX-\4",
            description="Credit card masking (PCI-DSS)",
            compliance=["PCI-DSS"]
        ))
        
        # API Keys and Tokens
        self.add_rule(MaskingRule(
            name="api_key_bearer",
            pattern=r"(Bearer\s+)([A-Za-z0-9\-_]{10,})",
            replacement=r"\1***MASKED***",
            description="Bearer token masking"
        ))
        
        self.add_rule(MaskingRule(
            name="api_key_basic",
            pattern=r"(Basic\s+)([A-Za-z0-9+/]{10,}={0,2})",
            replacement=r"\1***MASKED***",
            description="Basic auth token masking"
        ))
        
        self.add_rule(MaskingRule(
            name="jwt_token",
            pattern=r"\b(eyJ[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,}\.[A-Za-z0-9\-_]{10,})\b",
            replacement="***JWT_TOKEN_MASKED***",
            description="JWT token masking"
        ))
        
        # Passwords
        self.add_rule(MaskingRule(
            name="password_field",
            pattern=r'("password"\s*:\s*")([^"]+)(")',
            replacement=r'\1***MASKED***\3',
            description="Password field in JSON"
        ))
        
        self.add_rule(MaskingRule(
            name="password_query",
            pattern=r'([?&]password=)([^&\s]+)',
            replacement=r'\1***MASKED***',
            description="Password in query string"
        ))
        
        # Email (GDPR/LGPD compliant)
        self.add_rule(MaskingRule(
            name="email",
            pattern=r"\b(\w{1,2})[^@]*(@[\w\.-]+)\b",
            replacement=r"\1***\2",
            description="Email masking (GDPR/LGPD)",
            compliance=["GDPR", "LGPD"]
        ))
        
        # Phone numbers (enhanced)
        self.add_rule(MaskingRule(
            name="phone_br",
            pattern=r"\b(\d{2})\d{4,5}(\d{4})\b",
            replacement=r"\1*****\2",
            description="Brazilian phone masking",
            compliance=["LGPD"]
        ))
        
        self.add_rule(MaskingRule(
            name="phone_international",
            pattern=r"\+(\d{1,3})\s?(\d{2,3})\s?\d{6,8}",
            replacement=r"+\1 \2 ******",
            description="International phone masking"
        ))
        
        # IP Addresses (optional - for privacy)
        self.add_rule(MaskingRule(
            name="ipv4",
            pattern=r"\b(\d{1,3}\.\d{1,3})\.\d{1,3}\.\d{1,3}\b",
            replacement=r"\1.XXX.XXX",
            description="IPv4 address masking",
            enabled=False  # Disabled by default
        ))
        
        # Bank Account Numbers
        self.add_rule(MaskingRule(
            name="bank_account",
            pattern=r"\b(\d{4,6})-(\d)(\d{6,12})-(\d)\b",
            replacement=r"\1-\2XXXXXX-\4",
            description="Bank account masking",
            compliance=["PCI-DSS", "LGPD"]
        ))
        
        # Social Security Numbers (US)
        self.add_rule(MaskingRule(
            name="ssn",
            pattern=r"\b(\d{3})-?(\d{2})-?(\d{4})\b",
            replacement=r"\1-XX-\3",
            description="US SSN masking",
            compliance=["GDPR"]
        ))
        
        # Custom sensitive patterns
        self.add_rule(MaskingRule(
            name="secret_key",
            pattern=r'("(?:secret|key|token|password)"\s*:\s*")([^"]+)(")',
            replacement=r'\1***MASKED***\3',
            description="Generic secret fields in JSON"
        ))
    
    def add_rule(self, rule: MaskingRule):
        """Add a custom masking rule."""
        self.rules[rule.name] = rule
    
    def remove_rule(self, rule_name: str):
        """Remove a masking rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]
    
    def enable_rule(self, rule_name: str):
        """Enable a specific rule."""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = True
    
    def disable_rule(self, rule_name: str):
        """Disable a specific rule."""
        if rule_name in self.rules:
            self.rules[rule_name].enabled = False
    
    def mask_text(self, text: Union[str, Any]) -> Union[str, Any]:
        """Apply all enabled masking rules to text."""
        if not isinstance(text, str):
            return text
        
        masked_text = text
        applied_rules = []
        
        for rule_name, rule in self.rules.items():
            if not rule.enabled:
                continue
                
            try:
                if isinstance(rule.pattern, str):
                    pattern = re.compile(rule.pattern)
                else:
                    pattern = rule.pattern
                
                if pattern.search(masked_text):
                    masked_text = pattern.sub(rule.replacement, masked_text)
                    applied_rules.append(rule_name)
                    
            except Exception as e:
                # Log error but continue with other rules
                import logging
                logger = logging.getLogger("solview.security.masking")
                logger.error(f"Error applying masking rule '{rule_name}': {e}")
        
        return masked_text
    
    def mask_dict(self, data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """Recursively mask sensitive data in dictionary."""
        if not isinstance(data, dict):
            return data
        
        masked_data = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                # Apply masking to string values
                masked_data[key] = self.mask_text(value)
            elif isinstance(value, dict) and deep:
                # Recursively mask nested dictionaries
                masked_data[key] = self.mask_dict(value, deep=deep)
            elif isinstance(value, list) and deep:
                # Mask items in lists
                masked_data[key] = [
                    self.mask_dict(item, deep=deep) if isinstance(item, dict)
                    else self.mask_text(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data
    
    def get_compliance_rules(self, compliance_standard: str) -> List[str]:
        """Get rules that apply to a specific compliance standard."""
        return [
            rule_name for rule_name, rule in self.rules.items()
            if rule.compliance and compliance_standard in rule.compliance
        ]
    
    def validate_compliance(self, text: str, compliance_standards: List[str]) -> Dict[str, bool]:
        """Check if text complies with masking requirements."""
        results = {}
        
        for standard in compliance_standards:
            compliant = True
            rules = self.get_compliance_rules(standard)
            
            for rule_name in rules:
                rule = self.rules[rule_name]
                if rule.enabled:
                    pattern = re.compile(rule.pattern) if isinstance(rule.pattern, str) else rule.pattern
                    if pattern.search(text):
                        compliant = False
                        break
            
            results[standard] = compliant
        
        return results
    
    def generate_hash_id(self, sensitive_data: str, salt: str = "") -> str:
        """Generate a deterministic hash for sensitive data (for correlation without exposure)."""
        hasher = hashlib.sha256()
        hasher.update(f"{sensitive_data}{salt}".encode('utf-8'))
        return hasher.hexdigest()[:12]  # Return first 12 chars for brevity

# Global enhanced masking instance
enhanced_masking = EnhancedDataMasking()

# Convenience functions for backward compatibility
def mask_sensitive_data(text: Union[str, Any]) -> Union[str, Any]:
    """Enhanced version of the original mask_sensitive_data function."""
    return enhanced_masking.mask_text(text)

def mask_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhanced version of the original mask_dict function."""
    return enhanced_masking.mask_dict(data)
