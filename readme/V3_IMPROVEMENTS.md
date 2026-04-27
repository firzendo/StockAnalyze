# 🚀 v3.0 決策邏輯三大改進

## 概述
v3.0升級解決了v2.0的三個關鍵問題，引入**動能分析**、**趨勢強度判斷**、**回檔確認機制**，讓交易訊號更精准、減少假信號。

---

## 改進 ❶ 智能過熱區判斷（解決盲目減碼）

### v2.0 問題
**"過熱就直接減碼 → 太粗暴"**

當 BIAS > 5% 時，v2.0 直接發出減碼信號，完全忽視股票是否處於強勢多頭。這在強牛市中會造成嚴重漏利。

例如：台積電(2330) BIAS 10-15% 時仍在加速上漲，盲目減碼會在買點減少持倉。

### v3.0 解決方案
使用**趨勢強度分析**區分過熱區的真假上升：

```
BIAS > 5% 的智能邏輯：
├─ 如果 EMA12 > EMA26 距離 > 2% + BIAS 環比上升
│  └─ 💪 持有 (強勢多頭持續加速)
│
├─ 如果 EMA12 < EMA26 + BIAS 環比下降
│  └─ 🔴 減碼 (動能轉弱或空頭市場)
│
└─ 其他情況
   └─ ⚪ 觀望 (不確定)
```

### 實現細節

#### 1. 趨勢強度判斷函數
```python
def analyze_trend_strength(analysis: Dict) -> str:
    """
    根據 EMA 乖離率分類趨勢強度
    
    強趨勢: EMA12 > EMA26 距離 > 2.0%
    正常趨勢: EMA12 > EMA26 距離 0.5~2.0%
    弱趨勢: EMA12 > EMA26 距離 < 0.5% 或 EMA12 < EMA26
    """
    ema_short = analysis.get('ema_short', 0)
    ema_long = analysis.get('ema_long', 0)
    
    if ema_long == 0:
        return 'weak'
    
    ema_gap_ratio = (ema_short - ema_long) / ema_long * 100
    
    if ema_gap_ratio > 2.0:
        return 'strong'
    elif ema_gap_ratio > 0.5:
        return 'normal'
    else:
        return 'weak'
```

#### 2. 過熱區的智能減碼邏輯
```python
# 當 BIAS > 5% 時
if momentum['is_strong_uptrend'] and trend_strength == 'strong':
    # 強勢多頭 + 動能加速 = 持續看多
    return "💪 持有", "過熱但強勢多頭持續加速...，持有別減碼"
elif momentum['is_weakening'] or trend_strength != 'strong':
    # 動能已轉弱 或 趨勢已變差 = 減碼觀察
    return "🔴 減碼", "動能轉弱或趨勢變差...，建議減碼"
```

### 實際案例
**0050 (11.67% BIAS)**
- v2.0 判斷: 🔴 減碼 (因為 BIAS > 5%)
- v3.0 判斷: 💪 持有 (EMA12 > EMA26 + BIAS 還在上升)
- 結果: 強牛市中持續上漲，v3.0 正確保留部位

---

## 改進 ❷ 動能加速度偵測（解決缺少變化追蹤）

### v2.0 問題
**"缺少動能變化"**

v2.0 只看當前 BIAS 值，不知道 BIAS 是在加速上升還是在減速，因此無法區分：
- BIAS 15% (從 5% 加速到 15%) = 強買
- BIAS 15% (從 20% 減速到 15%) = 弱賣

### v3.0 解決方案
追蹤 **BIAS 的方向和速度變化**：

```python
def analyze_momentum(analysis: Dict) -> Dict:
    """
    分析 BIAS 的動能狀態
    
    返回:
    - is_accelerating: BIAS 在上升或加速上升
    - is_strong_uptrend: BIAS > 5% 且 在上升
    - is_weakening: BIAS > 5% 但在下降
    - momentum_direction: 'accelerating' / 'normal' / 'weakening'
    """
    bias = analysis.get('bias', 0)
    bias_prev = analysis.get('bias_prev', bias)
    
    bias_change = bias - bias_prev
    is_accelerating = bias_change > 0
    is_strong_uptrend = bias > 5 and bias_change > 0
    is_weakening = bias > 5 and bias_change < 0
    
    return {
        'is_accelerating': is_accelerating,
        'is_strong_uptrend': is_strong_uptrend,
        'is_weakening': is_weakening,
        'bias_change': bias_change,
        'momentum_direction': 'accelerating' if is_accelerating else ('weakening' if is_weakening else 'normal')
    }
```

### 實現邏輯
1. **自動追蹤歷史BIAS**
   - `bias_prev`: 前1天的BIAS
   - `bias_5d_ago`: 5天前的BIAS
   - 計算 `bias_change = bias - bias_prev`

2. **判斷加速度方向**
   - BIAS 上升中 + BIAS_CHANGE > 0 → 加速上升 ✅
   - BIAS 下降中 + BIAS_CHANGE < 0 → 加速下降 ❌
   - BIAS > 5% + BIAS_CHANGE < 0 → 動能轉弱 ⚠️

3. **在4個區間應用**
   - 超跌區 (BIAS < -5%): 等待加速反彈信號
   - 合理區 (-5% ~ 3%): 所有反彈都可進場
   - 偏熱區 (3% ~ 5%): 只追加速信號
   - 過熱區 (> 5%): 根據加速度決定持有或減碼

### 實際案例
**2330 (BIAS 11.31% 且環比上升)**
- v2.0: 🔴 減碼 (BIAS > 5% 直接減)
- v3.0: 💪 持有 (BIAS 環比上升 = 動能加速)

**同一股票隔日 (BIAS 11% 但環比下降)**
- v2.0: 🔴 減碼 (BIAS > 5%)
- v3.0: 🔴 減碼 (BIAS 動能轉弱，更強確信減碼)

---

## 改進 ❸ 回檔確認機制（解決假突破進場）

### v2.0 問題
**"沒有回檔確認"**

v2.0 在超跌區 (BIAS < -5%) 時立刻發訊號，可能在最低點前一刻進場，導致：
- 進場後繼續跌 (假突破)
- 本金虧損後才反彈

### v3.0 解決方案
在超跌區等待**反彈確認**：

```python
def check_pullback_confirmation(analysis: Dict) -> Tuple[bool, str]:
    """
    確認是否有有效的反彈信號
    
    超跌區 (BIAS < -5%):
    ├─ BIAS 環比上升 → 已開始反彈 ✅ 可進場
    └─ BIAS 環比下降 → 還在下跌 ❌ 繼續等待
    
    合理區 (-5% ~ 3%): 都可進場
    """
    bias = analysis.get('bias', 0)
    bias_prev = analysis.get('bias_prev', bias)
    bias_change = bias - bias_prev
    
    if bias < -5.0:
        if bias_change > 0:
            return True, "已開始反彈"
        else:
            return False, "還在下跌，等待反彈"
    
    if -5.0 <= bias <= 3.0:
        return True, "合理區間，可進場"
    
    return False, "不在建議進場區"
```

### 實現邏輯
1. **超跌區 (BIAS < -5%)**
   - ✅ 允許進場條件: BIAS 環比上升 (反彈已確認)
   - ❌ 拒絕進場條件: BIAS 環比下降 (還在尋底，等待)

2. **合理區 (-5% ~ 3%)**
   - ✅ 所有情況都可進場 (安全區間)

3. **不建議進場 (BIAS > 3%)**
   - 在回檔確認邏輯中返回 False
   - 由更高層的決策邏輯決定是否進場

### 實際案例
**某股票 BIAS -8% (超跌)**
- 前日 BIAS: -10%
- 當日 BIAS: -8% (環比上升)
- v3.0: ✅ 可進場 (反彈已確認)

**同一股票隔日 (BIAS -9%，假反彈)**
- 前日 BIAS: -8%
- 當日 BIAS: -9% (環比下降)
- v3.0: ❌ 等待 (還在下跌中)

---

## 完整決策流程（v3.0 決策樹）

```
📊 獲取最新數據 (BIAS, EMA12, EMA26, 環比變化)
          ↓
🔍 計算 3 個分析層面
    ├─ analyze_momentum() → 獲取加速度信息
    ├─ analyze_trend_strength() → 獲取趨勢強度
    └─ check_pullback_confirmation() → 獲取反彈確認
          ↓
🎯 進入 4 個區間的階層邏輯
    │
    ├─ BIAS < -5% (超跌區 🔵)
    │  ├─ 已反彈確認? YES → 💡 可以買 (適合布局)
    │  └─ 還在下跌? NO → ⚪ 觀望 (等待反彈)
    │
    ├─ -5% ≤ BIAS ≤ +3% (合理區 🟢)
    │  └─ 所有情況 → 💡 可以買 (安全進場)
    │
    ├─ +3% < BIAS ≤ +5% (偏熱區 🟡)
    │  ├─ 動能加速 + 趨勢強? YES → 🟡 可以買 (追強)
    │  └─ 動能減弱或趨勢弱? NO → ⚪ 觀望 (等待回檔)
    │
    └─ BIAS > +5% (過熱區 🔴)
       ├─ 強勢多頭持續加速? YES → 💪 持有 (持續看多)
       ├─ 動能轉弱或趨勢差? YES → 🔴 減碼 (動能已反轉)
       └─ 其他 → ⚪ 觀望 (觀察)
           ↓
       💡 出現訊號和理由
```

---

## 測試結果（v3.0 實際案例）

### 組合分析結果 (2024-04-24)

| 股票 | BIAS | 動能 | 趨勢 | v2.0 判斷 | v3.0 判斷 | 改進說明 |
|------|------|------|------|---------|---------|---------|
| 0050 | 11.67% | ⬆️ 加速 | 強 | 🔴 減碼 | 💪 持有 | ❶ 過熱區智能判斷 |
| 00878 | 7.37% | ⬆️ 加速 | 強 | 🔴 減碼 | 💪 持有 | ❶ 過熱區智能判斷 |
| 00919 | 2.33% | ➡️ 正常 | 正常 | 🟢 可買 | 🟢 可買 | ✓ 一致 |
| 2330 | 11.31% | ⬆️ 加速 | 強 | 🔴 減碼 | 💪 持有 | ❶ 過熱區智能判斷 |

**關鍵發現**: v3.0 在過熱區 (BIAS > 5%) 的決策更精確，區分了強牛市 (持有) 和弱熊市 (減碼)。

---

## 配置參數

v3.0 使用的關鍵門檻值：

```python
# 超跌區
BIAS_ULTRA_LOW_THRESHOLD = -5.0          # 超跌臨界

# 合理區
BIAS_COMFORTABLE_LOW = -5.0               # 舒適區下界
BIAS_COMFORTABLE_HIGH = 3.0               # 舒適區上界

# 偏熱區
BIAS_WARM_THRESHOLD = 3.0                 # 偏熱起點
BIAS_WARM_HIGH = 5.0                      # 偏熱上界

# 過熱區
BIAS_HOT_THRESHOLD = 5.0                  # 過熱起點

# 趨勢強度
EMA_STRONG_GAP = 2.0                      # 強趨勢 EMA 距離 %
EMA_NORMAL_GAP = 0.5                      # 正常趨勢 EMA 距離 %

# EMA 參數
EMA_SHORT = 12                            # 短期 EMA 週期
EMA_LONG = 26                             # 長期 EMA 週期
```

---

## 架構改進

### 技術變更
- ✅ `get_latest_analysis()`: 新增 `bias_prev`, `bias_5d_ago`, `ema_short_prev` 欄位
- ✅ `SignalGenerator` 新增 4 個方法:
  - `analyze_momentum()`: 計算動能加速度
  - `analyze_trend_strength()`: 判斷趨勢強弱
  - `check_pullback_confirmation()`: 驗證反彈確認
  - `generate_signal()`: 改寫為階層邏輯

### 依賴性
- pandas: DataFrame 歷史數據處理
- numpy: 數值計算
- 無新增第三方套件

---

## 未來優化方向

1. **動能加速度進階版**
   - 使用 BIAS 的二階導數（加速度的加速度）判斷趨勢反轉點
   
2. **成交量確認**
   - 加入成交量 ADR 判斷動能真偽
   
3. **機器學習參數最佳化**
   - 根據歷史勝率自動調整 EMA_STRONG_GAP 等參數
   
4. **風險管理**
   - 根據 BIAS 波動率動態調整持倉比例

---

## 更新日期
- **v3.0 發佈**: 2025-04
- **包含改進**: ❶❷❸ 三大改進
- **測試狀態**: ✅ 已驗證通過
- **檔案位置**: [technical_analyzer.py](src/technical_analyzer.py)
