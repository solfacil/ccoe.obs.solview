"""
Data masking utilities for SolView logging.
Provides functionality to mask sensitive data like CPF, CNPJ, phone numbers, and emails.
"""

import re
import json
from typing import Any, Optional
from datetime import datetime, date
from uuid import UUID


class DataMasker:
    """Handles masking of sensitive data in log messages."""
    
    def __init__(self, ignore_mask: bool = False):
        """
        Initialize the DataMasker.
        
        Args:
            ignore_mask: If True, disables masking (useful for debugging)
        """
        self.ignore_mask = ignore_mask
    
    def _convert_to_serializable(self, value: Any) -> Any:
        """
        Convert value to JSON-serializable format.
        
        Args:
            value: Value to convert
            
        Returns:
            Serializable value
        """
        if isinstance(value, UUID):
            return str(value)
        elif isinstance(value, (datetime, date)):
            return value.isoformat()
        elif isinstance(value, set):
            return list(value)
        elif isinstance(value, bytes):
            return value.decode("utf-8", errors="ignore")
        return value
    
    def mask_sensitive_data(self, text: str) -> str:
        """
        Mask sensitive data in text (CPF, CNPJ, phone, email).
        
        Args:
            text: Text to mask
            
        Returns:
            Text with sensitive data masked
        """
        if self.ignore_mask or not isinstance(text, str):
            return text
        
        # CPF - Keep first 3 and last 2 digits
        text = re.sub(r"\b(\d{3})\d{6}(\d{2})\b", r"\1.XXX.XXX-\2", text)  # Without mask
        text = re.sub(r"\b(\d{3})\.\d{3}\.\d{3}-(\d{2})\b", r"\1.XXX.XXX-\2", text)  # With mask
        
        # CNPJ - Keep first 2 and last 2 digits
        text = re.sub(r"\b(\d{2})\d{10}(\d{2})\b", r"\1.XXX.XXX/XXXX-\2", text)  # Without mask
        text = re.sub(r"\b(\d{2})\.\d{3}\.\d{3}/\d{4}-(\d{2})\b", r"\1.XXX.XXX/XXXX-\2", text)  # With mask
        
        # Phone - Keep area code and last 4 digits
        text = re.sub(r"\b(\d{2})\d{4,5}(\d{4})\b", r"\1*****\2", text)  # Without mask
        text = re.sub(r"\b(\(\d{2}\))\s?\d{4,5}-\d{4}\b", r"\1 XXXXX-XXXX", text)  # With mask
        
        # Email - Keep first 3 letters and everything after @
        text = re.sub(r"\b(\w{3})\w*(@[\w\.-]+\b)", r"\1***\2", text)
        
        return text
    
    def sanitize_message(self, msg: Any) -> str:
        """
        Sanitize message by converting to string and masking sensitive data.
        
        Args:
            msg: Message to sanitize (can be Exception, dict, or any type)
            
        Returns:
            Sanitized string message
        """
        # Convert to string if it's not already
        if isinstance(msg, Exception):
            msg = str(msg)
        elif isinstance(msg, dict):
            # Convert dict values to serializable format
            msg = {key: self._convert_to_serializable(value) for key, value in msg.items()}
            msg = json.dumps(msg, ensure_ascii=False)
        elif not isinstance(msg, str):
            msg = str(msg)
        
        # Apply masking
        msg = self.mask_sensitive_data(msg)
        
        return msg

