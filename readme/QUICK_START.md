# 快速開始指南 (Quick Start Guide)

## 🎯 5 分鐘開始使用

### 第 1 步：初始化環境 (一次性)

```bash
# 進入項目目錄
cd d:\Case\stock\StockAnalyze

# 創建虛擬環境 (如果還沒有)
python -m venv venv

# 啟動虛擬環境
venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

### 第 2 步：編輯股票清單

修改 `stockList.txt`，輸入你想追蹤的股票代號：

```
0050
00878
00919
2330
2454
```

### 第 3 步：運行分析

```bash
# 方法 1：分析投資組合中的所有股票 (推薦)
python StockAnalyzeMain.py

# 方法 2：分析單一股票
python StockAnalyzeMain.py --stock 2330

# 方法 3：進行 BIAS 策略回測
python StockAnalyzeMain.py --stock 0050 --backtest
```

---

## 📊 理解輸出結果

每次運行會輸出：

```
📈 分析股票: 2330
收盤價: NT$2185.00    ← 今天收盤價
EMA12: 2042.07       ← 短期上升趨勢
EMA26: 1973.55       ← 長期上升趨勢
SMA20: 1963.00       ← 20 天平均價
BIAS: 11.31%         ← 價格高於平均線 11.31%
MACD: 68.53          ← 正值，看漲

訊號: 🟢 可以買       ← 買賣推薦
```

### 訊號含義

| 訊號 | 符號 | 含義 | 行動 |
|------|------|------|------|
| 強烈買入 | ✅ | BIAS < -5% 且趨勢向上 | 大膽進場 |
| 可以買 | 🟢 | BIAS 在 -5%~+3% 且趨勢向上 | 適合買入 |
| 等待 | 🟠 | BIAS 看好但趨勢向下 | 暫時觀望 |
| 觀望 | ⚪ | BIAS 在 +3%~+5% | 等待更好機會 |
| 減碼 | 🔴 | BIAS > +5% | 部分出場 |

---

## 💡 常見場景

### 📋 場景 1：每天開盤前檢查

```bash
python StockAnalyzeMain.py
```

找「✅ 強烈買入」或「🟢 可以買」的股票，查看 Excel 報告詳細資訊。

### 📈 場景 2：分析特定股票

```bash
python StockAnalyzeMain.py --stock 2330
```

深入分析一個股票的所有技術指標。

### 🔍 場景 3：找出最佳進場點

```bash
python StockAnalyzeMain.py --stock 0050 --backtest
```

回測歷史數據，看在什麼 BIAS% 買入勝率最高。

---

## 🚨 常見問題

**Q: 為什麼有些股票沒有數據？**
A: 可能是代碼錯誤，確保使用正確的台灣股票代號格式。

**Q: 如何添加新股票到監控列表？**
A: 編輯 `stockList.txt`，添加股票代號，每行一個。

**Q: Excel 文件在哪裡？**
A: 自動保存在項目目錄中，文件名格式：`stock_analysis_YYYYMMDD_HHMMSS.xlsx`

**Q: 回測需要多長時間？**
A: 取決於網絡速度，通常 1-3 分鐘。

**Q: 可以同時分析多個股票嗎？**
A: 可以，編輯 `stockList.txt` 並運行 `python StockAnalyzeMain.py --portfolio`

---

## 🎓 學習技術指標

### 什麼是 BIAS？
BIAS 衡量股價與 20 天均線的偏離程度。
- BIAS > 3%：可能過熱，考慮賣出
- BIAS < -3%：可能過冷，考慮買入
- BIAS ≈ 0%：股價回到均線

### 什麼是 EMA？
EMA 根據最近的價格變動進行加權。
- EMA12 > EMA26：短期強於長期，看漲
- EMA12 < EMA26：短期弱於長期，看跌

---

## ⚠️ 免責聲明

- 本工具僅供參考，不構成投資建議
- 過去績效不代表未來表現
- 投資前務必自行研究分析
- 承擔投資虧損的所有責任

---

**開始交易吧！** 🚀📈
