"""
Technical Analyzer Module - Calculate EMA, BIAS, SMA and other indicators
"""
import pandas as pd
import numpy as np
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class TechnicalAnalyzer:
    """Class to calculate technical indicators"""
    
    @staticmethod
    def calculate_sma(data: pd.Series, period: int = 20) -> pd.Series:
        """
        Calculate Simple Moving Average
        
        Args:
            data: Price series (usually Close price)
            period: Period for SMA calculation
            
        Returns:
            SMA series
        """
        return data.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(data: pd.Series, period: int = 12) -> pd.Series:
        """
        Calculate Exponential Moving Average
        
        Args:
            data: Price series
            period: Period for EMA calculation
            
        Returns:
            EMA series
        """
        return data.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_bias(close: pd.Series, sma_period: int = 20) -> pd.Series:
        """
        Calculate BIAS indicator
        BIAS = (Close - SMA) / SMA * 100
        
        Args:
            close: Close price series
            sma_period: Period for SMA calculation
            
        Returns:
            BIAS series (in percentage)
        """
        sma = TechnicalAnalyzer.calculate_sma(close, sma_period)
        bias = ((close - sma) / sma) * 100
        return bias
    
    @staticmethod
    def add_indicators(df: pd.DataFrame, 
                       ema_short: int = 12,
                       ema_long: int = 26,
                       sma_period: int = 20) -> pd.DataFrame:
        """
        Add all technical indicators to dataframe
        
        Args:
            df: DataFrame with OHLCV data
            ema_short: Short EMA period
            ema_long: Long EMA period
            sma_period: SMA period for BIAS
            
        Returns:
            DataFrame with added indicators
        """
        df = df.copy()
        
        # 處理多級列索引（來自yfinance）
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        # Add EMA
        df['EMA_Short'] = TechnicalAnalyzer.calculate_ema(df['Close'], ema_short)
        df['EMA_Long'] = TechnicalAnalyzer.calculate_ema(df['Close'], ema_long)
        
        # Add SMA
        df['SMA_20'] = TechnicalAnalyzer.calculate_sma(df['Close'], sma_period)
        
        # Add BIAS
        df['BIAS'] = TechnicalAnalyzer.calculate_bias(df['Close'], sma_period)
        
        # 🆕 1️⃣ BIAS 動能（超重要）- 追蹤 BIAS 方向變化
        df['BIAS_prev'] = df['BIAS'].shift(1)
        df['BIAS_diff'] = df['BIAS'] - df['BIAS_prev']
        
        # 🆕 2️⃣ 價格 vs EMA20 距離 - 確認「回檔是否到位」
        df['Distance_SMA20'] = (df['Close'] - df['SMA_20']) / df['SMA_20'] * 100
        
        # 🆕 3️⃣ 短期轉弱訊號 - 「開始跌」的第一訊號
        df['Below_EMA5'] = df['Close'] < df['EMA_Short']
        
        # Add MACD (EMA12 - EMA26)
        df['MACD'] = df['EMA_Short'] - df['EMA_Long']
        
        # Add price change percentage
        df['Price_Change_Pct'] = df['Close'].pct_change() * 100
        
        return df
    
    @staticmethod
    def get_latest_analysis(df: pd.DataFrame) -> Dict:
        """
        Get latest indicator values with historical context
        
        Args:
            df: DataFrame with indicators
            
        Returns:
            Dictionary with latest values and momentum info
        """
        # Ensure we're working with a DataFrame with proper multi-level columns if needed
        if df.empty or len(df) < 2:
            return None
        
        # Handle multi-level columns from yfinance (e.g., ('Close', 'symbol'))
        if isinstance(df.columns, pd.MultiIndex):
            symbol = df.columns.get_level_values(1).unique()[0]
            df_clean = df.copy()
            df_clean.columns = df_clean.columns.get_level_values(0)
        else:
            df_clean = df.copy()
        
        latest_row = df_clean.iloc[-1]
        prev_row = df_clean.iloc[-2] if len(df_clean) > 1 else None
        prev_5_row = df_clean.iloc[-5] if len(df_clean) > 4 else None
        
        # Extract values safely
        def get_value(row, key, default=None):
            try:
                val = row[key] if key in row.index else default
                if isinstance(val, (pd.Series, pd.DataFrame)):
                    return float(val.iloc[0]) if len(val) > 0 else default
                return float(val) if val is not None else default
            except:
                return default
        
        # Build analysis dictionary with momentum info
        analysis = {
            'date': str(latest_row.name if hasattr(latest_row, 'name') else 'N/A'),
            'close': round(get_value(latest_row, 'Close', 0), 2) if 'Close' in latest_row.index else 0,
            'ema_short': round(get_value(latest_row, 'EMA_Short', 0), 2) if 'EMA_Short' in latest_row.index else 0,
            'ema_long': round(get_value(latest_row, 'EMA_Long', 0), 2) if 'EMA_Long' in latest_row.index else 0,
            'sma_20': round(get_value(latest_row, 'SMA_20', 0), 2) if 'SMA_20' in latest_row.index else 0,
            'bias': round(get_value(latest_row, 'BIAS', 0), 2) if 'BIAS' in latest_row.index else 0,
            'macd': round(get_value(latest_row, 'MACD', 0), 4) if 'MACD' in latest_row.index else 0,
            'price_change_pct': round(get_value(latest_row, 'Price_Change_Pct', 0), 2) if 'Price_Change_Pct' in latest_row.index else 0,
            # 🆕 新增指標
            'bias_diff': round(get_value(latest_row, 'BIAS_diff', 0), 2) if 'BIAS_diff' in latest_row.index else 0,
            'distance_sma20': round(get_value(latest_row, 'Distance_SMA20', 0), 2) if 'Distance_SMA20' in latest_row.index else 0,
            'below_ema5': bool(get_value(latest_row, 'Below_EMA5', False)) if 'Below_EMA5' in latest_row.index else False
        }
        
        # 关键改进：添加动能信息（前一天的BIAS）
        if prev_row is not None:
            analysis['bias_prev'] = round(get_value(prev_row, 'BIAS', 0), 2) if 'BIAS' in prev_row.index else 0
            analysis['ema_short_prev'] = round(get_value(prev_row, 'EMA_Short', 0), 2) if 'EMA_Short' in prev_row.index else 0
        
        # 5日前的BIAS用于判断多头强度
        if prev_5_row is not None:
            analysis['bias_5d_ago'] = round(get_value(prev_5_row, 'BIAS', 0), 2) if 'BIAS' in prev_5_row.index else 0
        
        return analysis


class SignalGenerator:
    """
    Advanced signal generator with momentum and trend strength analysis
    
    三大改进：
    1. 区分强弱多头 - 过热时判断是加速还是减速
    2. 动能变化 - 追踪BIAS方向和加速度
    3. 回档确认 - 等待确认信号再进场
    """
    
    @staticmethod
    def analyze_momentum(analysis: Dict) -> Dict:
        """
        分析BIAS动能变化（关键改进）
        
        🆕 现在利用新指标：
        - BIAS_diff: 直接反映BIAS方向（> 0上升，< 0下降）
        - Distance_SMA20: 判断是否进入回档区
        - Below_EMA5: 短期转弱的第一信号
        
        Args:
            analysis: Dictionary with current and historical BIAS
            
        Returns:
            Dictionary with momentum info
        """
        bias = analysis.get('bias', 0)
        bias_prev = analysis.get('bias_prev', bias)
        bias_5d_ago = analysis.get('bias_5d_ago', bias)
        
        # 使用新的 BIAS_diff 指标
        bias_diff = analysis.get('bias_diff', bias - bias_prev)  # 当天BIAS变化
        bias_5d_change = bias - bias_5d_ago  # 5日变化
        
        # 新指标
        distance_sma20 = analysis.get('distance_sma20', 0)  # 价格与SMA20距离
        below_ema5 = analysis.get('below_ema5', False)  # 是否跌破EMA5
        
        # 判断是否在加速（变化加快）
        is_accelerating = bias_diff > 0
        
        # 判断是否在强势上升中（高位且还在涨）
        is_strong_uptrend = bias > 5 and bias_diff > 0
        
        # 判断是否在减速/转弱（高位但在跌）
        is_weakening = bias > 5 and bias_diff < 0
        
        # 🆕 判断是否进入回档区（价格接近SMA20）
        is_in_pullback_zone = distance_sma20 < 3.0 and distance_sma20 > -2.0  # 在SMA20上下3%以内
        
        # 🆕 短期转弱信号（价格跌破EMA5）
        has_short_term_weakness = below_ema5
        
        momentum_info = {
            'bias_change': round(bias_diff, 2),  # 当天变化（使用新指标）
            'bias_5d_change': round(bias_5d_change, 2),  # 5日变化
            'is_accelerating': is_accelerating,  # 是否在加速
            'is_strong_uptrend': is_strong_uptrend,  # 强勢上升中
            'is_weakening': is_weakening,  # 正在减速/转弱
            'is_in_pullback_zone': is_in_pullback_zone,  # 🆕 是否在回档区
            'has_short_term_weakness': has_short_term_weakness,  # 🆕 是否有短期转弱
            'distance_sma20': round(distance_sma20, 2),  # 🆕 价格与SMA20距离
        }
        
        return momentum_info
    
    @staticmethod
    def analyze_trend_strength(analysis: Dict) -> str:
        """
        判断多头的强弱程度
        
        Args:
            analysis: Dictionary with indicators
            
        Returns:
            'strong', 'normal', 'weak'
        """
        ema_short = analysis.get('ema_short', 0)
        ema_long = analysis.get('ema_long', 0)
        ema_short_prev = analysis.get('ema_short_prev', ema_short)
        
        if ema_short <= ema_long:
            return 'weak'  # EMA已转弱
        
        # EMA间距越大，多头越强
        ema_gap = ema_short - ema_long
        ema_gap_ratio = (ema_gap / ema_long * 100) if ema_long != 0 else 0
        
        if ema_gap_ratio > 2.0:
            return 'strong'  # 间距>2%，强多头
        elif ema_gap_ratio > 0.5:
            return 'normal'  # 正常多头
        else:
            return 'weak'  # 弱多头
    
    @staticmethod
    def check_pullback_confirmation(analysis: Dict) -> Tuple[bool, str]:
        """
        检查是否有回档确认信号
        
        关键改进3：在低位等待回档确认
        - 只在BIAS开始反弹时进场（不是最低点）
        - 避免在半山腰追高或追低
        
        Args:
            analysis: Dictionary with momentum info
            
        Returns:
            Tuple of (is_confirmed, reason)
        """
        bias = analysis.get('bias', 0)
        bias_prev = analysis.get('bias_prev', bias)
        bias_change = bias - bias_prev  # 计算变化
        
        # 超跌区间（BIAS < -5%）需要等待反弹确认
        if bias < -5.0:
            if bias_change > 0:
                return True, f"已开始反弹（从{bias_prev:.2f}% → {bias:.2f}%）"
            else:
                return False, f"还在下跌中（BIAS {bias:.2f}%），等待反弹"
        
        # 在-5%~+3%区间可以进场
        if -5.0 <= bias <= 3.0:
            return True, f"合理区间（BIAS {bias:.2f}%）"
        
        return False, f"不在建议进场区"
    
    @staticmethod
    def generate_signal(analysis: Dict) -> Tuple[str, str]:
        """
        生成交易信号 - 改良版核心邏輯（簡潔直接）
        
        🔥 核心改進：
        1. 使用 BIAS_diff 判斷動能（上升 vs 下降）
        2. 使用 close > EMA_short 判斷價格位置
        3. 4層清晰邏輯，無冗餘判斷
        
        Args:
            analysis: Dictionary with latest analysis
            
        Returns:
            Tuple of (signal, reason)
        """
        # 提取關鍵數據
        bias = analysis.get('bias', 0)
        bias_diff = analysis.get('bias_diff', 0)
        ema_short = analysis.get('ema_short', 0)
        ema_long = analysis.get('ema_long', 0)
        close = analysis.get('close', 0)
        sma_20 = analysis.get('sma_20', 0)
        
        # 核心判斷
        trend_is_bullish = ema_short > ema_long
        above_ema_short = close > ema_short
        
        # ======================================
        # 🟢 1️⃣ 超跌（進場點）- BIAS < -5%
        # ======================================
        if bias < -5:
            if trend_is_bullish:
                return "✅ 強烈買入", f"超跌（BIAS {bias:.2f}%）+ 多頭趨勢，進場好時機"
            else:
                return "🟠 觀察反彈", f"雖然超跌（BIAS {bias:.2f}%）但趨勢向下，等待反彈確認"
        
        # ======================================
        # 🟢 2️⃣ 合理區（要加「止跌」條件）-5% ≤ BIAS ≤ 3%
        # ======================================
        elif -5 <= bias <= 3:
            if trend_is_bullish and bias_diff > 0:
                return "🟢 可以買", f"合理區（BIAS {bias:.2f}%）+ 多頭回升中，適合進場"
            else:
                return "⚪ 等確認", f"BIAS 合理但缺少確認訊號（多頭：{trend_is_bullish}, 回升：{bias_diff > 0}）"
        
        # ======================================
        # 🟡 3️⃣ 偏熱（重點改這）- 3% < BIAS ≤ 5%
        # ======================================
        elif 3 < bias <= 5:
            if bias_diff > 0:
                return "🟡 強勢持有", f"偏熱區（BIAS {bias:.2f}%）+ 動能向上，持有別追"
            else:
                return "⚪ 觀望", f"偏熱區（BIAS {bias:.2f}%）但動能轉弱，等待回檔"
        
        # ======================================
        # 🔴 4️⃣ 過熱（關鍵修正）- BIAS > 5%
        # ======================================
        else:  # bias > 5
            if bias_diff > 0 and above_ema_short:
                return "🟡 強勢持有", f"過熱但加速上升（BIAS {bias:.2f}%↑），主升段不減碼"
            else:
                return "🔴 減碼", f"過熱（BIAS {bias:.2f}%）且動能轉弱或跌破EMA，建議減碼"
        
        return "⚪ 觀望", "無清晰訊號"
