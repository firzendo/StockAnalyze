"""
Backtester Module - Backtest trading strategies with different BIAS entry points
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class Backtester:
    """Class to backtest trading strategies"""
    
    @staticmethod
    def backtest_bias_strategy(df: pd.DataFrame, 
                               bias_thresholds: List[float],
                               holding_days: int = 5) -> Dict:
        """
        Backtest BIAS entry strategy with different thresholds
        
        Args:
            df: DataFrame with OHLCV and BIAS indicator
            bias_thresholds: List of BIAS% entry points to test
            holding_days: Number of days to hold the position
            
        Returns:
            Dictionary with backtest results for each threshold
        """
        results = {}
        
        # Ensure we have the required columns
        if 'BIAS' not in df.columns or 'Close' not in df.columns:
            logger.warning("DataFrame missing required columns (BIAS or Close)")
            return results
        
        for threshold in bias_thresholds:
            trades = []
            in_position = False
            entry_price = 0.0
            entry_idx = 0
            
            for idx in range(len(df)):
                current_row = df.iloc[idx]
                
                # Extract scalar values safely
                try:
                    bias = float(current_row['BIAS']) if 'BIAS' in current_row.index else float('nan')
                    close = float(current_row['Close']) if 'Close' in current_row.index else float('nan')
                except (ValueError, TypeError):
                    continue
                
                if np.isnan(bias) or np.isnan(close):
                    continue
                
                if not in_position:
                    # Entry signal
                    if bias < threshold:  # Oversold condition
                        entry_price = close
                        entry_idx = idx
                        in_position = True
                else:
                    # Exit conditions
                    exit_reason = None
                    days_held = idx - entry_idx
                    
                    if days_held >= holding_days:
                        exit_reason = f"Held {holding_days} days"
                    
                    if exit_reason:
                        exit_price = close
                        profit = exit_price - entry_price
                        profit_pct = (profit / entry_price) * 100 if entry_price != 0 else 0
                        
                        trades.append({
                            'entry_date': df.index[entry_idx],
                            'exit_date': df.index[idx],
                            'entry_price': entry_price,
                            'exit_price': exit_price,
                            'profit': profit,
                            'profit_pct': profit_pct,
                            'exit_reason': exit_reason,
                            'days_held': days_held,
                            'is_win': profit > 0
                        })
                        in_position = False
            
            # Calculate statistics
            if trades:
                total_trades = len(trades)
                winning_trades = sum(1 for t in trades if t['is_win'])
                losing_trades = total_trades - winning_trades
                win_rate = (winning_trades / total_trades) * 100
                avg_profit = np.mean([t['profit_pct'] for t in trades])
                total_profit = sum(t['profit_pct'] for t in trades)
            else:
                total_trades = 0
                winning_trades = 0
                losing_trades = 0
                win_rate = 0
                avg_profit = 0
                total_profit = 0
            
            results[threshold] = {
                'bias_threshold': threshold,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'avg_profit_pct': avg_profit,
                'total_profit_pct': total_profit,
                'trades': trades
            }
        
        return results
    
    @staticmethod
    def find_optimal_bias(backtest_results: Dict) -> Tuple[float, Dict]:
        """
        Find the BIAS threshold with highest win rate
        
        Args:
            backtest_results: Dictionary from backtest_bias_strategy
            
        Returns:
            Tuple of (optimal_bias_threshold, results_for_threshold)
        """
        # Filter results with at least 5 trades for statistical significance
        valid_results = {
            k: v for k, v in backtest_results.items() 
            if v['total_trades'] >= 5
        }
        
        if not valid_results:
            logger.warning("No valid results with minimum 5 trades")
            # Return result with most trades
            valid_results = backtest_results
        
        # Find best by win rate, then by average profit
        optimal = max(
            valid_results.items(),
            key=lambda x: (x[1]['win_rate'], x[1]['avg_profit_pct'])
        )
        
        return optimal[0], optimal[1]
    
    @staticmethod
    def format_backtest_results(backtest_results: Dict) -> str:
        """
        Format backtest results for display
        
        Args:
            backtest_results: Dictionary from backtest_bias_strategy
            
        Returns:
            Formatted string for display
        """
        output = []
        output.append("\n" + "="*80)
        output.append("📊 BIAS 策略回測結果")
        output.append("="*80)
        
        # Sort by win rate
        sorted_results = sorted(
            backtest_results.items(),
            key=lambda x: x[1]['win_rate'],
            reverse=True
        )
        
        output.append(f"{'BIAS%':<8} {'交易數':<8} {'勝率':<8} {'平均獲利%':<12} {'總獲利%':<12}")
        output.append("-"*80)
        
        for bias_threshold, result in sorted_results:
            output.append(
                f"{bias_threshold:<8.2f} "
                f"{result['total_trades']:<8} "
                f"{result['win_rate']:<8.1f}% "
                f"{result['avg_profit_pct']:<12.2f}% "
                f"{result['total_profit_pct']:<12.2f}%"
            )
        
        # Find and highlight optimal
        optimal_bias, optimal_result = Backtester.find_optimal_bias(backtest_results)
        
        output.append("\n" + "="*80)
        output.append(f"🎯 最優 BIAS 進場點: {optimal_bias:.2f}%")
        output.append(f"   勝率: {optimal_result['win_rate']:.1f}%")
        output.append(f"   交易數: {optimal_result['total_trades']}")
        output.append(f"   平均獲利: {optimal_result['avg_profit_pct']:.2f}%")
        output.append("="*80 + "\n")
        
        return "\n".join(output)
