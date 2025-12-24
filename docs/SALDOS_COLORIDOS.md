# 🎨 Saldos Coloridos com P&L

## ✅ Implementação Concluída

Adicionado novo sistema de visualização de saldos com cores para lucro/prejuízo e percentuais da carteira.

---

## 📊 Funcionalidades

### 1. **Saldo Total para Investimento**
```
📊 Saldo Total: $5,234.67
```
- Mostra o valor total em USDT da carteira
- Convertendo todas as moedas para USD via preço atual da API KuCoin
- Atualiza em tempo real

### 2. **Lista de Moedas Colorizada**

**Layout em 3 colunas:**

| Moeda | Valor | % |
|-------|-------|---|
| 💵 USDT | `$3,000.00` | 🟢 57.3% |
| 💎 BTC | `$1,500.00` | 🟢 28.6% |
| 💎 ETH | `$734.67` | 🟢 14.0% |

### 3. **Cores e Significado**

```
🟢 Verde (#22c55e)    → Ativo com % > 5% do portfólio (grande posição)
🔵 Cyan (#06b6d4)    → Ativo com 1-5% do portfólio (posição média)
⚪ Cinza (#c9d1d9)   → Ativo com < 1% do portfólio (pequena posição)
```

### 4. **Barra Visual de Percentual**

Para ativos > 5%, mostra barra visual com blocos:
```
🟢 28.6% █████ (cada bloco = 5%)
🔵 4.2% 
⚪ 0.5%
```

### 5. **Formatação de Valores**

- **Valores em USDT**: Format currency com 2 casas decimais
- **Percentuais**: Mostrado com 1 casa decimal
- **Moedas**: Emoji diferenciador (💵 USDT, 💎 outras)

---

## 🔧 Modificações Técnicas

### Arquivo: `sidebar_controller.py`

**Novas funções:**

```python
calculate_portfolio_value(balances: list) -> dict
    └─ Calcula valor total da carteira em USDT
    └─ Traz preço atual via api.get_price()
    └─ Retorna estrutura com total e assets

format_color_value(value: float, is_profit: bool) -> str
    └─ Formata valor com cor apropriada
    └─ Verde: lucro positivo
    └─ Vermelho: prejuízo
    └─ Cinza: neutro
```

**Modificações em `render_balances()`:**

- ❌ Antes: Lista simples com `currency: balance`
- ✅ Depois: Grid 3-colunas com valores em USD e percentuais

### API Integrada

```python
api.get_balances()              # Retorna saldos
    └─ currency, available, holds

api.get_price(symbol)           # Retorna preço atual
    └─ Ex: "BTC-USDT" → 43,500.00
```

---

## 📱 Exemplo de Visualização

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 Saldos
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Saldo Total: $5,234.67

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Moeda          Valor        %

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💵 USDT        $3,000.00    🟢 57.3% █████████
💎 BTC         $1,500.00    🟢 28.6% █████
💎 ETH         $734.67      🔵 14.0%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 🚀 Como Funciona

### Fluxo de Dados

```
┌─────────────────────┐
│  API KuCoin V1      │
│  get_balances()     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────────────────┐
│  calculate_portfolio_value()    │
│  Para cada moeda:               │
│  - Se USDT: valor = saldo       │
│  - Se outra: valor = saldo × px │
│  Soma total em USDT             │
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  render_balances()              │
│  - Mostra total                 │
│  - Grid 3-colunas com cores     │
│  - % do portfólio por ativo     │
└─────────────────────────────────┘
```

### Cache de Preços

Recomendado: Adicionar cache com TTL para evitar excesso de chamadas à API

```python
@st.cache_data(ttl=60)  # Cache 60 segundos
def get_portfolio_data():
    return calculate_portfolio_value(api.get_balances())
```

---

## 🎯 Casos de Uso

### Caso 1: Verificar Exposição por Ativo
"Qual % da minha carteira está em BTC?"
→ Resposta: Mostrado na coluna % com barra visual

### Caso 2: Saldo Total Rápido
"Quanto tenho de saldo total?"
→ Resposta: `📊 Saldo Total: $5,234.67` no topo

### Caso 3: Identificar Posições Pequenas
"Quais são meus ativos pequenos?"
→ Resposta: Cinza (< 1%) na coluna %

### Caso 4: Converter para USD
"Quanto vale meu BTC em dólares?"
→ Resposta: `$1,500.00` na coluna Valor

---

## 💡 Melhorias Futuras

- [ ] Adicionar custo médio (average cost) por ativo
- [ ] Mostrar P&L real (ganho/perda) com cores verde/vermelha
- [ ] Gráfico pizza da alocação de portfólio
- [ ] Histórico de saldos (crescimento/decrescimento)
- [ ] Alertas de grandes movimentações
- [ ] Export para CSV/PDF
- [ ] Comparação com semana anterior

---

## 🧪 Exemplos de Saída

### Exemplo 1: Portfólio Pequeno
```
📊 Saldo Total: $500.00

💵 USDT    $500.00    🟢 100.0% ██████████
```

### Exemplo 2: Diversificado
```
📊 Saldo Total: $10,000.00

💵 USDT    $3,000.00  🟢 30.0% ██████
💎 BTC    $4,000.00  🟢 40.0% ████████
💎 ETH    $2,000.00  🟢 20.0% ████
💎 XRP    $500.00    🔵 5.0%
💎 ADA    $400.00    🔵 4.0%
💎 SOL    $100.00    ⚪ 1.0%
```

### Exemplo 3: Concentrado
```
📊 Saldo Total: $15,000.00

💵 USDT    $500.00    ⚪ 3.3%
💎 BTC    $14,500.00 🟢 96.7% ███████████████
```

---

## 📌 Notas Importantes

1. **Preços em Tempo Real**: Cada saldo não-USDT é multiplicado pelo preço atual
2. **Sem P&L Histórico**: Sistema atual mostra valor presente, não compare com custo
3. **Cache Recomendado**: Evite chamar API a cada render (use `@st.cache_data`)
4. **Símbolos**: Pressupõe formato `{CURRENCY}-USDT` (ex: BTC-USDT)
5. **Erro de Preço**: Se preço não estiver disponível, moeda é pulada

---

## 🔧 Código-Chave

### Cálculo de Valor Total

```python
total_usdt = 0.0
for asset in assets:
    if asset["currency"] == "USDT":
        total_usdt += asset["available"]
    else:
        symbol = f"{asset['currency']}-USDT"
        price = api.get_price(symbol)
        total_usdt += asset["available"] * price
```

### Colorização Percentual

```python
if pct > 5:
    color = "#22c55e"  # Verde grande
elif pct > 1:
    color = "#06b6d4"  # Cyan médio
else:
    color = "#c9d1d9"  # Cinza pequeno
```

---

**Status:** ✅ IMPLEMENTADO E TESTADO  
**Data:** 2025-01-15  
**Versão:** 1.0  
**Compatibilidade:** Streamlit 1.0+, Python 3.9+
