# log_colorizer.py
"""
Analisador de logs para extrair informações de lucro/prejuízo e colorir terminal

Regras de coloração:
- Verde: Lucro (positivo)
- Vermelho: Prejuízo (negativo)
- Amarelo: Informativo/Neutro (compra, vendas, info)
- Cyan: Ação importante
"""

import re
import json
from typing import Dict, Tuple, Optional
from decimal import Decimal

class LogColorizer:
    """Analisa logs e determina cores baseado em lucro/prejuízo"""
    
    # Padrões para extrair valores de lucro
    PROFIT_PATTERNS = [
        r'lucro:\s*([\d.]+)%',           # "lucro: 2.5%"
        r'profit:\s*([\d.]+)%',          # "profit: 2.5%"
        r'profit_percentage["\']?\s*:\s*([\d.-]+)',  # "profit_percentage": 2.5
        r'unrealized_profit["\']?\s*:\s*([\d.-]+)',  # "unrealized_profit": 5.25
        r'\+\s*([\d.]+)%',               # "+2.5%"
        r'-([\d.]+)%',                   # "-2.5%"
    ]
    
    # Padrões para eventos importantes
    EVENT_PATTERNS = {
        'compra': [r'compra executada|order placed.*buy|purchase.*complete'],
        'venda': [r'venda executada|order placed.*sell|sold'],
        'erro': [r'erro|error|❌|failed'],
        'sucesso': [r'sucesso|success|✅|concluído'],
    }
    
    @staticmethod
    def extract_profit(line: str) -> Optional[float]:
        """
        Extrai valor de lucro/prejuízo de uma linha de log
        
        Returns:
            float: Lucro (positivo) ou prejuízo (negativo), ou None
        """
        try:
            # Procura padrões de lucro
            for pattern in LogColorizer.PROFIT_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    # Se é prejuízo (com - no padrão), inverte
                    if '-' in pattern and value > 0:
                        value = -value
                    return value
            
            # Tenta parsear JSON na linha
            try:
                json_str = line[line.find('{'):line.rfind('}')+1]
                data = json.loads(json_str)
                
                if 'profit_percentage' in data:
                    return float(data['profit_percentage'])
                if 'unrealized_profit' in data and 'invested' in data:
                    profit = data['unrealized_profit']
                    invested = data['invested']
                    if invested > 0:
                        return (profit / invested) * 100
            except (json.JSONDecodeError, ValueError):
                pass
        
        except Exception as e:
            pass
        
        return None
    
    @staticmethod
    def get_line_color(line: str, profit_value: Optional[float] = None) -> str:
        """
        Determina cor da linha baseado no conteúdo e lucro
        
        Returns:
            str: Nome da classe CSS ('profit', 'loss', 'info', 'success', 'error', 'neutral')
        """
        if profit_value is not None:
            if profit_value > 0:
                return 'profit'
            elif profit_value < 0:
                return 'loss'
        
        # Verifica padrões de evento
        line_lower = line.lower()
        
        if any(re.search(p, line_lower) for p in LogColorizer.EVENT_PATTERNS['erro']):
            return 'error'
        
        if any(re.search(p, line_lower) for p in LogColorizer.EVENT_PATTERNS['sucesso']):
            return 'success'
        
        if any(re.search(p, line_lower) for p in LogColorizer.EVENT_PATTERNS['compra']):
            return 'info'
        
        if any(re.search(p, line_lower) for p in LogColorizer.EVENT_PATTERNS['venda']):
            return 'info'
        
        return 'neutral'
    
    @staticmethod
    def colorize_line(line: str) -> Tuple[str, str]:
        """
        Coloriza uma linha de log
        
        Args:
            line: Texto da linha
        
        Returns:
            Tuple: (classe_css, texto_linha)
        """
        profit = LogColorizer.extract_profit(line)
        color_class = LogColorizer.get_line_color(line, profit)
        return color_class, line
    
    @staticmethod
    def get_css_styles() -> str:
        """Retorna CSS para colorização do terminal"""
        return """
        <style>
            /* Cores do terminal */
            .log-profit {
                color: #22c55e !important;  /* Verde */
                font-weight: bold;
            }
            
            .log-loss {
                color: #ef4444 !important;  /* Vermelho */
                font-weight: bold;
            }
            
            .log-success {
                color: #22c55e !important;  /* Verde */
            }
            
            .log-error {
                color: #ef4444 !important;  /* Vermelho */
                font-weight: bold;
            }
            
            .log-info {
                color: #06b6d4 !important;  /* Cyan */
            }
            
            .log-neutral {
                color: #c9d1d9 !important;  /* Cinza padrão */
            }
            
            .log-warning {
                color: #f59e0b !important;  /* Amarelo */
            }
        </style>
        """


if __name__ == "__main__":
    # Test
    colorizer = LogColorizer()
    
    test_lines = [
        "✅ Compra executada com lucro: 2.5%",
        "❌ Prejuízo realizado: -1.5%",
        "📊 Preço atual: 88500 (profit: 2.3%)",
        '{"profit_percentage": 1.8, "unrealized_profit": 5.25, "invested": 50}',
        "[INFO] Bot iniciado com sucesso",
        "Aguardando próxima análise",
    ]
    
    print("🎨 LOG COLORIZER TEST\n")
    for line in test_lines:
        css_class, colored_line = colorizer.colorize_line(line)
        profit = colorizer.extract_profit(line)
        print(f"[{css_class:10}] {line}")
        if profit is not None:
            print(f"             → Lucro: {profit:+.2f}%\n")
