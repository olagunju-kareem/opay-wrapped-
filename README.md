# OPay Wrap 💰

A beautiful PyQt5 application that visualizes your OPay financial data with interactive graphs and insightful statistics.

## Features

- 📊 **Interactive Balance Graph**: See how your money increased and decreased over time (like a crypto graph)
- 💵 **Financial Statistics**: 
  - Total money in
  - Total money out
  - Net change
  - Opening and closing balances
  - Average transaction amount
  - Highest and lowest balances
- 👥 **Top Recipients**: See who you sent the most money to
- 🎨 **Modern Dark UI**: Beautiful, easy-to-use interface

## Installation

1. Install Python 3.9 or higher
2. Create and activate a virtual environment (recommended):
```bash
# Create virtual environment
python -m venv venv

# Activate it (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Or (Windows CMD)
venv\Scripts\activate.bat

# Or (Linux/Mac)
source venv/bin/activate
```

3. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python opay_wrap.py
```

2. Click "📁 Select Excel File" to choose your OPay statement Excel file
3. The app will automatically:
   - Convert Excel to CSV
   - Parse your transactions
   - Display the balance graph
   - Show all statistics

## Requirements

- Python 3.9+
- PyQt5
- matplotlib
- openpyxl

## Notes

- The app processes OPay statement files in Excel format
- It automatically extracts transaction data including dates, amounts, and descriptions
- The graph shows your account balance over time with a smooth line chart
## Using `opay_wrap.py`

- **What it is:** `opay_wrap.py` is a small Python script that converts an OPay Excel bank statement into CSV, parses transactions, and produces visualizations and summary statistics (the functionality used by the GUI app can also be run from the script).

- **Get your OPay statement (Excel):**
  1. Open the OPay mobile app and go to _Transaction History_.
 2. Tap **Download** (top-left corner of the Transaction History screen).
 3. Select the **start date** and **end date** for the period you want, then export for the year or chosen range and send the file to your email.
 4. From your email, download the Excel file to the computer where you will run the script.

- **Install dependencies:**

```bash
pip install -r requirements.txt
```

- **Run the script:**

```bash
python opay_wrap.py
```

- **Notes:**
  - Place the downloaded Excel file in an accessible folder, or point the script to its path when prompted.
  - The script will convert the Excel file to CSV, parse transactions, and generate output (CSV, graphs, and summary stats) depending on the script options.


