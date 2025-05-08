import re
from typing import Any, Union

def mask_sensitive_data(text: Union[str, Any]) -> Union[str, Any]:
    """
    Mascarar dados sensíveis (CPF, CNPJ, telefone, e-mail).
    Se não for string, retorna o valor original.
    """
    if not isinstance(text, str):
        return text

    # CPF - Mantém os 3 primeiros e 2 últimos dígitos
    text = re.sub(r"\b(\d{3})\d{6}(\d{2})\b", r"\1.XXX.XXX-\2", text)  # Sem máscara
    text = re.sub(r"\b(\d{3})\.\d{3}\.\d{3}-(\d{2})\b", r"\1.XXX.XXX-\2", text)  # Com máscara

    # CNPJ - Mantém os 2 primeiros e 2 últimos dígitos
    text = re.sub(r"\b(\d{2})\d{10}(\d{2})\b", r"\1.XXX.XXX/XXXX-\2", text)
    text = re.sub(r"\b(\d{2})\.\d{3}\.\d{3}/\d{4}-(\d{2})\b", r"\1.XXX.XXX/XXXX-\2", text)

    # Telefone - Mantém o DDD e os últimos 4 dígitos
    text = re.sub(r"\b(\d{2})\d{4,5}(\d{4})\b", r"\1*****\2", text)  # Sem máscara
    text = re.sub(r"\b$$\d{2}$$\s?\d{4,5}-\d{4}\b", r"\1 XXXXX-XXXX", text)  # Com máscara

    # E-mail - Mantém as 3 primeiras letras e o domínio completo
    text = re.sub(r"\b(\w{3})\w*(@[\w\.-]+\b)", r"\1***\2", text)

    return text

def mask_dict(d: dict) -> dict:
    """
    Percorre e mascara dados sensíveis de um dicionário recursivamente,
    aplicando mask_sensitive_data em cada valor string.
    """
    def mask_item(item):
        if isinstance(item, str):
            return mask_sensitive_data(item)
        elif isinstance(item, dict):
            return {k: mask_item(v) for k, v in item.items()}
        elif isinstance(item, list):
            return [mask_item(v) for v in item]
        return item
    return {k: mask_item(v) for k, v in d.items()}