"""
Run this once to generate a sample banking_data.xlsx for testing.
  python generate_sample_data.py
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

random.seed(42)
np.random.seed(42)

n = 500
start = datetime(2024, 1, 1)

account_types  = ['Savings', 'Current', 'Fixed Deposit', 'Salary']
txn_types      = ['Credit', 'Debit']

dates   = [start + timedelta(days=random.randint(0, 364)) for _ in range(n)]
amounts = np.round(np.random.exponential(scale=15000, size=n) + 500, 2)
# Inject a few outliers
amounts[5]  = 850000
amounts[42] = 720000
amounts[99] = 1200000

data = pd.DataFrame({
    'TransactionDate': dates,
    'AccountType':     [random.choice(account_types) for _ in range(n)],
    'TransactionType': [random.choice(txn_types)     for _ in range(n)],
    'Amount':          amounts,
})

data.sort_values('TransactionDate', inplace=True)
data.reset_index(drop=True, inplace=True)

data.to_excel('banking_data.xlsx', index=False)
print(f"Generated banking_data.xlsx  →  {n} rows")
print(data.head())
