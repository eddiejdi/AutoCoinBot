<<<<<<< HEAD
# OS Cleaner Agent 🧹

Agente especializado em limpeza e otimização de sistemas operacionais. Multiplataforma (Windows, Linux, macOS, WSL).

## 📋 Características

- **Multiplataforma**: Detecta automaticamente o SO e executa limpezas apropriadas
- **Seguro**: Modo dry-run para simular antes de executar
- **Modular**: Limpe alvos específicos ou todos de uma vez
- **Extensível**: Fácil adicionar novos alvos de limpeza
- **Relatórios**: Gera relatórios em JSON para análise

## 🚀 Uso Rápido

```bash
# Limpeza padrão
python agents/os_cleaner_agent.py

# Apenas analisar (não limpa)
python agents/os_cleaner_agent.py --analyze

# Simular sem executar
python agents/os_cleaner_agent.py --dry-run

# Modo agressivo (inclui downloads antigos, docker, caches de dev)
python agents/os_cleaner_agent.py --aggressive

# Limpar alvos específicos
python agents/os_cleaner_agent.py --target browser temp cache

# Salvar relatório
python agents/os_cleaner_agent.py --output relatorio.json
```

## 📁 Alvos de Limpeza

### Comuns (Todos os SOs)
| Alvo | Descrição |
|------|-----------|
| `temp` | Arquivos temporários |
| `cache` | Caches gerais do sistema |
| `logs` | Arquivos de log antigos |
| `browser` | Cache dos navegadores (Chrome, Firefox, Edge, Opera, Brave) |
| `thumbnails` | Cache de miniaturas/thumbnails |

### Windows
| Alvo | Descrição |
|------|-----------|
| `windows_update` | Cache do Windows Update |
| `prefetch` | Arquivos Prefetch |
| `recycle_bin` | Lixeira |
| `delivery_optimization` | Cache do Delivery Optimization |

### Linux/WSL
| Alvo | Descrição |
|------|-----------|
| `apt` | Cache do APT (apt clean + autoremove) |
| `journal` | Logs do systemd journal |
| `trash` | Lixeira do Linux |

### macOS
| Alvo | Descrição |
|------|-----------|
| `xcode` | Caches do Xcode (DerivedData, Archives) |
| `trash` | Lixeira do macOS |
| `ios_backup` | Backups antigos do iOS (modo agressivo) |

### Modo Agressivo (--aggressive)
| Alvo | Descrição |
|------|-----------|
| `downloads` | Downloads com mais de 30 dias |
| `pip_cache` | Cache do pip |
| `npm_cache` | Cache do npm |
| `docker` | Imagens e containers não utilizados |

## 📊 Exemplos de Saída

### Análise
```
$ python agents/os_cleaner_agent.py --analyze

OS Cleaner Agent v1.0.0
Sistema detectado: windows
Modo: EXECUÇÃO REAL
Analisando espaço para limpeza...
  temp: 325.08 MB
  cache: 5.01 MB
  logs: 37.24 MB
  browser: 126.37 MB
  thumbnails: 5.01 MB
  windows_update: 175.93 MB

Total estimado: 674.63 MB
```

### Limpeza
```
$ python agents/os_cleaner_agent.py

============================================================
📊 RESUMO DA LIMPEZA
============================================================
Espaço liberado (estimado): 294.53 MB
Espaço liberado (real):     24.05 MB
Arquivos removidos:         28
Operações bem-sucedidas:    9
Operações com falha:        0

Disco antes:  2.50 GB livre (97.5% usado)
Disco depois: 2.52 GB livre (97.4% usado)
============================================================
```

## 🔧 Opções

| Opção | Curto | Descrição |
|-------|-------|-----------|
| `--analyze` | `-a` | Apenas analisa o espaço que pode ser liberado |
| `--dry-run` | `-n` | Simula a limpeza sem executar |
| `--aggressive` | `-A` | Modo agressivo (mais alvos) |
| `--target` | `-t` | Alvos específicos para limpar |
| `--list-targets` | `-l` | Lista alvos disponíveis |
| `--output` | `-o` | Salva relatório em arquivo JSON |
| `--quiet` | `-q` | Modo silencioso (apenas erros) |
| `--version` | `-v` | Mostra versão |

## 🐍 Uso como Módulo Python

```python
from agents.os_cleaner_agent import OSCleanerAgent

# Criar agente
agent = OSCleanerAgent(dry_run=False, aggressive=False)

# Analisar
analysis = agent.analyze()
print(f"Total estimado: {agent.format_size(sum(analysis.values()))}")

# Executar limpeza específica
report = agent.run(targets=['browser', 'temp', 'cache'])

# Acessar resultados
print(f"Espaço liberado: {agent.format_size(report['summary']['total_freed_actual'])}")
```

## 📝 Estrutura do Relatório JSON

```json
{
  "timestamp": "2026-01-01T14:50:27",
  "os": "windows",
  "dry_run": false,
  "aggressive": false,
  "summary": {
    "total_freed_estimated": 294530000,
    "total_freed_actual": 24050000,
    "total_files_removed": 28,
    "targets_successful": 9,
    "targets_failed": 0
  },
  "disk_before": {
    "free": 2500000000,
    "percent_used": 97.5
  },
  "disk_after": {
    "free": 2520000000,
    "percent_used": 97.4
  },
  "details": [
    {
      "target": "Arquivos Temporários",
      "bytes_freed": 72860000,
      "files_removed": 6,
      "success": true,
      "error": null
    }
  ]
}
```

## ⚠️ Notas Importantes

1. **Permissões**: Algumas limpezas requerem privilégios de administrador
2. **Navegadores**: Feche os navegadores antes de limpar seus caches
3. **Modo Agressivo**: Use com cuidado - pode remover arquivos que você precisa
4. **WSL**: O agente detecta automaticamente quando está rodando no WSL

## 🔒 Segurança

- Sempre use `--dry-run` primeiro para verificar o que será removido
- O agente nunca remove arquivos do sistema essenciais
- Backups importantes não são removidos (exceto em modo agressivo com confirmação)

## 📄 Licença

MIT License - Veja [LICENSE](../LICENSE) para detalhes.
=======
# OS Cleaner Agent 🧹

Agente especializado em limpeza e otimização de sistemas operacionais. Multiplataforma (Windows, Linux, macOS, WSL).

## 📋 Características

- **Multiplataforma**: Detecta automaticamente o SO e executa limpezas apropriadas
- **Seguro**: Modo dry-run para simular antes de executar
- **Modular**: Limpe alvos específicos ou todos de uma vez
- **Extensível**: Fácil adicionar novos alvos de limpeza
- **Relatórios**: Gera relatórios em JSON para análise

## 🚀 Uso Rápido

```bash
# Limpeza padrão
python agents/os_cleaner_agent.py

# Apenas analisar (não limpa)
python agents/os_cleaner_agent.py --analyze

# Simular sem executar
python agents/os_cleaner_agent.py --dry-run

# Modo agressivo (inclui downloads antigos, docker, caches de dev)
python agents/os_cleaner_agent.py --aggressive

# Limpar alvos específicos
python agents/os_cleaner_agent.py --target browser temp cache

# Salvar relatório
python agents/os_cleaner_agent.py --output relatorio.json
```

## 📁 Alvos de Limpeza

### Comuns (Todos os SOs)
| Alvo | Descrição |
|------|-----------|
| `temp` | Arquivos temporários |
| `cache` | Caches gerais do sistema |
| `logs` | Arquivos de log antigos |
| `browser` | Cache dos navegadores (Chrome, Firefox, Edge, Opera, Brave) |
| `thumbnails` | Cache de miniaturas/thumbnails |

### Windows
| Alvo | Descrição |
|------|-----------|
| `windows_update` | Cache do Windows Update |
| `prefetch` | Arquivos Prefetch |
| `recycle_bin` | Lixeira |
| `delivery_optimization` | Cache do Delivery Optimization |

### Linux/WSL
| Alvo | Descrição |
|------|-----------|
| `apt` | Cache do APT (apt clean + autoremove) |
| `journal` | Logs do systemd journal |
| `trash` | Lixeira do Linux |

### macOS
| Alvo | Descrição |
|------|-----------|
| `xcode` | Caches do Xcode (DerivedData, Archives) |
| `trash` | Lixeira do macOS |
| `ios_backup` | Backups antigos do iOS (modo agressivo) |

### Modo Agressivo (--aggressive)
| Alvo | Descrição |
|------|-----------|
| `downloads` | Downloads com mais de 30 dias |
| `pip_cache` | Cache do pip |
| `npm_cache` | Cache do npm |
| `docker` | Imagens e containers não utilizados |

## 📊 Exemplos de Saída

### Análise
```
$ python agents/os_cleaner_agent.py --analyze

OS Cleaner Agent v1.0.0
Sistema detectado: windows
Modo: EXECUÇÃO REAL
Analisando espaço para limpeza...
  temp: 325.08 MB
  cache: 5.01 MB
  logs: 37.24 MB
  browser: 126.37 MB
  thumbnails: 5.01 MB
  windows_update: 175.93 MB

Total estimado: 674.63 MB
```

### Limpeza
```
$ python agents/os_cleaner_agent.py

============================================================
📊 RESUMO DA LIMPEZA
============================================================
Espaço liberado (estimado): 294.53 MB
Espaço liberado (real):     24.05 MB
Arquivos removidos:         28
Operações bem-sucedidas:    9
Operações com falha:        0

Disco antes:  2.50 GB livre (97.5% usado)
Disco depois: 2.52 GB livre (97.4% usado)
============================================================
```

## 🔧 Opções

| Opção | Curto | Descrição |
|-------|-------|-----------|
| `--analyze` | `-a` | Apenas analisa o espaço que pode ser liberado |
| `--dry-run` | `-n` | Simula a limpeza sem executar |
| `--aggressive` | `-A` | Modo agressivo (mais alvos) |
| `--target` | `-t` | Alvos específicos para limpar |
| `--list-targets` | `-l` | Lista alvos disponíveis |
| `--output` | `-o` | Salva relatório em arquivo JSON |
| `--quiet` | `-q` | Modo silencioso (apenas erros) |
| `--version` | `-v` | Mostra versão |

## 🐍 Uso como Módulo Python

```python
from agents.os_cleaner_agent import OSCleanerAgent

# Criar agente
agent = OSCleanerAgent(dry_run=False, aggressive=False)

# Analisar
analysis = agent.analyze()
print(f"Total estimado: {agent.format_size(sum(analysis.values()))}")

# Executar limpeza específica
report = agent.run(targets=['browser', 'temp', 'cache'])

# Acessar resultados
print(f"Espaço liberado: {agent.format_size(report['summary']['total_freed_actual'])}")
```

## 📝 Estrutura do Relatório JSON

```json
{
  "timestamp": "2026-01-01T14:50:27",
  "os": "windows",
  "dry_run": false,
  "aggressive": false,
  "summary": {
    "total_freed_estimated": 294530000,
    "total_freed_actual": 24050000,
    "total_files_removed": 28,
    "targets_successful": 9,
    "targets_failed": 0
  },
  "disk_before": {
    "free": 2500000000,
    "percent_used": 97.5
  },
  "disk_after": {
    "free": 2520000000,
    "percent_used": 97.4
  },
  "details": [
    {
      "target": "Arquivos Temporários",
      "bytes_freed": 72860000,
      "files_removed": 6,
      "success": true,
      "error": null
    }
  ]
}
```

## ⚠️ Notas Importantes

1. **Permissões**: Algumas limpezas requerem privilégios de administrador
2. **Navegadores**: Feche os navegadores antes de limpar seus caches
3. **Modo Agressivo**: Use com cuidado - pode remover arquivos que você precisa
4. **WSL**: O agente detecta automaticamente quando está rodando no WSL

## 🔒 Segurança

- Sempre use `--dry-run` primeiro para verificar o que será removido
- O agente nunca remove arquivos do sistema essenciais
- Backups importantes não são removidos (exceto em modo agressivo com confirmação)

## 📄 Licença

MIT License - Veja [LICENSE](../LICENSE) para detalhes.
>>>>>>> d82f869 (Checkpoint from VS Code for coding agent session)
