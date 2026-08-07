FTA Banking Analytics


---

## Project Structure

```
banking_app/
├── app.py                   ← Flask backend
├── requirements.txt         ← Python packages
├── Procfile                 ← Render start command
├── generate_sample_data.py  ← Test data generator (optional)
└── templates/
    └── index.html           ← Full frontend (landing + dashboard)
```

---

## STEPS FOR Installing

```bash
# 1. Go into your project folder
cd banking_app

# 2. Create a virtual environment
python -m venv venv

# 3. Activate it
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# 4. Install all packages
pip install -r requirements.txt

# 5. (Optional) Generate sample test data
python generate_sample_data.py

# 6. Run the app
python app.py

# 7. Open your browser at:
#    http://localhost:5000
```

---

## ✅ Quick Checklist Before Deploying

- [ ] `app.py` is in the root of the folder (not inside a subfolder)
- [ ] `templates/index.html` exists
- [ ] `requirements.txt` lists all packages
- [ ] `Procfile` is present with the gunicorn command
- [ ] All 4 files are committed and pushed to GitHub
- [ ] Render build log shows `Build successful`

---

## 🧪 Testing the Dataset

Your Excel file must have these 4 columns (exact names):

| Column          | Type     | Example             |
|-----------------|----------|---------------------|
| TransactionDate | Date     | 2024-03-15          |
| Amount          | Number   | 15000.50            |
| TransactionType | Text     | Credit or Debit     |
| AccountType     | Text     | Savings / Current   |

Run `python generate_sample_data.py` to create a ready-to-use `banking_data.xlsx` with 500 rows.

---

## 💡 Tech Stack Summary

```
Frontend  → HTML5 + CSS3 + Vanilla JS + Chart.js 4
Backend   → Python 3 + Flask
Analytics → Pandas, NumPy, Scikit-Learn
Export    → OpenPyXL (Excel report)

```
