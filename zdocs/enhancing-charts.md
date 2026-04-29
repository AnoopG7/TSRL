# Professional Trading Platform Features - Implementation Plan

## Context
Enhance TSRL frontend with professional trading platform features similar to TradingView. The current charts have basic functionality (equity curves, drawdowns, hover info bars) but lack advanced analysis features found in industry-standard tools.

---

## Phase 1: High-Impact Chart Enhancements (Priority)

### 1. Synchronized Crosshair
Vertical dashed line that syncs across equity and drawdown charts when hovering.

**New File**: `frontend/src/contexts/ChartSyncContext.tsx`
- Shared state: `{ activeIndex, activeDate }`
- Provider wraps charts in BacktestPage

**Modifications**:
- `EquityCurveChart.tsx`: Broadcast hover via context, render synced ReferenceLine
- `DrawdownChart.tsx`: Same pattern
- `BacktestPage.tsx`: Wrap charts in `<ChartSyncProvider>`

### 2. Trade Markers on Equity Curve
Show entry/exit points visually on the equity curve.

**Modifications to** `EquityCurveChart.tsx`:
- Add `trades?: Trade[]` prop
- Add `showTradeMarkers` toggle (default true)
- Render custom SVG triangles using Recharts `<Scatter>` with custom shape
- Entry: Green triangle pointing up
- Exit: Triangle down (green if profit, red if loss)

**Data**: Trades array already available in `useBacktestStore()`

### 2b. OHLCV Price Chart with Trade Overlays (NEW)
Professional candlestick chart showing price action with trade entry/exit markers.

**New File**: `frontend/src/components/charts/PriceChart.tsx`
- Candlestick rendering using Recharts `<Bar>` with custom shape for OHLC
- Volume bars below (separate Y-axis)
- Trade markers: Entry arrows, exit arrows with profit/loss coloring
- Zoom/pan with Brush
- Optional moving average overlays (from strategy)

**Backend Enhancement**: Need to return OHLCV data in backtest response
- Modify `/src/main.py` to include `ohlcv_data` in response (limited to 500 points)
- Data already exists in backtest engine, just needs to be exposed

**New Tab**: "Price" in BacktestPage chart section

### 3. Return Distribution Histogram
Bar chart showing daily return distribution with statistics.

**New File**: `frontend/src/components/charts/ReturnDistributionChart.tsx`
- Props: `returns: number[]`, `type: 'daily' | 'trade'`
- Calculate histogram bins, show green/red bars
- Overlay normal distribution curve (dashed)
- Stats bar: Mean, Std Dev, Skewness, Kurtosis
- Reference line at mean

### 4. Rolling Sharpe Chart
60-day rolling Sharpe ratio visualization over time.

**New File**: `frontend/src/components/charts/RollingSharpeChart.tsx`
- Calculate rolling Sharpe from equity curve (frontend)
- Area chart with gradient fill
- Reference lines at Sharpe = 0, 1, 2, -1
- Stats bar: Current, Average, Time > 1.0, Range
- Brush for zoom/pan

---

## Phase 2: Enhanced Metrics & Controls

### 5. Expanded Risk Metrics Panel
New section showing VaR 95%, CVaR 95%, Calmar, Omega ratios (backend already calculates these).

### 6. Chart Toolbar
Per-chart toolbar with: Fullscreen, Export PNG, Reset Zoom buttons.

### 7. Time Range Selector
Quick filter buttons: 1M, 3M, 6M, 1Y, ALL.

---

## Phase 3: Portfolio Enhancements

### 8. Correlation Heatmap
Visual matrix of asset correlations (data from `portfolio_metrics.correlation_matrix`).

### 9. Risk Contribution Chart
Horizontal bar chart showing per-asset risk contribution.

### 10. Benchmark Comparison
Overlay benchmark (SPY) on equity curve when available.

---

## Files to Create

| File | Description |
|------|-------------|
| `frontend/src/contexts/ChartSyncContext.tsx` | Crosshair sync state |
| `frontend/src/components/charts/ReturnDistributionChart.tsx` | Histogram chart |
| `frontend/src/components/charts/RollingSharpeChart.tsx` | Rolling performance |
| `frontend/src/components/charts/PriceChart.tsx` | OHLCV candlestick with trade markers |

## Files to Modify

| File | Changes |
|------|---------|
| `frontend/src/components/charts/EquityCurveChart.tsx` | Trade markers, crosshair sync |
| `frontend/src/components/charts/DrawdownChart.tsx` | Crosshair sync |
| `frontend/src/components/charts/index.ts` | Export new components |
| `frontend/src/pages/BacktestPage.tsx` | ChartSyncProvider, new tabs (Price, Distribution, Rolling), pass trades |
| `frontend/src/styles/theme.css` | Crosshair, trade marker, candlestick, histogram styles |
| `frontend/src/lib/schemas/backtest.schema.ts` | Add OHLCVPoint type, update BacktestResult |
| `src/main.py` | Return OHLCV data in backtest response |

## Patterns to Reuse

- `HoverInfoBar` for stats display
- `chart-stats-bar` CSS grid for metrics
- `chart-controls` for toggles
- `Cell` for conditional coloring
- Custom tooltip pattern (return null, update state via setTimeout)

---

## Verification

1. **Crosshair**: Hover equity chart → drawdown shows matching vertical line
2. **Trade Markers (Equity)**: Markers align with trade dates on equity curve
3. **Price Chart**: Candlesticks render correctly, trade markers at correct prices
4. **Distribution**: Histogram shape with positive/negative coloring
5. **Rolling Sharpe**: Values reasonable (typically -2 to +3 range)
6. **Performance**: No lag with 500+ data points on any chart
7. **Build**: `npm run build` passes without errors
