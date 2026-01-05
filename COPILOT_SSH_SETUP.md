# 🤖 Setup Copilot com Modelos Remotos SSH

## 🚀 Início Rápido

### 1. Execute o Script de Descoberta
```powershell
cd C:\seu\caminho\AutoCoinBot
.\setup_copilot_models_ssh.ps1
```

**O script irá:**
- ✅ Conectar ao servidor 192.168.15.2 (homelab/homelab)
- ✅ Descobrir todos os modelos IA disponíveis
- ✅ Configurar VSCode automaticamente
- ✅ Gerar relatório de sucesso

### 2. Verifique as Extensões Necessárias

O VSCode precisa dessas extensões:
```
GitHub Copilot
GitHub Copilot Chat
Remote - SSH
Remote - SSH: Editing Configuration Files
Remote Explorer
```

**Instalar via CLI:**
```powershell
code --install-extension GitHub.copilot
code --install-extension GitHub.copilot-chat
code --install-extension ms-vscode-remote.remote-ssh
code --install-extension ms-vscode-remote.remote-ssh-edit
code --install-extension ms-vscode.remote-explorer
```

### 3. Conectar ao Servidor

**Opção A - VSCode UI:**
1. Abra a paleta de comandos: `Ctrl+Shift+P`
2. Digite: "Remote-SSH: Connect to Host..."
3. Selecione: "homelab-models"
4. Aguarde conexão

**Opção B - Terminal PowerShell:**
```powershell
ssh homelab@192.168.15.2
```

### 4. Usar Modelos no Copilot

Uma vez conectado remotamente ao servidor:
1. Abra um arquivo Python/código
2. Abra o Copilot Chat: `Ctrl+Shift+I`
3. Solicite completions/sugestões
4. O Copilot usará os modelos do servidor!

---

## 📁 Estrutura de Diretórios Esperada

```
/home/homelab/
├── models/              # Diretório principal de modelos
│   ├── llm/            # Modelos de linguagem
│   │   ├── model.gguf
│   │   ├── model.bin
│   │   └── ...
│   ├── embeddings/     # Modelos de embedding
│   │   ├── model.safetensors
│   │   └── ...
│   └── vision/         # Modelos de visão
│       ├── model.pt
│       └── ...
```

---

## 🔧 Configuração Manual (Se Necessário)

Se o script não detectar automaticamente, configure manualmente:

### A. SSH Config (`~/.ssh/config`)
```
Host homelab-models
    HostName 192.168.15.2
    User homelab
    Port 22
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

### B. VSCode Settings (`settings.json`)
```json
{
  "github.copilot.enable": {
    "*": true
  },
  "github.copilot.advanced": {
    "authorizationFallback": true,
    "authorizationFallbackTimeout": 100
  },
  "remote.SSH.configFile": "~/.ssh/config"
}
```

### C. Remote Settings no Servidor
Após conectar, crie `.vscode/settings.json` no servidor:
```json
{
  "python.defaultInterpreterPath": "/usr/bin/python3",
  "python.linting.enabled": true,
  "github.copilot.enable": true
}
```

---

## 🐛 Troubleshooting

### "Connection refused"
```powershell
# Verificar se SSH está acessível
Test-NetConnection -ComputerName 192.168.15.2 -Port 22
```

### "Permission denied"
```powershell
# Testar conexão manual
ssh -vvv homelab@192.168.15.2
```

### Modelos não aparecem
1. Verifique o caminho dos modelos no servidor:
```bash
ssh homelab@192.168.15.2 'find /home/homelab/models -type f | head -10'
```

2. Ajuste o caminho no script:
```powershell
.\setup_copilot_models_ssh.ps1 -ModelsPath "/seu/caminho/customizado"
```

### VSCode não reconhece modelos remotos
1. Reinicie VSCode
2. Execute: `Remote-SSH: Kill VS Code Server on Host`
3. Reconecte

---

## 📊 Verificar Modelos Disponíveis

No terminal remoto do VSCode:
```bash
# Listar todos os modelos
find /home/homelab/models -type f

# Verificar tamanho
du -sh /home/homelab/models

# Listar modelos por tipo
ls -la /home/homelab/models/*.gguf
ls -la /home/homelab/models/*.bin
ls -la /home/homelab/models/*.safetensors
```

---

## 🎯 Casos de Uso

### 1. Code Completion Remoto
```python
# Começar a digitar, Copilot sugerirá usando modelos do servidor
def process_trading_data(df):
    # Copilot sugere implementação completa aqui
```

### 2. Chat IA Remoto
`Ctrl+Shift+I` → "Explique esse código de trading"
→ Modelo do servidor processa a pergunta

### 3. Multi-File Analysis
Perguntar sobre múltiplos arquivos:
"Qual é a arquitetura geral do bot de trading?"
→ Modelo analisa todos os arquivos remotamente

---

## ⚡ Performance Tips

- **Latência**: Use WiFi 5GHz ou Ethernet para melhor performance
- **Conexão Persistente**: O VSCode mantém conexão SSH aberta
- **Modelos Grandes**: Se usar modelos `>10GB`, considere SSD no servidor
- **GPU**: Certifique-se de que GPU está configurada no servidor

```bash
# Verificar GPU no servidor
nvidia-smi

# Se não vir saída, configure CUDA/cuDNN
```

---

## 📝 Notas Importantes

⚠️ **Segurança:**
- Mude a senha "homelab" para algo seguro
- Use chaves SSH em vez de senhas:
```powershell
ssh-keygen -t ed25519 -f ~/.ssh/homelab_key
# Copiar chave pública para servidor:
ssh-copy-id -i ~/.ssh/homelab_key.pub homelab@192.168.15.2
```

✅ **Boas Práticas:**
- Mantenha o servidor atualizado (`apt update && apt upgrade`)
- Monitore uso de GPU/CPU
- Faça backup dos modelos regularmente
- Documente quais modelos estão instalados

---

## 📚 Recursos Adicionais

- [VSCode Remote SSH Docs](https://code.visualstudio.com/docs/remote/ssh)
- [GitHub Copilot Settings](https://docs.github.com/en/copilot/configuring-github-copilot)
- [OpenSSH on Windows](https://docs.microsoft.com/en-us/windows-server/administration/openssh/openssh_overview)

---

**Última atualização:** 5 de janeiro de 2026  
**Script:** `setup_copilot_models_ssh.ps1`  
**Config:** `vscode_copilot_config.json`
