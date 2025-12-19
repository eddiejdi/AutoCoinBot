# kucoin_app/backtest.py
# Backtesting engine for strategy validation

import pandas as pd
import numpy as np
import logging
from typing import List, Tuple, Dict, Any
from datetime import datetime, timedelta
from . import api

logger = logging.getLogger(__name__)

class BacktestEngine:
    """Backtest trading strategies on historical data"""
    
    def __init__(self, symbol: str, start_date: datetime, end_date: datetime,
                 initial_capital: float = 10000.0):
        self.symbol = symbol
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        
        # Results
        self.trades = []
        self.equity_curve = []
        self.metrics = {}
        
    def fetch_historical_data(self) -> pd.DataFrame:
        """Fetch historical candle data"""
        logger.info(f"Fetching historical data for {self.symbol}")
        
        start_ts = int(self.start_date.timestamp())
        end_ts = int(self.end_date.timestamp())
        
        try:
            candles = api.get_candles_safe(
                self.symbol,
                ktype='1hour',
                startAt=start_ts,
                endAt=end_ts
            )
            
            if not candles:
                raise ValueError("No historical data available")
            
            df = pd.DataFrame(
                candles,
                columns=['timestamp', 'open', 'close', 'high', 'low', 'volume', 'amount']
            )
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values('timestamp')
            
            # Calculate indicators
            df['MA9'] = df['close'].rolling(window=9).mean()
            df['MA21'] = df['close'].rolling(window=21).mean()
            
            # RSI
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
            
            logger.info(f"Fetched {len(df)} candles")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            raise
    
    def run_strategy(self, df: pd.DataFrame, strategy_params: Dict) -> Dict:
        """
        Run backtest with given strategy parameters
        
        Strategy params example:
        {
            'entry_mode': 'ma_cross',  # or 'rsi_oversold'
            'exit_mode': 'target',     # or 'ma_cross_back'
            'target_pct': 2.5,
            'stop_loss_pct': -1.5,
            'position_size_pct': 10.0
        }
        """
        logger.info(f"Running backtest with strategy: {strategy_params}")
        
        capital = self.initial_capital
        position = None
        trades = []
        equity = []
        
        for i in range(len(df)):
            row = df.iloc[i]
            
            # Record equity
            if position:
                current_value = capital + (position['size'] * row['close'])
            else:
                current_value = capital
            
            equity.append({
                'timestamp': row['timestamp'],
                'equity': current_value
            })
            
            # Skip if indicators not ready
            if pd.isna(row['MA9']) or pd.isna(row['MA21']) or pd.isna(row['RSI']):
                continue
            
            # Entry logic
            if position is None:
                entry_signal = self._check_entry_signal(df, i, strategy_params)
                
                if entry_signal:
                    position_size = (capital * strategy_params.get('position_size_pct', 10) / 100) / row['close']
                    
                    position = {
                        'entry_price': row['close'],
                        'entry_time': row['timestamp'],
                        'size': position_size,
                        'entry_idx': i
                    }
                    
                    capital -= position_size * row['close']
                    logger.debug(f"Entry @ {row['close']:.2f} on {row['timestamp']}")
            
            # Exit logic
            else:
                exit_signal, exit_reason = self._check_exit_signal(
                    df, i, position, strategy_params
                )
                
                if exit_signal:
                    exit_price = row['close']
                    exit_value = position['size'] * exit_price
                    profit = exit_value - (position['size'] * position['entry_price'])
                    profit_pct = (profit / (position['size'] * position['entry_price'])) * 100
                    
                    capital += exit_value
                    
                    trade = {
                        'entry_time': position['entry_time'],
                        'entry_price': position['entry_price'],
                        'exit_time': row['timestamp'],
                        'exit_price': exit_price,
                        'size': position['size'],
                        'profit': profit,
                        'profit_pct': profit_pct,
                        'exit_reason': exit_reason,
                        'duration': (row['timestamp'] - position['entry_time']).total_seconds() / 3600
                    }
                    
                    trades.append(trade)
                    position = None
                    
                    logger.debug(f"Exit @ {exit_price:.2f} | Profit: {profit:.2f} ({profit_pct:.2f}%) | Reason: {exit_reason}")
        
        # Close any open position at end
        if position:
            final_row = df.iloc[-1]
            exit_value = position['size'] * final_row['close']
            profit = exit_value - (position['size'] * position['entry_price'])
            capital += exit_value
            
            trades.append({
                'entry_time': position['entry_time'],
                'entry_price': position['entry_price'],
                'exit_time': final_row['timestamp'],
                'exit_price': final_row['close'],
                'size': position['size'],
                'profit': profit,
                'profit_pct': (profit / (position['size'] * position['entry_price'])) * 100,
                'exit_reason': 'end_of_backtest',
                'duration': (final_row['timestamp'] - position['entry_time']).total_seconds() / 3600
            })
        
        self.trades = trades
        self.equity_curve = equity
        
        # Calculate metrics
        self.metrics = self._calculate_metrics(trades, equity)
        
        return self.metrics
    
    def _check_entry_signal(self, df: pd.DataFrame, idx: int, params: Dict) -> bool:
        """Check for entry signal"""
        row = df.iloc[idx]
        prev_row = df.iloc[idx - 1] if idx > 0 else None
        
        if params['entry_mode'] == 'ma_cross':
            # MA9 crosses above MA21
            if prev_row is not None:
                return (prev_row['MA9'] <= prev_row['MA21'] and 
                       row['MA9'] > row['MA21'])
        
        elif params['entry_mode'] == 'rsi_oversold':
            # RSI below 30
            return row['RSI'] < 30
        
        elif params['entry_mode'] == 'rsi_and_ma':
            # RSI below 40 AND price below MA9
            return row['RSI'] < 40 and row['close'] < row['MA9']
        
        return False
    
    def _check_exit_signal(self, df: pd.DataFrame, idx: int, 
                          position: Dict, params: Dict) -> Tuple[bool, str]:
        """Check for exit signal"""
        row = df.iloc[idx]
        entry_price = position['entry_price']
        
        # Stop loss
        stop_loss_pct = params.get('stop_loss_pct', -5.0)
        current_pnl_pct = ((row['close'] - entry_price) / entry_price) * 100
        
        if current_pnl_pct <= stop_loss_pct:
            return True, 'stop_loss'
        
        # Target
        if params['exit_mode'] == 'target':
            target_pct = params.get('target_pct', 2.5)
            if current_pnl_pct >= target_pct:
                return True, 'target'
        
        # MA cross back
        elif params['exit_mode'] == 'ma_cross_back':
            prev_row = df.iloc[idx - 1] if idx > 0 else None
            if prev_row:
                if prev_row['MA9'] >= prev_row['MA21'] and row['MA9'] < row['MA21']:
                    return True, 'ma_cross_back'
        
        # Trailing stop
        trailing_stop_pct = params.get('trailing_stop_pct')
        if trailing_stop_pct:
            # Calculate peak since entry
            entry_idx = position['entry_idx']
            peak_price = df.iloc[entry_idx:idx+1]['close'].max()
            trailing_threshold = peak_price * (1 - trailing_stop_pct / 100)
            
            if row['close'] <= trailing_threshold:
                return True, 'trailing_stop'
        
        return False, ''
    
    def _calculate_metrics(self, trades: List[Dict], equity: List[Dict]) -> Dict:
        """Calculate performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'total_profit': 0,
                'total_return_pct': 0,
                'sharpe_ratio': 0,
                'max_drawdown_pct': 0,
                'profit_factor': 0
            }
        
        df_trades = pd.DataFrame(trades)
        df_equity = pd.DataFrame(equity)
        
        # Basic metrics
        total_trades = len(trades)
        winning_trades = len(df_trades[df_trades['profit'] > 0])
        losing_trades = len(df_trades[df_trades['profit'] <= 0])
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_profit = df_trades['profit'].sum()
        final_equity = df_equity['equity'].iloc[-1]
        total_return_pct = ((final_equity - self.initial_capital) / self.initial_capital) * 100
        
        # Profit factor
        total_wins = df_trades[df_trades['profit'] > 0]['profit'].sum()
        total_losses = abs(df_trades[df_trades['profit'] <= 0]['profit'].sum())
        profit_factor = total_wins / total_losses if total_losses > 0 else 0
        
        # Sharpe ratio (simplified - assumes daily returns)
        df_equity['returns'] = df_equity['equity'].pct_change()
        returns_mean = df_equity['returns'].mean()
        returns_std = df_equity['returns'].std()
        sharpe_ratio = (returns_mean / returns_std) * np.sqrt(252) if returns_std > 0 else 0
        
        # Max drawdown
        df_equity['peak'] = df_equity['equity'].cummax()
        df_equity['drawdown'] = (df_equity['equity'] - df_equity['peak']) / df_equity['peak']
        max_drawdown_pct = df_equity['drawdown'].min() * 100
        
        # Average metrics
        avg_profit = df_trades['profit'].mean()
        avg_win = df_trades[df_trades['profit'] > 0]['profit'].mean() if winning_trades > 0 else 0
        avg_loss = df_trades[df_trades['profit'] <= 0]['profit'].mean() if losing_trades > 0 else 0
        avg_duration = df_trades['duration'].mean()
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_return_pct': total_return_pct,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown_pct': max_drawdown_pct,
            'profit_factor': profit_factor,
            'avg_profit': avg_profit,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_duration_hours': avg_duration,
            'final_equity': final_equity
        }
    
    def get_results_dataframe(self) -> pd.DataFrame:
        """Get trades as DataFrame"""
        return pd.DataFrame(self.trades)
    
    def get_equity_dataframe(self) -> pd.DataFrame:
        """Get equity curve as DataFrame"""
        return pd.DataFrame(self.equity_curve)

def run_backtest(symbol: str, days_back: int = 30, 
                strategy_params: Dict = None) -> Dict:
    """
    Convenience function to run a backtest
    
    Args:
        symbol: Trading pair
        days_back: Number of days of historical data
        strategy_params: Strategy configuration
    
    Returns:
        Dictionary with metrics and DataFrames
    """
    if strategy_params is None:
        strategy_params = {
            'entry_mode': 'ma_cross',
            'exit_mode': 'target',
            'target_pct': 2.5,
            'stop_loss_pct': -1.5,
            'trailing_stop_pct': 1.0,
            'position_size_pct': 10.0
        }
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    backtest = BacktestEngine(symbol, start_date, end_date)
    
    try:
        df = backtest.fetch_historical_data()
        metrics = backtest.run_strategy(df, strategy_params)
        
        return {
            'metrics': metrics,
            'trades': backtest.get_results_dataframe(),
            'equity': backtest.get_equity_dataframe(),
            'symbol': symbol,
            'start_date': start_date,
            'end_date': end_date
        }
    except Exception as e:
        logger.error(f"Backtest failed: {e}")
        return {
            'error': str(e),
            'metrics': {},
            'trades': pd.DataFrame(),
            'equity': pd.DataFrame()
        }
