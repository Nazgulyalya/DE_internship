# Bookstore Analytics Dashboard

Professional Business Intelligence Dashboard for analyzing bookstore sales data across three datasets.

## 🚀 Live Dashboard
[View Dashboard](https://nazgulyalya.github.io/DE_internship/task_4/)

## 📊 Features

- **Top 5 Revenue Days** in YYYY-MM-DD format
- **Unique Users Count** with alias reconciliation
- **Unique Author Sets** analysis
- **Most Popular Authors** by book sales
- **Best Customers** with all aliases as array of IDs
- **Daily Revenue Charts** for visual analysis

## 🛠️ Technical Implementation

### Data Processing
- Loads data from YAML, Parquet, and CSV files
- Handles currency conversion (€1 = $1.2)
- Extracts date components (year, month, day) from timestamps
- Reconciles user aliases (assumes only one field can change)
- Calculates paid_price = quantity * unit_price

### Analysis Features
- Daily revenue computation and top 5 days identification
- User deduplication with alias detection
- Author set analysis (individual vs collaborative works)
- Sales-based popularity ranking
- Customer spending analysis with alias grouping

## 📁 Project Structure
├── script.py # Main analysis script

├── index.html # Professional BI dashboard 

├── dashboard_data.js # Generated data for dashboard 

├── results/ # Analysis results (JSON) 

└── charts/ # Revenue charts (PNG)


## 🔧 Installation & Usage

```bash
# Install dependencies
pip install pandas numpy matplotlib seaborn PyYAML pyarrow python-dateutil

# Run analysis
python script.py

# Open index.html in browser or deploy to web server
```

## 📈 Dashboard Preview
### The dashboard provides:
- Interactive tabs for DATA1, DATA2, DATA3
- Professional metrics cards
- Revenue ranking tables
- Author popularity insights
- Customer analysis with aliases
- Responsive daily revenue charts

