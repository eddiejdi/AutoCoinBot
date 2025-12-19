# reserve_fund_manager.py
"""
Gerencia a reserva de fundos e negociação até atingir lucro X%

Funcionalidades:
1. Consulta saldo disponível via API KuCoin
2. Reserva % do saldo
3. Efetua compra com aquele valor
4. Negocia até atingir X% de lucro
"""

import logging
import time
from typing import Dict, Optional, Any
from decimal import Decimal

try:
    from . import api
except ImportError:
    import api

logger = logging.getLogger(__name__)


class ReserveFundManager:
    """Gerencia reserva de fundos e negociação até lucro"""
    
    def __init__(self, logger: logging.Logger = None):
        """
        Inicializa o gerenciador
        
        Args:
            logger: Logger para registrar eventos
        """
        self.logger = logger or logging.getLogger(__name__)
        self.reserved_amount = 0.0
        self.purchase_price = 0.0
        self.purchased_amount = 0.0
        self.entry_price = 0.0
    
    def get_usdt_balance(self) -> float:
        """
        Consulta saldo disponível em USDT
        
        Returns:
            float: Saldo em USDT
        """
        try:
            balances = api.get_balances(account_type="trade")
            for balance in balances:
                if balance.get("currency") == "USDT":
                    available = balance.get("available", 0.0)
                    self.logger.info(f"💰 Saldo disponível em USDT: {available}")
                    return float(available)
            
            self.logger.warning("⚠️ Nenhum saldo USDT encontrado")
            return 0.0
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao consultar saldo USDT: {e}")
            return 0.0
    
    def reserve_fund_percentage(self, percentage: float) -> float:
        """
        Reserva uma % do saldo USDT disponível
        
        Args:
            percentage: % do saldo a reservar (0-100)
        
        Returns:
            float: Valor reservado em USDT
        """
        if not 0 < percentage <= 100:
            raise ValueError(f"Porcentagem deve estar entre 0 e 100, recebido: {percentage}")
        
        available_balance = self.get_usdt_balance()
        
        if available_balance <= 0:
            self.logger.error(f"❌ Saldo insuficiente para reservar {percentage}%")
            raise ValueError(f"Saldo USDT insuficiente: {available_balance}")
        
        # Calcula 99% do saldo para evitar problemas de taxa/rounding
        reserve_multiplier = min(percentage / 100.0, 0.99)
        self.reserved_amount = available_balance * reserve_multiplier
        
        self.logger.info(f"✅ Reservado {percentage}% ({self.reserved_amount:.2f} USDT) do saldo")
        
        return self.reserved_amount
    
    def purchase_with_reserved_funds(self, symbol: str, entry_price: float) -> Dict[str, Any]:
        """
        Efetua compra de moeda usando fundos reservados
        
        Args:
            symbol: Par de trading (ex: BTC-USDT)
            entry_price: Preço de entrada esperado
        
        Returns:
            dict: Informações da compra (amount, price, order_id)
        """
        if self.reserved_amount <= 0:
            raise ValueError("❌ Nenhum fundo reservado. Execute reserve_fund_percentage() primeiro")
        
        self.entry_price = entry_price
        
        try:
            self.logger.info(f"📊 Executando compra: {symbol} com {self.reserved_amount:.2f} USDT")
            
            result = api.place_market_order(
                symbol=symbol,
                side="buy",
                funds=self.reserved_amount
            )
            
            order_id = result.get("data", {}).get("orderId", "unknown")
            
            # Estima quantidade comprada baseado no preço
            estimated_quantity = self.reserved_amount / entry_price
            self.purchased_amount = estimated_quantity
            self.purchase_price = entry_price
            
            self.logger.info(
                f"✅ Compra executada! "
                f"Ordem ID: {order_id} | "
                f"Quantidade estimada: {estimated_quantity:.8f} {symbol.split('-')[0]}"
            )
            
            return {
                "order_id": order_id,
                "symbol": symbol,
                "side": "buy",
                "funds_used": self.reserved_amount,
                "quantity": estimated_quantity,
                "price": entry_price,
                "timestamp": time.time()
            }
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao executar compra: {e}")
            raise
    
    def calculate_profit_percentage(self, current_price: float) -> float:
        """
        Calcula % de lucro/prejuízo atual
        
        Args:
            current_price: Preço atual do ativo
        
        Returns:
            float: % de lucro (positivo) ou prejuízo (negativo)
        """
        if self.purchase_price <= 0 or self.purchased_amount <= 0:
            return 0.0
        
        # Lucro total = (preço_atual - preço_compra) * quantidade
        profit_per_unit = current_price - self.purchase_price
        total_profit = profit_per_unit * self.purchased_amount
        
        # % de lucro = (lucro_total / investimento_total) * 100
        profit_percentage = (total_profit / self.reserved_amount) * 100
        
        return profit_percentage
    
    def should_sell(self, current_price: float, target_profit_pct: float) -> bool:
        """
        Verifica se deve vender (atingiu lucro alvo)
        
        Args:
            current_price: Preço atual
            target_profit_pct: % de lucro alvo
        
        Returns:
            bool: True se deve vender
        """
        current_profit = self.calculate_profit_percentage(current_price)
        should_sell = current_profit >= target_profit_pct
        
        return should_sell
    
    def sell_with_profit(self, symbol: str, target_profit_pct: float, 
                        current_price: float) -> Optional[Dict[str, Any]]:
        """
        Vende moeda quando atingir lucro alvo
        
        Args:
            symbol: Par de trading
            target_profit_pct: % de lucro alvo
            current_price: Preço atual
        
        Returns:
            dict: Informações da venda ou None se não deve vender
        """
        if not self.should_sell(current_price, target_profit_pct):
            return None
        
        current_profit = self.calculate_profit_percentage(current_price)
        
        try:
            self.logger.info(
                f"💵 Vendendo {self.purchased_amount:.8f} {symbol.split('-')[0]} "
                f"a {current_price} USDT/unidade (lucro: {current_profit:.2f}%)"
            )
            
            result = api.place_market_order(
                symbol=symbol,
                side="sell",
                size=self.purchased_amount
            )
            
            order_id = result.get("data", {}).get("orderId", "unknown")
            total_received = self.purchased_amount * current_price
            realized_profit = total_received - self.reserved_amount
            
            self.logger.info(
                f"✅ Venda executada! "
                f"Ordem ID: {order_id} | "
                f"Lucro realizado: {realized_profit:.2f} USDT ({current_profit:.2f}%)"
            )
            
            return {
                "order_id": order_id,
                "symbol": symbol,
                "side": "sell",
                "quantity": self.purchased_amount,
                "price": current_price,
                "revenue": total_received,
                "profit": realized_profit,
                "profit_percentage": current_profit,
                "timestamp": time.time()
            }
        
        except Exception as e:
            self.logger.error(f"❌ Erro ao executar venda: {e}")
            raise
    
    def get_status(self, current_price: float = 0.0) -> Dict[str, Any]:
        """
        Retorna status atual da posição
        
        Args:
            current_price: Preço atual para cálculo de lucro
        
        Returns:
            dict: Status completo
        """
        profit_pct = self.calculate_profit_percentage(current_price) if current_price > 0 else 0.0
        current_value = (self.purchased_amount * current_price) if current_price > 0 else 0.0
        
        return {
            "reserved_amount": self.reserved_amount,
            "purchase_price": self.purchase_price,
            "purchased_amount": self.purchased_amount,
            "entry_price": self.entry_price,
            "current_price": current_price,
            "current_value": current_value,
            "profit_percentage": profit_pct,
            "invested": self.reserved_amount,
            "unrealized_profit": current_value - self.reserved_amount
        }


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    manager = ReserveFundManager()
    
    print("\n" + "="*60)
    print("📊 DEMO: Reserve Fund Manager")
    print("="*60 + "\n")
    
    # Simula uso
    try:
        balance = manager.get_usdt_balance()
        if balance > 0:
            reserved = manager.reserve_fund_percentage(50)  # 50% do saldo
            print(f"✅ Reservado: {reserved:.2f} USDT\n")
            
            # Status inicial
            status = manager.get_status()
            print(f"Status inicial: {status}\n")
    
    except Exception as e:
        print(f"Erro na demo: {e}\n")
