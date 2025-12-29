import sys
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFileDialog, QScrollArea, QFrame, QGridLayout,
    QGraphicsDropShadowEffect, QDialog, QLineEdit, QTextEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor
from dotenv import load_dotenv

# Try to import OpenAI and LangChain (will show error if not installed)
LANGCHAIN_AVAILABLE = False
LANGCHAIN_ERROR = None
ChatOpenAI = None

try:
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError as e:
    try:
        from langchain.chat_models import ChatOpenAI
        LANGCHAIN_AVAILABLE = True
    except ImportError as e2:
        LANGCHAIN_ERROR = str(e2) if str(e2) else str(e)
        LANGCHAIN_AVAILABLE = False

load_dotenv()
class Theme:
    BG = "#121212"
    CARD = "#181818"
    PRIMARY = "#1DB954"
    ACCENT_PINK = "#FF4B6B"
    ACCENT_BLUE = "#509BF5"
    ACCENT_GOLD = "#F59B23"
    TEXT = "#FFFFFF"
    WHITE = "#FFFFFF"
    TEXT_DIM = "#B3B3B3"
    
    QSS = f"""
        QMainWindow {{ background-color: {BG}; }}
        QWidget {{ color: {TEXT}; font-family: 'Segoe UI', sans-serif; }}
        QScrollArea {{ border: none; background-color: {BG}; }}
        QPushButton#PrimaryBtn {{
            background-color: {PRIMARY}; color: black; border-radius: 20px;
            padding: 12px 30px; font-weight: bold; font-size: 14px;
        }}
        QPushButton#PrimaryBtn:hover {{ background-color: #1ed760; }}
    """

# --- AI FINANCIAL ADVISOR ---
class AIFinancialAdvisor:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.llm = None
        if self.api_key and LANGCHAIN_AVAILABLE and ChatOpenAI is not None:
            try:
                os.environ['OPENAI_API_KEY'] = self.api_key
                self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
            except Exception as e:
                print(f"Error initializing OpenAI: {e}")
                self.llm = None

    def generate_advice(self, stats_dict):
        """Generate financial advice based on statistics"""
        if not self.llm:
            return "Please configure your OpenAI API key to get AI financial advice."
        
        try:
            stats_summary = f"""
Financial Summary:
- Total Income: {stats_dict.get('in', 'N/A')}
- Total Spent: {stats_dict.get('out', 'N/A')}
- Net Balance: {stats_dict.get('net', 'N/A')}
- Total Data Spending: {stats_dict.get('total_data_spending', 'N/A')} ({stats_dict.get('data_pct', 'N/A')} of total spending)
- Average per Transaction: {stats_dict.get('avg_spend', 'N/A')}
- Weekend Spending: {stats_dict.get('weekend_pct', 'N/A')}
- Most Expensive Day: {stats_dict.get('busiest_day', 'N/A')} - {stats_dict.get('busiest_day_amt', 'N/A')}
- Top Spending Month: {stats_dict.get('top_month', 'N/A')}
"""

            prompt = f"""You are a friendly financial advisor. Based on the following transaction data summary, provide practical and actionable advice on:
1. How to improve their financial situation
2. Ways to save more money
3. Specific recommendations based on their spending patterns (especially data spending, weekend spending, etc.)
4. Tips for better money management

Keep the advice concise (3-4 paragraphs), friendly, and practical. Focus on actionable steps they can take immediately.

Transaction Data:
{stats_summary}

Please provide your financial advice:"""

            response = self.llm.invoke(prompt)
            return response.content if hasattr(response, 'content') else str(response)
        except Exception as e:
            return f"Error generating advice: {str(e)}"


class DataAnalyzer:
    def __init__(self):
        self.df = None
        self.monthly_df = None

    def process_data(self, file_path):
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path, on_bad_lines='skip')
            else:
                df = pd.read_excel(file_path)
            
            # Find the actual table header
            header_row = -1
            for i in range(min(len(df), 20)):
                row_values = [str(val) for val in df.iloc[i].values]
                if any("Trans. Date" in val for val in row_values):
                    header_row = i
                    break
            
            if header_row == -1: 
                return False, "Could not find the transaction table header."
            
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row + 1:].reset_index(drop=True)
            df.columns = [str(c).strip() for c in df.columns]
            
            col_map = {
                'Trans. Date': 'date', 'Description': 'desc', 
                'Debit(₦)': 'debit', 'Credit(₦)': 'credit', 
                'Balance After(₦)': 'balance'
            }
            df = df.rename(columns=col_map)

            for col in ['debit', 'credit', 'balance']:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace(r'[₦,"]', '', regex=True)
                    df[col] = df[col].replace('--', '0').replace('nan', '0')
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.dropna(subset=['date']).sort_values('date')
            df['month_year'] = df['date'].dt.strftime('%b %Y')
            df['day_name'] = df['date'].dt.day_name()
            df['hour'] = df['date'].dt.hour
            
            self.df = df
            self.monthly_df = df.groupby('month_year', sort=False).agg({'debit': 'sum', 'credit': 'sum'})
            return True, "Success"
        except Exception as e:
            return False, str(e)

    def get_fun_stats(self):
        d = self.df
        if d is None or d.empty: return {}

        total_out = d['debit'].sum()
        total_in = d['credit'].sum()
        
        ignore_kws = [
            'Interest', 'Internal', 'OWealth', 'Auto-save', 
            'POS Transfer', 'Electronic Money Trans', 'Mobile Data', 
            'Deposit', 'Withdrawal'
        ]
        
        pay_df = d[d['debit'] > 0].copy()
        for kw in ignore_kws:
            pay_df = pay_df[~pay_df['desc'].str.contains(kw, case=False, na=False)]
        
        def clean_name(desc):
            name = desc.replace('Transfer to ', '').replace('Payment to ', '')
            name = name.split('-')[0].split('/')[0].strip()
            return name[:22]

        top_people = pay_df['desc'].apply(clean_name).value_counts().head(5)

        avg_spend = d[d['debit'] > 0]['debit'].mean()
        weekend_spend = d[d['day_name'].isin(['Saturday', 'Sunday'])]['debit'].sum()
        weekend_pct = (weekend_spend / total_out * 100) if total_out > 0 else 0
        
        daily_sums = d.groupby(d['date'].dt.date)['debit'].sum()
        max_day = daily_sums.idxmax()
        max_day_val = daily_sums.max()

        data_keywords = ['Mobile Data', 'Data', 'Airtime', 'MTN', 'GLO', 'Airtel', '9mobile']
        data_df = d[d['debit'] > 0].copy()
        data_mask = data_df['desc'].str.contains('|'.join(data_keywords), case=False, na=False)
        total_data_spending = data_df[data_mask]['debit'].sum()
        data_pct = (total_data_spending / total_out * 100) if total_out > 0 else 0

        return {
            'out': f"₦{total_out:,.2f}",
            'in': f"₦{total_in:,.2f}",
            'net': f"₦{(total_in - total_out):,.2f}",
            'top_people': top_people,
            'avg_spend': f"₦{avg_spend:,.2f}",
            'weekend_pct': f"{weekend_pct:.1f}%",
            'busiest_day': max_day.strftime('%d %b'),
            'busiest_day_amt': f"₦{max_day_val:,.2f}",
            'count': len(d),
            'top_month': self.monthly_df['debit'].idxmax(),
            'total_data_spending': f"₦{total_data_spending:,.2f}",
            'data_pct': f"{data_pct:.1f}%"
        }

class ModernCard(QFrame):
    def __init__(self, color=Theme.CARD):
        super().__init__()
        self.setStyleSheet(f"background-color: {color}; border-radius: 15px; border: 1px solid #252525;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20); shadow.setColor(QColor(0,0,0,150)); shadow.setOffset(0,8)
        self.setGraphicsEffect(shadow)

class ChartWidget(FigureCanvas):
    def __init__(self):
        self.fig = Figure(figsize=(8, 4), facecolor=Theme.CARD)
        super().__init__(self.fig)

    def plot_monthly(self, monthly_df):
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor=Theme.CARD)
        x = np.arange(len(monthly_df))
        width = 0.35
        ax.bar(x - width/2, monthly_df['credit'], width, label='In', color=Theme.PRIMARY)
        ax.bar(x + width/2, monthly_df['debit'], width, label='Out', color=Theme.ACCENT_PINK)
        ax.set_xticks(x)
        ax.set_xticklabels(monthly_df.index, rotation=35, color=Theme.TEXT_DIM, fontsize=8)
        ax.legend(facecolor=Theme.CARD, labelcolor='white', framealpha=0)
        for s in ax.spines.values(): s.set_visible(False)
        self.fig.tight_layout()
        self.draw()

class APIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OpenAI API Key Configuration")
        self.setStyleSheet(f"""
            QDialog {{ background-color: {Theme.BG}; }}
            QLabel {{ color: {Theme.TEXT}; }}
            QLineEdit {{ 
                background-color: {Theme.CARD}; 
                color: {Theme.TEXT}; 
                border: 1px solid #252525; 
                border-radius: 5px; 
                padding: 8px;
            }}
            QPushButton {{
                background-color: {Theme.PRIMARY}; 
                color: black; 
                border-radius: 10px; 
                padding: 8px 20px; 
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #1ed760; }}
        """)
        self.setFixedSize(500, 200)
        layout = QVBoxLayout(self)
        
        label = QLabel("Enter your OpenAI API Key:")
        layout.addWidget(label)
        
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("sk-...")
        self.key_input.setText(os.getenv('OPENAI_API_KEY', ''))
        self.key_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.key_input)
        
        btn_layout = QHBoxLayout()
        btn_save = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_cancel)
        layout.addLayout(btn_layout)
    
    def get_api_key(self):
        return self.key_input.text()

class AIAdviceWorker(QThread):
    advice_ready = pyqtSignal(str)
    
    def __init__(self, advisor, stats):
        super().__init__()
        self.advisor = advisor
        self.stats = stats
    
    def run(self):
        advice = self.advisor.generate_advice(self.stats)
        self.advice_ready.emit(advice)

class OPayWrapped(QMainWindow):
    def __init__(self):
        super().__init__()
        self.analyzer = DataAnalyzer()
        api_key = os.getenv('OPENAI_API_KEY')
        self.ai_advisor = AIFinancialAdvisor(api_key=api_key)
        self.setWindowTitle("OPay Wrapped 2025")
        self.resize(1200, 1000)
        self.setStyleSheet(Theme.QSS)
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        self.layout = QVBoxLayout(central)
        
        header = QHBoxLayout()
        title_v = QVBoxLayout()
        t = QLabel("Your 2025 OPay Wrapped"); t.setStyleSheet("font-size: 32px; font-weight: 900;")
        st = QLabel("A summary of your year in money."); st.setStyleSheet(f"color: {Theme.TEXT_DIM};")
        title_v.addWidget(t); title_v.addWidget(st)
        
        self.btn_load = QPushButton("Load Statement"); self.btn_load.setObjectName("PrimaryBtn")
        self.btn_load.clicked.connect(self.load_file)
        
        self.btn_api_key = QPushButton("🔑 API Key"); self.btn_api_key.setObjectName("PrimaryBtn")
        self.btn_api_key.setStyleSheet(f"""
            QPushButton {{ background-color: {Theme.ACCENT_BLUE}; color: white; 
                           border-radius: 20px; padding: 12px 30px; font-weight: bold; font-size: 14px; }}
            QPushButton:hover {{ background-color: #6080F5; }}
        """)
        self.btn_api_key.clicked.connect(self.configure_api_key)
        
        header.addLayout(title_v); header.addStretch(); header.addWidget(self.btn_api_key); header.addWidget(self.btn_load)
        self.layout.addLayout(header)

        self.scroll = QScrollArea(); self.container = QWidget()
        self.grid = QGridLayout(self.container); self.scroll.setWidget(self.container)
        self.scroll.setWidgetResizable(True); self.layout.addWidget(self.scroll)
        
        self.msg_lbl = QLabel("Ready to analyze your year."); self.msg_lbl.setAlignment(Qt.AlignCenter)
        self.grid.addWidget(self.msg_lbl, 0, 0)

    def configure_api_key(self):
        dialog = APIKeyDialog(self)
        if dialog.exec_():
            api_key = dialog.get_api_key()
            if api_key:
                # Save to .env file
                env_file = '.env'
                with open(env_file, 'w') as f:
                    f.write(f"OPENAI_API_KEY={api_key}\n")
                load_dotenv(override=True)
                self.ai_advisor = AIFinancialAdvisor(api_key=api_key)
                QMessageBox.information(self, "Success", "API key saved successfully!")
            else:
                QMessageBox.warning(self, "Warning", "Please enter a valid API key.")

    def load_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select OPay File", "", "Data (*.csv *.xlsx)")
        if path:
            success, msg = self.analyzer.process_data(path)
            if success: self.build_dashboard()
            else: self.msg_lbl.setText(f"Error: {msg}")

    def build_dashboard(self):
        for i in reversed(range(self.grid.count())): self.grid.itemAt(i).widget().setParent(None)
        s = self.analyzer.get_fun_stats()

        self.add_stat_card("TOTAL INCOME", s['in'], Theme.PRIMARY, 0, 0)
        self.add_stat_card("TOTAL SPENT", s['out'], Theme.ACCENT_PINK, 0, 1)
        self.add_stat_card("NET BALANCE", s['net'], Theme.ACCENT_BLUE, 0, 2)

        chart_card = ModernCard(); cv = QVBoxLayout(chart_card)
        canvas = ChartWidget(); canvas.plot_monthly(self.analyzer.monthly_df)
        cv.addWidget(QLabel("MONTHLY TRENDS")); cv.addWidget(canvas)
        self.grid.addWidget(chart_card, 1, 0, 1, 2)

        people_card = ModernCard(); pv = QVBoxLayout(people_card)
        pv.addWidget(QLabel("TOP RECIPIENTS (Filtered)"))
        for name, count in s['top_people'].items():
            row = QWidget(); rl = QHBoxLayout(row); nl = QLabel(name); cl = QLabel(f"{count} tx")
            cl.setStyleSheet(f"color: {Theme.PRIMARY}; font-weight: bold;")
            rl.addWidget(nl); rl.addStretch(); rl.addWidget(cl); pv.addWidget(row)
        pv.addStretch(); self.grid.addWidget(people_card, 1, 2)

        self.add_stat_card("AVG PER TRANSACTION", s['avg_spend'], Theme.TEXT, 2, 0)
        self.add_stat_card("WEEKEND SPENDING %", s['weekend_pct'], Theme.ACCENT_GOLD, 2, 1)
        self.add_stat_card("TOTAL DATA SPENDING", s['total_data_spending'], Theme.ACCENT_BLUE, 2, 2)
        
        peak_card = ModernCard(); pk = QVBoxLayout(peak_card)
        pk.addWidget(QLabel("MOST EXPENSIVE DAY", styleSheet=f"color:{Theme.TEXT_DIM}; font-size:11px;"))
        pk.addWidget(QLabel(s['busiest_day'], styleSheet="font-size:24px; font-weight:800;"))
        pk.addWidget(QLabel(s['busiest_day_amt'], styleSheet=f"color:{Theme.ACCENT_PINK}; font-weight:bold;"))
        self.grid.addWidget(peak_card, 3, 0)
        
        advice_card = ModernCard(); av = QVBoxLayout(advice_card)
        advice_title = QLabel("🤖 AI FINANCIAL ADVISOR"); 
        advice_title.setStyleSheet(f"color: {Theme.PRIMARY}; font-size: 14px; font-weight: bold;")
        av.addWidget(advice_title)
        
        self.advice_label = QTextEdit()
        self.advice_label.setReadOnly(True)
        self.advice_label.setStyleSheet(f"""
            QTextEdit {{
                background-color: {Theme.CARD}; 
                color: {Theme.TEXT}; 
                border: 1px solid #252525; 
                border-radius: 10px; 
                padding: 10px;
                font-size: 12px;
            }}
        """)
        self.advice_label.setPlaceholderText("Generating financial advice...")
        self.advice_label.setMaximumHeight(200)
        av.addWidget(self.advice_label)
        self.grid.addWidget(advice_card, 3, 1, 1, 2)
        
        self.generate_ai_advice(s)

    def generate_ai_advice(self, stats_dict):
        """Generate AI advice in a background thread"""
        if not LANGCHAIN_AVAILABLE:
            error_msg = "LangChain/OpenAI packages not found.\n\n"
            error_msg += "Please install:\npip install langchain langchain-openai openai\n\n"
            if LANGCHAIN_ERROR:
                error_msg += f"Import error: {LANGCHAIN_ERROR}"
            self.advice_label.setText(error_msg)
            return
        
        if not self.ai_advisor.api_key:
            self.advice_label.setText("Please configure your OpenAI API key using the '🔑 API Key' button to get personalized financial advice.\n\nOr add OPENAI_API_KEY to your .env file.")
            return
        
        self.advice_label.setText("Analyzing your finances... This may take a few seconds.")
        self.worker = AIAdviceWorker(self.ai_advisor, stats_dict)
        self.worker.advice_ready.connect(lambda advice: self.advice_label.setText(advice))
        self.worker.start()

    def add_stat_card(self, title, val, color, r, c):
        card = ModernCard(); v = QVBoxLayout(card)
        tl = QLabel(title); tl.setStyleSheet(f"color: {Theme.TEXT_DIM}; font-size: 11px; font-weight: bold;")
        vl = QLabel(val); vl.setStyleSheet(f"color: {color}; font-size: 24px; font-weight: 800;")
        v.addWidget(tl); v.addWidget(vl); self.grid.addWidget(card, r, c)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OPayWrapped(); window.show()
    sys.exit(app.exec_())