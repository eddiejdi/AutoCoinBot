"""
Agents - Agentes especializados para automação

Este módulo contém agentes especializados que podem ser utilizados
em qualquer projeto/modelo.

Agentes disponíveis:
- os_cleaner_agent: Agente de limpeza de sistema operacional (Windows/Linux/macOS)
"""

from .os_cleaner_agent import OSCleanerAgent, CleanupResult, DiskInfo

__all__ = [
    'OSCleanerAgent',
    'CleanupResult', 
    'DiskInfo',
]
