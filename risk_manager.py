# kucoin_app/risk_manager.py
# Advanced risk management with circuit breakers and portfolio limits

import logging
import time
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from . import api
from .database import db

logger = logging.getLogger(__name__)

class RiskManager:
    """Manages trading risks and enforces limits"""
    
    def __init__(self):
        # Daily limits
        self.max_daily_loss_pct = 5.0  # Max 5% daily loss
        self.max_daily_trades = 50
        self.max_position_size_pct = 10.0  # Max 10% of portfolio per position
        
        # Circuit breaker
        self.circuit_breaker_active = False
        self.circuit_breaker_until = None
        self.consecutive_losses = 0
        self.max_consecutive_losses = 5
        
        # Position limits
        self.max_open_positions = 5
        self.min_liquidity_usd = 100  # Min $100 liquidity to trade
        
        # Drawdown tracking
        self.peak_equity = None
        self.max_drawdown_pct = 20.0  # Max 20% drawdown from peak
        
    def validate_trade(self, symbol: str, side: str, size: float, 
                       funds: float = None) -> Tuple[bool, str]:
        """
        Validate if trade meets risk criteria
        
        Returns:
            (is_valid, message)
        """
        
        # Check circuit breaker
        if self.circuit_breaker_active:
            if self.circuit_breaker_until and time.time() < self.circuit_breaker_until:
                return False, f"Circuit breaker active until {datetime.fromtimestamp(self.circuit_breaker_until)}"
            else:
                self._reset_circuit_breaker()
        
        # Check daily trade limit
        daily_trades = self._get_daily_trade_count()
        if daily_trades >= self.max_daily_trades:
            return False, f"Daily trade limit reached ({self.max_daily_trades})"
        
        # Check daily loss limit
        daily_pnl_pct = self._get_daily_pnl_pct()
        if daily_pnl_pct <= -self.max_daily_loss_pct:
            self._activate_circuit_breaker(hours=24)
            return False, f"Daily loss limit reached ({self.max_daily_loss_pct}%)"
        
        # Check position size limit
        try:
            current_balance = api.get_balance()
            position_value = funds if funds else (size * api.get_price(symbol))
            position_pct = (position_value / current_balance) * 100 if current_balance > 0 else 0
            
            if position_pct > self.max_position_size_pct:
                return False, f"Position size ({position_pct:.1f}%) exceeds limit ({self.max_position_size_pct}%)"
        except Exception as e:
            logger.warning(f"Could not validate position size: {e}")
        
        # Check open positions limit
        active_bots = db.get_active_bots()
        if len(active_bots) >= self.max_open_positions:
            return False, f"Maximum open positions reached ({self.max_open_positions})"
        
        # Check liquidity
        try:
            orderbook = api.get_orderbook_price(symbol)
            bid = orderbook.get('best_bid')
            ask = orderbook.get('best_ask')
            
            if not bid or not ask:
                return False, f"Insufficient liquidity data for {symbol}"
            
            spread = ask - bid
            spread_pct = (spread / ask) * 100
            
            if spread_pct > 1.0:  # More than 1% spread
                return False, f"Spread too wide ({spread_pct:.2f}%)"
                
        except Exception as e:
            logger.warning(f"Could not check liquidity: {e}")
        
        # Check drawdown limit
        if not self._check_drawdown_limit():
            self._activate_circuit_breaker(hours=24)
            return False, f"Maximum drawdown exceeded ({self.max_drawdown_pct}%)"
        
        return True, "Trade approved"
    
    def record_trade_result(self, profit: float):
        """Record trade result for tracking consecutive losses"""
        if profit < 0:
            self.consecutive_losses += 1
            if self.consecutive_losses >= self.max_consecutive_losses:
                self._activate_circuit_breaker(hours=1)
                logger.warning(f"Circuit breaker activated: {self.consecutive_losses} consecutive losses")
        else:
            self.consecutive_losses = 0
    
    def _get_daily_trade_count(self) -> int:
        """Get number of trades today"""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_ts = today_start.timestamp()
            trades = db.get_trades(start_ts=start_ts, limit=1000)
            return len(trades)
        except Exception as e:
            logger.error(f"Error getting daily trade count: {e}")
            return 0
    
    def _get_daily_pnl_pct(self) -> float:
        """Get today's PnL as percentage"""
        try:
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            start_ts = today_start.timestamp()
            trades = db.get_trades(start_ts=start_ts, limit=1000)
            
            total_pnl = sum(t.get('profit', 0) for t in trades)
            current_balance = api.get_balance()
            
            if current_balance <= 0:
                return 0.0
            
            pnl_pct = (total_pnl / current_balance) * 100
            return pnl_pct
        except Exception as e:
            logger.error(f"Error calculating daily PnL: {e}")
            return 0.0
    
    def _check_drawdown_limit(self) -> bool:
        """Check if current drawdown exceeds limit"""
        try:
            current_balance = api.get_balance()
            
            if self.peak_equity is None:
                self.peak_equity = current_balance
                return True
            
            if current_balance > self.peak_equity:
                self.peak_equity = current_balance
                return True
            
            drawdown_pct = ((self.peak_equity - current_balance) / self.peak_equity) * 100
            
            if drawdown_pct > self.max_drawdown_pct:
                logger.error(f"Maximum drawdown exceeded: {drawdown_pct:.2f}%")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error checking drawdown: {e}")
            return True
    
    def _activate_circuit_breaker(self, hours: int = 1):
        """Activate circuit breaker for specified hours"""
        self.circuit_breaker_active = True
        self.circuit_breaker_until = time.time() + (hours * 3600)
        logger.warning(f"Circuit breaker activated for {hours} hours")
        
        # Record metric
        db.add_risk_metric('circuit_breaker_activated', 1.0)
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker"""
        self.circuit_breaker_active = False
        self.circuit_breaker_until = None
        self.consecutive_losses = 0
        logger.info("Circuit breaker reset")
    
    def get_risk_status(self) -> Dict:
        """Get current risk status"""
        daily_pnl_pct = self._get_daily_pnl_pct()
        daily_trades = self._get_daily_trade_count()
        active_bots = len(db.get_active_bots())
        
        try:
            current_balance = api.get_balance()
            drawdown_pct = 0.0
            if self.peak_equity and self.peak_equity > 0:
                drawdown_pct = ((self.peak_equity - current_balance) / self.peak_equity) * 100
        except:
            current_balance = 0.0
            drawdown_pct = 0.0
        
        return {
            'circuit_breaker_active': self.circuit_breaker_active,
            'circuit_breaker_until': self.circuit_breaker_until,
            'consecutive_losses': self.consecutive_losses,
            'daily_pnl_pct': round(daily_pnl_pct, 2),
            'daily_trades': daily_trades,
            'active_positions': active_bots,
            'current_balance': round(current_balance, 2),
            'peak_equity': round(self.peak_equity, 2) if self.peak_equity else 0,
            'current_drawdown_pct': round(drawdown_pct, 2),
            'limits': {
                'max_daily_loss_pct': self.max_daily_loss_pct,
                'max_daily_trades': self.max_daily_trades,
                'max_position_size_pct': self.max_position_size_pct,
                'max_open_positions': self.max_open_positions,
                'max_drawdown_pct': self.max_drawdown_pct,
                'max_consecutive_losses': self.max_consecutive_losses
            }
        }
    
    def update_limits(self, **kwargs):
        """Update risk limits"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.info(f"Risk limit updated: {key} = {value}")

# Global instance
risk_manager = RiskManager()
