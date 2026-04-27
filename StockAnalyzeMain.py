"""
Stock Analysis Main Program
自動分析股票 EMA/BIAS，并显示"今天可不可以买"
支持回测找出最优 BIAS 进场点
"""
import sys
import os

# 设置UTF-8编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 尝试设置stdout编码，如果失败则忽略
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import argparse
import json
from pathlib import Path
from src.stock_fetcher import StockFetcher
from src.technical_analyzer import TechnicalAnalyzer, SignalGenerator
from src.backtester import Backtester
from src.excel_exporter import ExcelExporter


def load_stock_list(stock_list_file: str) -> list:
    """Load stock codes from file"""
    try:
        with open(stock_list_file, 'r', encoding='utf-8') as f:
            stocks = [line.strip() for line in f if line.strip()]
        return stocks
    except FileNotFoundError:
        print(f"❌ Stock list file not found: {stock_list_file}")
        return []


def analyze_single_stock(stock_code: str, fetcher: StockFetcher, 
                        show_backtest: bool = False) -> dict:
    """Analyze a single stock"""
    print(f"\n{'='*70}")
    print(f"📈 分析股票: {stock_code}")
    print(f"{'='*70}")
    
    # Fetch historical data
    print(f"  ⏳ 抓取歷史數據...")
    history = fetcher.fetch_historical_data(stock_code, days=250)
    
    if history is None or history.empty:
        print(f"  ❌ 無法獲取 {stock_code} 的數據")
        return None
    
    # Add indicators
    print(f"  ⏳ 計算技術指標...")
    history = TechnicalAnalyzer.add_indicators(history)
    
    # Get latest analysis
    analysis = TechnicalAnalyzer.get_latest_analysis(history)
    
    # Generate signal
    signal, reason = SignalGenerator.generate_signal(analysis)
    
    # Display analysis
    print(f"\n  📊 最新數據 ({analysis['date']}):")
    print(f"     收盤價: NT${analysis['close']:.2f}")
    print(f"     EMA12: {analysis['ema_short']:.2f}")
    print(f"     EMA26: {analysis['ema_long']:.2f}")
    print(f"     SMA20: {analysis['sma_20']:.2f}")
    print(f"     BIAS:  {analysis['bias']:.2f}%")
    print(f"     MACD:  {analysis['macd']:.4f}")
    
    print(f"\n  💡 訊號: {signal}")
    print(f"     原因: {reason}")
    
    # Backtest if requested
    backtest_results = None
    if show_backtest:
        print(f"\n  ⏳ 進行 BIAS 策略回測...")
        # Test BIAS thresholds from -5% to 0%
        bias_thresholds = [-5.0, -4.5, -4.0, -3.5, -3.0, -2.5, -2.0, -1.5, -1.0, -0.5, 0]
        backtest_results = Backtester.backtest_bias_strategy(history, bias_thresholds, holding_days=5)
        
        # Print backtest results
        print(Backtester.format_backtest_results(backtest_results))
    
    return {
        'code': stock_code,
        'analysis': analysis,
        'signal': signal,
        'reason': reason,
        'history': history,
        'backtest_results': backtest_results
    }


def analyze_portfolio(stock_list_file: str = 'stockList.txt', 
                     export_excel: bool = True,
                     show_backtest: bool = False) -> dict:
    """Analyze all stocks in portfolio"""
    stocks = load_stock_list(stock_list_file)
    
    if not stocks:
        print("❌ No stocks to analyze")
        return {}
    
    print(f"\n{'='*70}")
    print(f"🚀 股票投資組合分析工具")
    print(f"{'='*70}")
    print(f"📋 要分析的股票: {', '.join(stocks)}")
    print(f"   共 {len(stocks)} 檔")
    
    fetcher = StockFetcher()
    results = {}
    
    for i, stock_code in enumerate(stocks, 1):
        print(f"\n[{i}/{len(stocks)}]")
        result = analyze_single_stock(stock_code, fetcher, show_backtest)
        if result:
            results[stock_code] = result
    
    # Summary report
    print(f"\n{'='*70}")
    print(f"📋 摘要報告")
    print(f"{'='*70}")
    print(f"{'股票代號':<12} {'今日收盤':<12} {'BIAS%':<10} {'訊號':<15} {'理由':<30}")
    print("-"*70)
    
    for stock_code, result in results.items():
        if result and result['analysis']:
            analysis = result['analysis']
            signal = result['signal']
            print(f"{stock_code:<12} "
                  f"NT${analysis['close']:<11.2f} "
                  f"{analysis['bias']:<10.2f} "
                  f"{signal:<15} "
                  f"{result['reason'][:30]:<30}")
    
    # Export to Excel if requested
    if export_excel:
        print(f"\n{'='*70}")
        print(f"💾 匯出 Excel 到 output 資料夾...")
        output_file = ExcelExporter.export_analysis(results)
        if output_file:
            print(f"   ✅ 已保存: output/{output_file.name}")
    
    print(f"\n{'='*70}\n")
    
    return results


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='🚀 股票分析工具 - 自動分析 EMA/BIAS 并推薦買賣'
    )
    parser.add_argument(
        '--stock',
        type=str,
        help='Single stock code to analyze (e.g., 00878)'
    )
    parser.add_argument(
        '--portfolio',
        action='store_true',
        help='Analyze all stocks in stockList.txt'
    )
    parser.add_argument(
        '--list-file',
        type=str,
        default='stockList.txt',
        help='Stock list file (default: stockList.txt)'
    )
    parser.add_argument(
        '--backtest',
        action='store_true',
        help='Run backtest to find optimal BIAS entry point'
    )
    parser.add_argument(
        '--no-excel',
        action='store_true',
        help='Do not export to Excel'
    )
    
    args = parser.parse_args()
    
    # If no specific arguments, default to portfolio analysis
    if not args.stock and not args.portfolio:
        args.portfolio = True
    
    try:
        if args.stock:
            # Analyze single stock
            fetcher = StockFetcher()
            analyze_single_stock(args.stock, fetcher, args.backtest)
        else:
            # Analyze portfolio
            analyze_portfolio(
                args.list_file,
                export_excel=not args.no_excel,
                show_backtest=args.backtest
            )
    
    except KeyboardInterrupt:
        print("\n\n⚠️  分析已取消")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()

