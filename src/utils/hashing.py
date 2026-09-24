import hashlib
import pandas as pd

SALT_SECRET = "DonDoctor_HabeasData_2026_Key"

def anonimizar_pii(valor: str, salt: str = SALT_SECRET) -> str:
    """Aplica hashing criptográfico SHA-256 + Salt para enmascarar PII (Ley 1581)."""
    if pd.isna(valor) or valor is None:
        return None
    val_clean = str(valor).strip().lower()
    return hashlib.sha256((val_clean + salt).encode('utf-8')).hexdigest()