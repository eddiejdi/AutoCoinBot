#!/usr/bin/env python3
"""
OS Cleaner Agent - Agente Especializado em Limpeza de Sistema Operacional

Um agente multiplataforma para limpeza e otimização de sistemas operacionais.
Suporta Windows, Linux e macOS.

Uso:
    python os_cleaner_agent.py                    # Executa limpeza padrão
    python os_cleaner_agent.py --analyze          # Apenas analisa (não limpa)
    python os_cleaner_agent.py --aggressive       # Limpeza agressiva
    python os_cleaner_agent.py --dry-run          # Simula sem executar
    python os_cleaner_agent.py --target browser   # Limpa apenas navegadores

Autor: AutoCoinBot Team
Versão: 1.0.0
"""

import os
import sys
import platform
import shutil
import subprocess
import json
import argparse
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """Resultado de uma operação de limpeza."""
    target: str
    bytes_freed: int = 0
    files_removed: int = 0
    success: bool = True
    error: Optional[str] = None
    details: List[str] = field(default_factory=list)


@dataclass
class DiskInfo:
    """Informações sobre o disco."""
    path: str
    total: int
    used: int
    free: int
    percent_used: float


class CleanupTarget(ABC):
    """Classe base abstrata para alvos de limpeza."""
    
    name: str = "base"
    description: str = "Base cleanup target"
    
    @abstractmethod
    def get_paths(self) -> List[Path]:
        """Retorna lista de caminhos a serem limpos."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Verifica se este alvo está disponível no sistema."""
        pass
    
    def pre_cleanup(self) -> bool:
        """Ações antes da limpeza. Retorna True se pode continuar."""
        return True
    
    def post_cleanup(self) -> None:
        """Ações após a limpeza."""
        pass


class OSCleanerAgent:
    """
    Agente principal de limpeza de SO.
    Detecta automaticamente o sistema operacional e executa limpezas apropriadas.
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, dry_run: bool = False, aggressive: bool = False):
        self.dry_run = dry_run
        self.aggressive = aggressive
        self.os_type = self._detect_os()
        self.home_dir = Path.home()
        self.results: List[CleanupResult] = []
        self.initial_disk_info: Optional[DiskInfo] = None
        self.final_disk_info: Optional[DiskInfo] = None
        
        logger.info(f"OS Cleaner Agent v{self.VERSION}")
        logger.info(f"Sistema detectado: {self.os_type}")
        logger.info(f"Modo: {'DRY-RUN (simulação)' if dry_run else 'EXECUÇÃO REAL'}")
        if aggressive:
            logger.warning("Modo AGRESSIVO ativado")
    
    def _detect_os(self) -> str:
        """Detecta o sistema operacional."""
        system = platform.system().lower()
        if system == 'windows':
            return 'windows'
        elif system == 'darwin':
            return 'macos'
        elif system == 'linux':
            # Detecta se está no WSL
            if 'microsoft' in platform.release().lower():
                return 'wsl'
            return 'linux'
        return 'unknown'
    
    def get_disk_info(self, path: str = '/') -> DiskInfo:
        """Obtém informações do disco."""
        if self.os_type == 'windows':
            path = 'C:\\'
        
        try:
            usage = shutil.disk_usage(path)
            return DiskInfo(
                path=path,
                total=usage.total,
                used=usage.used,
                free=usage.free,
                percent_used=(usage.used / usage.total) * 100
            )
        except Exception as e:
            logger.error(f"Erro ao obter info do disco: {e}")
            return DiskInfo(path=path, total=0, used=0, free=0, percent_used=0)
    
    def format_size(self, bytes_size: int) -> str:
        """Formata tamanho em bytes para formato legível."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if abs(bytes_size) < 1024.0:
                return f"{bytes_size:.2f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.2f} PB"
    
    def get_dir_size(self, path: Path) -> int:
        """Calcula o tamanho total de um diretório."""
        total = 0
        try:
            for entry in path.rglob('*'):
                try:
                    if entry.is_file():
                        total += entry.stat().st_size
                except (OSError, PermissionError):
                    pass
        except (OSError, PermissionError):
            pass
        return total
    
    def safe_remove(self, path: Path, is_dir: bool = False) -> Tuple[bool, int]:
        """Remove arquivo ou diretório de forma segura."""
        if self.dry_run:
            size = self.get_dir_size(path) if is_dir else (path.stat().st_size if path.exists() else 0)
            logger.debug(f"[DRY-RUN] Removeria: {path} ({self.format_size(size)})")
            return True, size
        
        try:
            if is_dir:
                size = self.get_dir_size(path)
                shutil.rmtree(path, ignore_errors=True)
            else:
                size = path.stat().st_size if path.exists() else 0
                path.unlink(missing_ok=True)
            return True, size
        except (OSError, PermissionError) as e:
            logger.debug(f"Não foi possível remover {path}: {e}")
            return False, 0
    
    def clean_directory(self, path: Path, patterns: List[str] = None, 
                       recursive: bool = True, contents_only: bool = True) -> CleanupResult:
        """
        Limpa um diretório.
        
        Args:
            path: Caminho do diretório
            patterns: Padrões de arquivos a remover (None = todos)
            recursive: Se deve limpar recursivamente
            contents_only: Se True, mantém o diretório mas remove conteúdo
        """
        result = CleanupResult(target=str(path))
        
        if not path.exists():
            result.details.append(f"Diretório não existe: {path}")
            return result
        
        try:
            if patterns:
                # Remove apenas arquivos que correspondem aos padrões
                for pattern in patterns:
                    if recursive:
                        files = list(path.rglob(pattern))
                    else:
                        files = list(path.glob(pattern))
                    
                    for f in files:
                        success, size = self.safe_remove(f, f.is_dir())
                        if success:
                            result.bytes_freed += size
                            result.files_removed += 1
            else:
                # Remove todo o conteúdo
                if contents_only:
                    for item in path.iterdir():
                        success, size = self.safe_remove(item, item.is_dir())
                        if success:
                            result.bytes_freed += size
                            result.files_removed += 1
                else:
                    size = self.get_dir_size(path)
                    success, _ = self.safe_remove(path, is_dir=True)
                    if success:
                        result.bytes_freed = size
                        result.files_removed = 1
            
            result.details.append(f"Limpo: {path}")
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(f"Erro ao limpar {path}: {e}")
        
        return result
    
    # ==================== TARGETS DE LIMPEZA ====================
    
    def get_cleanup_targets(self) -> Dict[str, Callable]:
        """Retorna os alvos de limpeza disponíveis para o SO atual."""
        common_targets = {
            'temp': self.clean_temp_files,
            'cache': self.clean_cache,
            'logs': self.clean_logs,
            'browser': self.clean_browsers,
            'thumbnails': self.clean_thumbnails,
        }
        
        if self.os_type == 'windows':
            common_targets.update({
                'windows_update': self.clean_windows_update,
                'prefetch': self.clean_prefetch,
                'recycle_bin': self.clean_recycle_bin,
                'delivery_optimization': self.clean_delivery_optimization,
            })
        elif self.os_type in ['linux', 'wsl']:
            common_targets.update({
                'apt': self.clean_apt_cache,
                'journal': self.clean_journal_logs,
                'trash': self.clean_trash,
            })
        elif self.os_type == 'macos':
            common_targets.update({
                'xcode': self.clean_xcode,
                'trash': self.clean_trash,
                'ios_backup': self.clean_ios_backups,
            })
        
        if self.aggressive:
            common_targets.update({
                'downloads': self.clean_old_downloads,
                'pip_cache': self.clean_pip_cache,
                'npm_cache': self.clean_npm_cache,
                'docker': self.clean_docker,
            })
        
        return common_targets
    
    # ==================== LIMPEZAS COMUNS ====================
    
    def clean_temp_files(self) -> CleanupResult:
        """Limpa arquivos temporários."""
        result = CleanupResult(target="Arquivos Temporários")
        
        temp_paths = []
        
        if self.os_type == 'windows':
            temp_paths = [
                Path(os.environ.get('TEMP', '')),
                Path(os.environ.get('TMP', '')),
                Path('C:/Windows/Temp'),
            ]
        else:
            temp_paths = [
                Path('/tmp'),
                Path('/var/tmp'),
                self.home_dir / '.cache' / 'tmp',
            ]
        
        for path in temp_paths:
            if path and path.exists():
                r = self.clean_directory(path, contents_only=True)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.extend(r.details)
        
        return result
    
    def clean_cache(self) -> CleanupResult:
        """Limpa caches gerais."""
        result = CleanupResult(target="Cache Geral")
        
        cache_paths = []
        
        if self.os_type == 'windows':
            cache_paths = [
                self.home_dir / 'AppData' / 'Local' / 'Microsoft' / 'Windows' / 'INetCache',
                self.home_dir / 'AppData' / 'Local' / 'Microsoft' / 'Windows' / 'Explorer',
            ]
        else:
            cache_paths = [
                self.home_dir / '.cache',
            ]
        
        patterns = ['*.tmp', '*.temp', '*.cache', 'thumbcache_*']
        
        for path in cache_paths:
            if path.exists():
                r = self.clean_directory(path, patterns=patterns)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.extend(r.details)
        
        return result
    
    def clean_logs(self) -> CleanupResult:
        """Limpa arquivos de log antigos."""
        result = CleanupResult(target="Arquivos de Log")
        
        log_paths = []
        
        if self.os_type == 'windows':
            log_paths = [
                Path('C:/Windows/Logs'),
                self.home_dir / 'AppData' / 'Local' / 'Temp',
            ]
        else:
            log_paths = [
                Path('/var/log'),
                self.home_dir / '.local' / 'share' / 'xorg',
            ]
        
        patterns = ['*.log', '*.log.*', '*.old']
        
        for path in log_paths:
            if path.exists():
                r = self.clean_directory(path, patterns=patterns)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.extend(r.details)
        
        return result
    
    def clean_browsers(self) -> CleanupResult:
        """Limpa cache dos navegadores."""
        result = CleanupResult(target="Cache de Navegadores")
        
        browser_caches = []
        
        if self.os_type == 'windows':
            browser_caches = [
                # Chrome
                self.home_dir / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Cache',
                self.home_dir / 'AppData' / 'Local' / 'Google' / 'Chrome' / 'User Data' / 'Default' / 'Code Cache',
                # Firefox
                self.home_dir / 'AppData' / 'Local' / 'Mozilla' / 'Firefox' / 'Profiles',
                # Edge
                self.home_dir / 'AppData' / 'Local' / 'Microsoft' / 'Edge' / 'User Data' / 'Default' / 'Cache',
                # Opera
                self.home_dir / 'AppData' / 'Local' / 'Opera Software' / 'Opera Stable' / 'Cache',
                # Brave
                self.home_dir / 'AppData' / 'Local' / 'BraveSoftware' / 'Brave-Browser' / 'User Data' / 'Default' / 'Cache',
            ]
        elif self.os_type == 'macos':
            browser_caches = [
                self.home_dir / 'Library' / 'Caches' / 'Google' / 'Chrome',
                self.home_dir / 'Library' / 'Caches' / 'Firefox',
                self.home_dir / 'Library' / 'Caches' / 'com.apple.Safari',
            ]
        else:  # Linux/WSL
            browser_caches = [
                self.home_dir / '.cache' / 'google-chrome',
                self.home_dir / '.cache' / 'chromium',
                self.home_dir / '.cache' / 'mozilla',
                self.home_dir / '.cache' / 'opera',
            ]
        
        for path in browser_caches:
            if path.exists():
                r = self.clean_directory(path, contents_only=True)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.append(f"Cache limpo: {path.name}")
        
        return result
    
    def clean_thumbnails(self) -> CleanupResult:
        """Limpa cache de miniaturas."""
        result = CleanupResult(target="Miniaturas/Thumbnails")
        
        thumb_paths = []
        
        if self.os_type == 'windows':
            thumb_paths = [
                self.home_dir / 'AppData' / 'Local' / 'Microsoft' / 'Windows' / 'Explorer',
            ]
            patterns = ['thumbcache_*']
        else:
            thumb_paths = [
                self.home_dir / '.cache' / 'thumbnails',
                self.home_dir / '.thumbnails',
            ]
            patterns = None
        
        for path in thumb_paths:
            if path.exists():
                r = self.clean_directory(path, patterns=patterns, contents_only=True)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.extend(r.details)
        
        return result
    
    # ==================== LIMPEZAS WINDOWS ====================
    
    def clean_windows_update(self) -> CleanupResult:
        """Limpa cache do Windows Update."""
        result = CleanupResult(target="Windows Update Cache")
        
        if self.os_type != 'windows':
            result.details.append("Não aplicável (não é Windows)")
            return result
        
        update_path = Path('C:/Windows/SoftwareDistribution/Download')
        
        if update_path.exists():
            # Para o serviço antes de limpar
            if not self.dry_run:
                try:
                    subprocess.run(['net', 'stop', 'wuauserv'], capture_output=True)
                except Exception:
                    pass
            
            r = self.clean_directory(update_path, contents_only=True)
            result.bytes_freed = r.bytes_freed
            result.files_removed = r.files_removed
            result.details = r.details
            
            # Reinicia o serviço
            if not self.dry_run:
                try:
                    subprocess.run(['net', 'start', 'wuauserv'], capture_output=True)
                except Exception:
                    pass
        
        return result
    
    def clean_prefetch(self) -> CleanupResult:
        """Limpa pasta Prefetch do Windows."""
        result = CleanupResult(target="Prefetch")
        
        if self.os_type != 'windows':
            result.details.append("Não aplicável (não é Windows)")
            return result
        
        prefetch_path = Path('C:/Windows/Prefetch')
        
        if prefetch_path.exists():
            r = self.clean_directory(prefetch_path, patterns=['*.pf'], contents_only=True)
            result.bytes_freed = r.bytes_freed
            result.files_removed = r.files_removed
            result.details = r.details
        
        return result
    
    def clean_recycle_bin(self) -> CleanupResult:
        """Esvazia a Lixeira do Windows."""
        result = CleanupResult(target="Lixeira")
        
        if self.os_type != 'windows':
            result.details.append("Não aplicável (não é Windows)")
            return result
        
        if self.dry_run:
            result.details.append("[DRY-RUN] Esvaziaria a lixeira")
            return result
        
        try:
            # Usando PowerShell para esvaziar lixeira
            subprocess.run([
                'powershell', '-Command',
                'Clear-RecycleBin -Force -ErrorAction SilentlyContinue'
            ], capture_output=True)
            result.details.append("Lixeira esvaziada")
        except Exception as e:
            result.error = str(e)
        
        return result
    
    def clean_delivery_optimization(self) -> CleanupResult:
        """Limpa cache do Delivery Optimization."""
        result = CleanupResult(target="Delivery Optimization")
        
        if self.os_type != 'windows':
            result.details.append("Não aplicável (não é Windows)")
            return result
        
        if self.dry_run:
            result.details.append("[DRY-RUN] Limparia Delivery Optimization")
            return result
        
        try:
            subprocess.run([
                'powershell', '-Command',
                'Delete-DeliveryOptimizationCache -Force'
            ], capture_output=True)
            result.details.append("Delivery Optimization limpo")
        except Exception as e:
            result.error = str(e)
        
        return result
    
    # ==================== LIMPEZAS LINUX/WSL ====================
    
    def clean_apt_cache(self) -> CleanupResult:
        """Limpa cache do APT (Debian/Ubuntu)."""
        result = CleanupResult(target="APT Cache")
        
        if self.os_type not in ['linux', 'wsl']:
            result.details.append("Não aplicável (não é Linux)")
            return result
        
        apt_cache = Path('/var/cache/apt/archives')
        
        if apt_cache.exists():
            if self.dry_run:
                size = self.get_dir_size(apt_cache)
                result.bytes_freed = size
                result.details.append(f"[DRY-RUN] Limparia APT cache ({self.format_size(size)})")
            else:
                try:
                    subprocess.run(['sudo', 'apt', 'clean'], capture_output=True)
                    subprocess.run(['sudo', 'apt', 'autoremove', '-y'], capture_output=True)
                    result.details.append("APT cache limpo")
                except Exception as e:
                    result.error = str(e)
        
        return result
    
    def clean_journal_logs(self) -> CleanupResult:
        """Limpa logs do systemd journal."""
        result = CleanupResult(target="Journal Logs")
        
        if self.os_type not in ['linux', 'wsl']:
            result.details.append("Não aplicável (não é Linux)")
            return result
        
        journal_path = Path('/var/log/journal')
        
        if journal_path.exists():
            if self.dry_run:
                size = self.get_dir_size(journal_path)
                result.bytes_freed = size
                result.details.append(f"[DRY-RUN] Limparia journal logs ({self.format_size(size)})")
            else:
                try:
                    # Mantém apenas os últimos 7 dias
                    subprocess.run([
                        'sudo', 'journalctl', '--vacuum-time=7d'
                    ], capture_output=True)
                    result.details.append("Journal logs limpos (mantidos últimos 7 dias)")
                except Exception as e:
                    result.error = str(e)
        
        return result
    
    def clean_trash(self) -> CleanupResult:
        """Esvazia a lixeira do Linux/macOS."""
        result = CleanupResult(target="Lixeira")
        
        if self.os_type == 'windows':
            return self.clean_recycle_bin()
        
        trash_paths = [
            self.home_dir / '.local' / 'share' / 'Trash',
            self.home_dir / '.Trash',
        ]
        
        for path in trash_paths:
            if path.exists():
                r = self.clean_directory(path, contents_only=True)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.extend(r.details)
        
        return result
    
    # ==================== LIMPEZAS MACOS ====================
    
    def clean_xcode(self) -> CleanupResult:
        """Limpa caches do Xcode."""
        result = CleanupResult(target="Xcode Cache")
        
        if self.os_type != 'macos':
            result.details.append("Não aplicável (não é macOS)")
            return result
        
        xcode_paths = [
            self.home_dir / 'Library' / 'Developer' / 'Xcode' / 'DerivedData',
            self.home_dir / 'Library' / 'Developer' / 'Xcode' / 'Archives',
            self.home_dir / 'Library' / 'Developer' / 'Xcode' / 'iOS DeviceSupport',
        ]
        
        for path in xcode_paths:
            if path.exists():
                r = self.clean_directory(path, contents_only=True)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.extend(r.details)
        
        return result
    
    def clean_ios_backups(self) -> CleanupResult:
        """Limpa backups antigos do iOS."""
        result = CleanupResult(target="iOS Backups")
        
        if self.os_type != 'macos':
            result.details.append("Não aplicável (não é macOS)")
            return result
        
        backup_path = self.home_dir / 'Library' / 'Application Support' / 'MobileSync' / 'Backup'
        
        if backup_path.exists() and self.aggressive:
            r = self.clean_directory(backup_path, contents_only=True)
            result.bytes_freed = r.bytes_freed
            result.files_removed = r.files_removed
            result.details = r.details
        else:
            result.details.append("Use --aggressive para limpar backups do iOS")
        
        return result
    
    # ==================== LIMPEZAS AGRESSIVAS ====================
    
    def clean_old_downloads(self) -> CleanupResult:
        """Limpa downloads antigos (mais de 30 dias)."""
        result = CleanupResult(target="Downloads Antigos")
        
        downloads_path = self.home_dir / 'Downloads'
        
        if not downloads_path.exists():
            return result
        
        cutoff = datetime.now().timestamp() - (30 * 24 * 60 * 60)  # 30 dias
        
        for item in downloads_path.iterdir():
            try:
                if item.stat().st_mtime < cutoff:
                    success, size = self.safe_remove(item, item.is_dir())
                    if success:
                        result.bytes_freed += size
                        result.files_removed += 1
            except (OSError, PermissionError):
                pass
        
        result.details.append(f"Removidos arquivos com mais de 30 dias")
        return result
    
    def clean_pip_cache(self) -> CleanupResult:
        """Limpa cache do pip."""
        result = CleanupResult(target="Pip Cache")
        
        pip_paths = [
            self.home_dir / '.cache' / 'pip',
            self.home_dir / 'AppData' / 'Local' / 'pip' / 'Cache',
        ]
        
        for path in pip_paths:
            if path.exists():
                r = self.clean_directory(path, contents_only=True)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.extend(r.details)
        
        return result
    
    def clean_npm_cache(self) -> CleanupResult:
        """Limpa cache do npm."""
        result = CleanupResult(target="NPM Cache")
        
        npm_paths = [
            self.home_dir / '.npm',
            self.home_dir / 'AppData' / 'Roaming' / 'npm-cache',
        ]
        
        for path in npm_paths:
            if path.exists():
                r = self.clean_directory(path, contents_only=True)
                result.bytes_freed += r.bytes_freed
                result.files_removed += r.files_removed
                result.details.extend(r.details)
        
        return result
    
    def clean_docker(self) -> CleanupResult:
        """Limpa imagens e containers Docker não utilizados."""
        result = CleanupResult(target="Docker")
        
        if self.dry_run:
            result.details.append("[DRY-RUN] Executaria 'docker system prune -af'")
            return result
        
        try:
            output = subprocess.run(
                ['docker', 'system', 'prune', '-af'],
                capture_output=True,
                text=True
            )
            result.details.append("Docker limpo")
            if output.stdout:
                result.details.append(output.stdout.strip())
        except FileNotFoundError:
            result.details.append("Docker não instalado")
        except Exception as e:
            result.error = str(e)
        
        return result
    
    # ==================== EXECUÇÃO ====================
    
    def analyze(self) -> Dict[str, int]:
        """Analisa o espaço que pode ser liberado sem executar limpeza."""
        logger.info("Analisando espaço para limpeza...")
        
        analysis = {}
        targets = self.get_cleanup_targets()
        
        # Força modo dry-run para análise
        original_dry_run = self.dry_run
        self.dry_run = True
        
        for name, cleanup_func in targets.items():
            try:
                result = cleanup_func()
                analysis[name] = result.bytes_freed
                logger.info(f"  {name}: {self.format_size(result.bytes_freed)}")
            except Exception as e:
                logger.error(f"  {name}: Erro - {e}")
                analysis[name] = 0
        
        self.dry_run = original_dry_run
        
        total = sum(analysis.values())
        logger.info(f"\nTotal estimado: {self.format_size(total)}")
        
        return analysis
    
    def run(self, targets: List[str] = None) -> Dict:
        """
        Executa a limpeza.
        
        Args:
            targets: Lista de alvos específicos para limpar. None = todos.
        
        Returns:
            Dicionário com resultados da limpeza.
        """
        logger.info("=" * 60)
        logger.info("Iniciando limpeza do sistema...")
        logger.info("=" * 60)
        
        # Captura estado inicial
        self.initial_disk_info = self.get_disk_info()
        logger.info(f"Espaço livre inicial: {self.format_size(self.initial_disk_info.free)}")
        
        available_targets = self.get_cleanup_targets()
        
        if targets:
            # Filtra apenas os alvos especificados
            available_targets = {k: v for k, v in available_targets.items() if k in targets}
        
        # Executa cada limpeza
        for name, cleanup_func in available_targets.items():
            logger.info(f"\n{'─' * 40}")
            logger.info(f"🧹 {name.upper()}")
            
            try:
                result = cleanup_func()
                self.results.append(result)
                
                if result.bytes_freed > 0:
                    logger.info(f"   ✓ Liberado: {self.format_size(result.bytes_freed)}")
                    logger.info(f"   ✓ Arquivos: {result.files_removed}")
                elif result.error:
                    logger.error(f"   ✗ Erro: {result.error}")
                else:
                    logger.info(f"   ○ Nada para limpar")
                    
            except Exception as e:
                logger.error(f"   ✗ Erro: {e}")
                self.results.append(CleanupResult(
                    target=name,
                    success=False,
                    error=str(e)
                ))
        
        # Captura estado final
        self.final_disk_info = self.get_disk_info()
        
        # Gera relatório
        return self.generate_report()
    
    def generate_report(self) -> Dict:
        """Gera relatório da limpeza."""
        total_freed = sum(r.bytes_freed for r in self.results)
        total_files = sum(r.files_removed for r in self.results)
        successful = sum(1 for r in self.results if r.success)
        failed = sum(1 for r in self.results if not r.success)
        
        actual_freed = 0
        if self.initial_disk_info and self.final_disk_info:
            actual_freed = self.final_disk_info.free - self.initial_disk_info.free
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'os': self.os_type,
            'dry_run': self.dry_run,
            'aggressive': self.aggressive,
            'summary': {
                'total_freed_estimated': total_freed,
                'total_freed_actual': actual_freed,
                'total_files_removed': total_files,
                'targets_successful': successful,
                'targets_failed': failed,
            },
            'disk_before': {
                'free': self.initial_disk_info.free if self.initial_disk_info else 0,
                'percent_used': self.initial_disk_info.percent_used if self.initial_disk_info else 0,
            },
            'disk_after': {
                'free': self.final_disk_info.free if self.final_disk_info else 0,
                'percent_used': self.final_disk_info.percent_used if self.final_disk_info else 0,
            },
            'details': [
                {
                    'target': r.target,
                    'bytes_freed': r.bytes_freed,
                    'files_removed': r.files_removed,
                    'success': r.success,
                    'error': r.error,
                }
                for r in self.results
            ]
        }
        
        # Imprime resumo
        logger.info("\n" + "=" * 60)
        logger.info("📊 RESUMO DA LIMPEZA")
        logger.info("=" * 60)
        logger.info(f"Espaço liberado (estimado): {self.format_size(total_freed)}")
        logger.info(f"Espaço liberado (real):     {self.format_size(actual_freed)}")
        logger.info(f"Arquivos removidos:         {total_files}")
        logger.info(f"Operações bem-sucedidas:    {successful}")
        logger.info(f"Operações com falha:        {failed}")
        
        if self.initial_disk_info and self.final_disk_info:
            logger.info(f"\nDisco antes:  {self.format_size(self.initial_disk_info.free)} livre ({self.initial_disk_info.percent_used:.1f}% usado)")
            logger.info(f"Disco depois: {self.format_size(self.final_disk_info.free)} livre ({self.final_disk_info.percent_used:.1f}% usado)")
        
        logger.info("=" * 60)
        
        return report


def main():
    """Função principal."""
    parser = argparse.ArgumentParser(
        description='OS Cleaner Agent - Agente de Limpeza de Sistema Operacional',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                      # Limpeza padrão
  %(prog)s --analyze            # Apenas analisa espaço
  %(prog)s --dry-run            # Simula sem executar
  %(prog)s --aggressive         # Limpeza agressiva
  %(prog)s --target browser     # Limpa apenas navegadores
  %(prog)s --target temp cache  # Limpa temp e cache
        """
    )
    
    parser.add_argument(
        '--analyze', '-a',
        action='store_true',
        help='Apenas analisa o espaço que pode ser liberado'
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Simula a limpeza sem executar'
    )
    
    parser.add_argument(
        '--aggressive', '-A',
        action='store_true',
        help='Modo agressivo (inclui downloads antigos, caches de dev, docker)'
    )
    
    parser.add_argument(
        '--target', '-t',
        nargs='+',
        help='Alvos específicos para limpar'
    )
    
    parser.add_argument(
        '--list-targets', '-l',
        action='store_true',
        help='Lista alvos disponíveis'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        help='Salva relatório em arquivo JSON'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Modo silencioso (apenas erros)'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version=f'OS Cleaner Agent v{OSCleanerAgent.VERSION}'
    )
    
    args = parser.parse_args()
    
    # Configura logging
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Cria agente
    agent = OSCleanerAgent(
        dry_run=args.dry_run,
        aggressive=args.aggressive
    )
    
    # Lista alvos disponíveis
    if args.list_targets:
        print("\nAlvos de limpeza disponíveis:")
        print("-" * 40)
        for name in agent.get_cleanup_targets().keys():
            print(f"  • {name}")
        print()
        return
    
    # Executa análise ou limpeza
    if args.analyze:
        agent.analyze()
    else:
        report = agent.run(targets=args.target)
        
        # Salva relatório se solicitado
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"\nRelatório salvo em: {args.output}")


if __name__ == '__main__':
    main()
