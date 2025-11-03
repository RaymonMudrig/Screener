# Fundamental Data for Stock Screening

## Data Source

```
https://idxmobile.co.id/Data/fd?isJSONStr=1&code={stockCode}:{year}:{quarter}
```

Let me provide a comprehensive taxonomy of fundamental metrics and data points used in professional stock screeners.

---

## 1. **VALUATION METRICS**

### Price-Based Ratios
- **P/E Ratio (Price-to-Earnings)**
  - Trailing P/E (last 12 months)
  - Forward P/E (next 12 months estimates)
  - PEG Ratio (P/E to Growth)
  - Relative P/E (vs industry/market)
  - Shiller P/E (CAPE - cyclically adjusted)

- **P/B Ratio (Price-to-Book)**
  - P/B vs historical average
  - P/B vs industry median
  - Tangible Book Value ratio

- **P/S Ratio (Price-to-Sales)**
  - Revenue multiple
  - Enterprise Value to Sales

- **P/CF Ratio (Price-to-Cash Flow)**
  - P/OCF (Operating Cash Flow)
  - P/FCF (Free Cash Flow)

### Enterprise Value Based
- **EV/EBITDA** - Enterprise value to earnings before interest, tax, depreciation, amortization
- **EV/EBIT** - Enterprise value to operating income
- **EV/Sales** - Enterprise value to revenue
- **EV/FCF** - Enterprise value to free cash flow
- **EV/IC** - Enterprise value to invested capital

### Dividend Metrics
- **Dividend Yield** - Annual dividend / Price
- **Dividend Payout Ratio** - Dividends / Net Income
- **Dividend Coverage** - Earnings / Dividends
- **Dividend Growth Rate** - YoY dividend increase
- **Consecutive Years of Dividends** - Payment history
- **Dividend Sustainability Score** - FCF / Dividends

---

## 2. **PROFITABILITY METRICS**

### Margin Analysis
- **Gross Margin** - (Revenue - COGS) / Revenue
- **Operating Margin** - Operating Income / Revenue
- **EBITDA Margin** - EBITDA / Revenue
- **Net Profit Margin** - Net Income / Revenue
- **Pre-tax Margin** - EBT / Revenue
- **Margin Trends** - QoQ, YoY changes

### Return Ratios
- **ROE (Return on Equity)** - Net Income / Shareholders' Equity
- **ROA (Return on Assets)** - Net Income / Total Assets
- **ROIC (Return on Invested Capital)** - NOPAT / Invested Capital
- **ROCE (Return on Capital Employed)** - EBIT / Capital Employed
- **ROI (Return on Investment)** - Net Profit / Investment Cost
- **DuPont Analysis** - ROE decomposition (margin × turnover × leverage)

### Efficiency Metrics
- **Asset Turnover** - Revenue / Total Assets
- **Inventory Turnover** - COGS / Average Inventory
- **Receivables Turnover** - Revenue / Accounts Receivable
- **Payables Turnover** - COGS / Accounts Payable
- **Working Capital Turnover** - Revenue / Working Capital
- **Fixed Asset Turnover** - Revenue / Net Fixed Assets

---

## 3. **GROWTH METRICS**

### Revenue Growth
- **Revenue Growth Rate** - YoY, QoQ percentage
- **Revenue CAGR** - Compound annual growth (3/5/10 year)
- **Same-Store Sales Growth** - Organic growth (retail)
- **Revenue Growth Acceleration** - Rate of change in growth
- **Sequential Growth** - Quarter over quarter

### Earnings Growth
- **EPS Growth** - YoY, QoQ earnings per share growth
- **EPS CAGR** - Historical compound growth
- **Forward EPS Growth** - Expected growth rate
- **Operating Income Growth** - EBIT growth trends
- **EBITDA Growth** - Cash earnings growth

### Other Growth Indicators
- **Book Value Growth** - Equity growth rate
- **Cash Flow Growth** - OCF/FCF growth rates
- **Dividend Growth** - Historical dividend increases
- **Asset Growth** - Total assets expansion
- **Subscriber/User Growth** - For tech/subscription businesses

---

## 4. **FINANCIAL HEALTH METRICS**

### Liquidity Ratios
- **Current Ratio** - Current Assets / Current Liabilities
- **Quick Ratio (Acid Test)** - (Current Assets - Inventory) / Current Liabilities
- **Cash Ratio** - (Cash + Marketable Securities) / Current Liabilities
- **Working Capital** - Current Assets - Current Liabilities
- **Net Working Capital Ratio** - Working Capital / Total Assets

### Leverage/Solvency Ratios
- **Debt-to-Equity** - Total Debt / Shareholders' Equity
- **Debt-to-Assets** - Total Debt / Total Assets
- **Debt-to-EBITDA** - Net Debt / EBITDA
- **Interest Coverage** - EBIT / Interest Expense
- **Equity Ratio** - Shareholders' Equity / Total Assets
- **Financial Leverage** - Total Assets / Shareholders' Equity
- **Net Debt** - Total Debt - Cash and Equivalents

### Credit Metrics
- **Altman Z-Score** - Bankruptcy prediction model
- **Piotroski F-Score** - Financial strength (0-9 scale)
- **Beneish M-Score** - Earnings manipulation detection
- **Credit Rating** - Agency ratings (if available)

---

## 5. **CASH FLOW METRICS**

### Cash Flow Analysis
- **Operating Cash Flow (OCF)** - Cash from operations
- **Free Cash Flow (FCF)** - OCF - CapEx
- **FCF Margin** - FCF / Revenue
- **FCF Yield** - FCF / Market Cap
- **Cash Flow to Debt** - OCF / Total Debt
- **Cash Conversion Cycle** - Days inventory + days receivable - days payable

### Capital Allocation
- **CapEx (Capital Expenditure)** - Investment in fixed assets
- **CapEx to Revenue** - CapEx intensity
- **CapEx to Depreciation** - Maintenance vs growth CapEx
- **Share Buyback Amount** - Repurchase programs
- **Total Shareholder Return** - Dividends + buybacks

### Cash Position
- **Cash and Equivalents** - Liquid assets
- **Cash per Share** - Cash / Shares Outstanding
- **Net Cash Position** - Cash - Total Debt
- **Cash Burn Rate** - For unprofitable companies
- **Runway** - Months of operation at current burn rate

---

## 6. **COMPANY PROFILE DATA**

### Classification
- **Sector** - GICS sector classification
- **Industry** - Specific industry group
- **Sub-Industry** - Detailed classification
- **Market Cap Category** - Large/Mid/Small/Micro cap
- **Country/Region** - Geographic location
- **Exchange** - Listed exchange

### Company Characteristics
- **Market Capitalization** - Share price × shares outstanding
- **Enterprise Value** - Market cap + debt - cash
- **Float** - Publicly traded shares
- **Institutional Ownership %** - Professional investor holdings
- **Insider Ownership %** - Management/founder holdings
- **Short Interest %** - Shares sold short / float
- **Shares Outstanding** - Total issued shares
- **IPO Date** - Time since public listing
- **Company Age** - Years since founding

### Business Model
- **Revenue Model** - Subscription, transactional, licensing, etc.
- **Geographic Revenue Mix** - Revenue by region
- **Product/Segment Mix** - Revenue by business line
- **Customer Concentration** - Top customers % of revenue
- **Recurring Revenue %** - Predictable revenue portion

---

## 7. **CORPORATE ACTIONS**

### Dividends
- **Ex-Dividend Date** - Last date to buy for dividend
- **Payment Date** - Dividend distribution date
- **Record Date** - Shareholder recording date
- **Dividend Amount** - Per share payment
- **Special Dividends** - One-time distributions
- **Dividend Frequency** - Quarterly, monthly, annual

### Stock Events
- **Stock Splits** - Forward/reverse splits
- **Stock Dividends** - Share distributions
- **Rights Issues** - Discounted share offerings
- **Warrant Exercise** - Dilution events
- **Bonus Issues** - Free share distribution

### Corporate Changes
- **Mergers & Acquisitions** - M&A activity
- **Spin-offs** - Business unit separation
- **Delisting Notices** - Exchange removal
- **Name Changes** - Corporate rebranding
- **Ticker Changes** - Symbol modifications

### Capital Raising
- **Secondary Offerings** - New share issuance
- **Private Placements** - Institutional sales
- **Convertible Bond Issues** - Potential dilution
- **Debt Issuance/Retirement** - Bond activity

---

## 8. **EARNINGS & ESTIMATES**

### Reported Results
- **Last Earnings Date** - Most recent report
- **Next Earnings Date** - Upcoming announcement
- **Earnings Surprise %** - Actual vs estimate
- **Revenue Surprise %** - Sales beat/miss
- **Earnings Quality** - Cash vs accrual basis
- **Restatements** - Historical corrections

### Analyst Coverage
- **Number of Analysts** - Coverage breadth
- **Consensus Rating** - Buy/Hold/Sell average
- **Price Target** - Average analyst target
- **Estimate Revisions** - Upgrades/downgrades trend
- **Earnings Estimate** - Forward EPS consensus
- **Revenue Estimate** - Forward sales consensus
- **Estimate Dispersion** - Analyst disagreement level

### Guidance
- **Management Guidance** - Company forecasts
- **Guidance vs Estimates** - Conservative/aggressive
- **Guidance Revision History** - Raises/lowers

---

## 9. **QUALITY INDICATORS**

### Earnings Quality
- **Accruals Ratio** - Non-cash earnings portion
- **Cash Earnings Ratio** - OCF / Net Income
- **Discretionary Accruals** - Accounting flexibility
- **Revenue Quality** - Cash collection efficiency
- **One-time Items** - Non-recurring charges frequency

### Balance Sheet Quality
- **Goodwill to Assets** - Acquisition premium
- **Intangible Assets %** - Hard vs soft assets
- **Off-Balance Sheet Items** - Hidden liabilities
- **Related Party Transactions** - Conflict risk
- **Audit Opinion** - Clean/qualified/adverse

### Management Quality
- **Management Tenure** - Executive stability
- **Board Independence** - Outside directors %
- **CEO/Chairman Split** - Governance structure
- **Executive Compensation** - Pay vs performance
- **Share-based Compensation** - Dilution trend
- **Insider Trading Activity** - Buy/sell patterns

---

## 10. **COMPARATIVE METRICS**

### Peer Comparison
- **Percentile Rank** - Position within industry
- **Relative Valuation** - Multiple vs peers
- **Growth Premium/Discount** - Growth-adjusted value
- **Quality Score** - Composite quality ranking
- **Market Share** - Position in industry

### Historical Comparison
- **5-Year Average Valuation** - Historical context
- **Valuation Percentile** - Current vs history
- **Margin Trend** - Improving/deteriorating
- **ROIC vs WACC** - Value creation spread

---

## 11. **RISK METRICS**

### Operational Risk
- **Operating Leverage** - Fixed vs variable costs
- **Revenue Concentration** - Customer/product risk
- **Geographic Risk** - Country exposure
- **Regulatory Risk** - Compliance burden
- **Competitive Position** - Market power

### Financial Risk
- **Beta** - Market sensitivity
- **Volatility** - Price standard deviation
- **Sharpe Ratio** - Risk-adjusted return
- **Max Drawdown** - Largest peak-to-trough decline
- **Bankruptcy Risk** - Z-score, distance to default

---

## **SCREENING STRATEGY COMBINATIONS**

### Value Screening
- Low P/E + Low P/B + Dividend Yield > 3% + Positive FCF
- EV/EBITDA < 8 + Debt/Equity < 0.5 + ROE > 15%
- P/B < 1 + Current Ratio > 2 + Piotroski F-Score > 7

### Growth Screening
- Revenue Growth > 20% + EPS Growth > 25% + Positive FCF
- PEG < 1 + Revenue Growth Acceleration + Margin Expansion
- User/Subscriber Growth > 30% + Low Churn + Increasing ARPU

### Quality Screening
- ROE > 15% + ROIC > 12% + FCF Margin > 10%
- Consecutive Years of Profit > 5 + Low Debt + Stable Margins
- High Piotroski F-Score + Low Accruals + Strong OCF/NI

### Dividend Screening
- Yield > 4% + Payout Ratio < 60% + 10+ Years Dividends
- Dividend Growth > 7% + FCF Coverage > 1.5x + Low Debt
- Dividend Aristocrats + Beta < 0.8 + Recession Resistant

### Turnaround Screening
- Improving Margins + Declining Debt + Insider Buying
- Estimate Revisions Upward + Relative Strength Improving
- New Management + Strategic Changes + Undervalued

### Financial Health Screening
- Altman Z-Score > 3 + Interest Coverage > 5x + Quick Ratio > 1
- FCF/Debt > 20% + ROIC > WACC + Low Leverage

---

## **COMPOSITE SCORING APPROACHES**

### Multi-Factor Models
```
Score = (Value Weight × Value Score) + 
        (Growth Weight × Growth Score) + 
        (Quality Weight × Quality Score) + 
        (Momentum Weight × Momentum Score)
```

### Factor Categories
1. **Value Factors** (25-30%)
2. **Growth Factors** (25-30%)
3. **Quality Factors** (20-25%)
4. **Technical Momentum** (15-20%)
5. **Sentiment/Other** (5-10%)

---

Would you like me to:
1. Design a specific screening strategy combining technical + fundamental signals?
2. Create a data model architecture for storing and querying this fundamental data?
3. Develop a scoring/ranking system for multi-factor screening?
4. Build the actual implementation with these metrics?