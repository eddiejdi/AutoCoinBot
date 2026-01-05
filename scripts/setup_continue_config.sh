#!/bin/bash
# Script para configurar Continue com Ollama do servidor homelab

mkdir -p ~/.continue

cat > ~/.continue/config.json << 'EOF'
{
  "models": [
    {
      "title": "Llama 3.1 8B (Homelab 4-core)",
      "provider": "ollama",
      "model": "llama3.1-4core",
      "apiBase": "http://192.168.15.2:11434"
    },
    {
      "title": "Dolphin Mistral 7B (Homelab 4-core)",
      "provider": "ollama",
      "model": "dolphin-mistral-4core",
      "apiBase": "http://192.168.15.2:11434"
    },
    {
      "title": "Uncensored Llama3 (Homelab 4-core)",
      "provider": "ollama",
      "model": "uncensored-llama3-4core",
      "apiBase": "http://192.168.15.2:11434"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Llama 3.1 Autocomplete",
    "provider": "ollama",
    "model": "llama3.1-4core",
    "apiBase": "http://192.168.15.2:11434"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "llama3.1-4core",
    "apiBase": "http://192.168.15.2:11434"
  },
  "allowAnonymousTelemetry": false,
  "docs": []
}
EOF

echo "Configuração do Continue criada em ~/.continue/config.json"
cat ~/.continue/config.json
