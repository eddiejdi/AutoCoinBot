"""Configuração de pytest para garantir que o diretório do projeto
esteja sempre presente em sys.path durante os testes.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
root_str = str(ROOT)

if root_str not in sys.path:
    sys.path.insert(0, root_str)
