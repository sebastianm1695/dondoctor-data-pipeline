import os
import sys
import pandas as pd

DIR_RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

from src.quality.profiling import perfilar_todas_las_columnas
from src.utils.hashing import anonimizar_pii

def test_anonimizar_pii():
    doc = "12345678"
    hash1 = anonimizar_pii(doc)
    hash2 = anonimizar_pii(doc)
    assert hash1 == hash2
    assert len(hash1) == 64

def test_perfilar_todas_las_columnas():
    df_test = pd.DataFrame({
        "id": [1, 2, 3],
        "nombre": ["Alice", "Bob", None]
    })
    res = perfilar_todas_las_columnas(df_test, "Test")
    assert len(res) == 2
    assert "completitud_porcentaje" in res.columns