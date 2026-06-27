from flask import Flask, render_template, request, jsonify, send_file, session
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fta_banking_analytics_2025')

UPLOAD_FOLDER = '/tmp/banking_uploads'
REPORT_FOLDER = '/tmp/banking_reports'
for folder in [UPLOAD_FOLDER, REPORT_FOLDER]:
    os.makedirs(folder, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def analyze_banking_data(filepath):
    df = pd.read_excel(filepath)
    df.drop_duplicates(inplace=True)
    df.dropna(subset=['Amount', 'TransactionType', 'AccountType', 'TransactionDate'], inplace=True)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df.dropna(subset=['Amount'], inplace=True)

    df["TransactionDate"] = pd.to_datetime(df["TransactionDate"])
    df["Year"]  = df["TransactionDate"].dt.year
    df["Month"] = df["TransactionDate"].dt.month
    df["Day"]   = df["TransactionDate"].dt.day

    results = {}
    credit_df = df[df["TransactionType"] == "Credit"]
    debit_df  = df[df["TransactionType"] == "Debit"]

    # 1. Summary
    results['summary'] = {
        'total_transactions': int(len(df)),
        'total_amount':       round(float(df["Amount"].sum()), 2),
        'avg_transaction':    round(float(df["Amount"].mean()), 2),
        'max_transaction':    round(float(df["Amount"].max()), 2),
        'min_transaction':    round(float(df["Amount"].min()), 2),
        'total_credit':       round(float(credit_df["Amount"].sum()), 2),
        'total_debit':        round(float(debit_df["Amount"].sum()), 2),
        'credit_count':       int(len(credit_df)),
        'debit_count':        int(len(debit_df)),
    }

    # 2. Transaction type counts
    tc = df["TransactionType"].value_counts()
    results['transaction_types'] = {'labels': list(tc.index), 'values': [int(v) for v in tc.values]}

    # 3. Account type distribution
    ac = df["AccountType"].value_counts()
    results['account_types'] = {'labels': list(ac.index), 'values': [int(v) for v in ac.values]}

    # 4. Monthly trend
    MONTHS = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    monthly = df.groupby("Month")["Amount"].sum()
    results['monthly_trend'] = {
        'labels': [MONTHS[m-1] for m in monthly.index],
        'values': [round(float(v), 2) for v in monthly.values]
    }

    # 5. Monthly credit vs debit
    cm = credit_df.groupby("Month")["Amount"].sum()
    dm = debit_df.groupby("Month")["Amount"].sum()
    all_m = sorted(set(list(cm.index) + list(dm.index)))
    results['monthly_breakdown'] = {
        'labels': [MONTHS[m-1] for m in all_m],
        'credit': [round(float(cm.get(m, 0)), 2) for m in all_m],
        'debit':  [round(float(dm.get(m, 0)), 2) for m in all_m],
    }

    # 6. Amount histogram
    hist_vals, bin_edges = np.histogram(df["Amount"].dropna(), bins=15)
    results['amount_distribution'] = {
        'labels': [f'{int(bin_edges[i])}-{int(bin_edges[i+1])}' for i in range(len(hist_vals))],
        'values': [int(v) for v in hist_vals]
    }

    # 7. Outlier analysis (IQR)
    Q1 = df["Amount"].quantile(0.25)
    Q3 = df["Amount"].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = df[(df["Amount"] < lower) | (df["Amount"] > upper)]
    results['outlier_analysis'] = {
        'count':       int(len(outliers)),
        'percentage':  round(float(len(outliers) / len(df) * 100), 2),
        'lower_bound': round(float(lower), 2),
        'upper_bound': round(float(upper), 2),
        'q1':          round(float(Q1), 2),
        'q3':          round(float(Q3), 2),
        'iqr':         round(float(IQR), 2),
    }

    # 8. Top 10 transactions
    top10 = df.nlargest(10, "Amount")[["TransactionDate","AccountType","TransactionType","Amount"]].copy()
    top10["TransactionDate"] = top10["TransactionDate"].dt.strftime('%Y-%m-%d')
    results['top_transactions'] = top10.to_dict('records')

    # 9. Daily trend (last 30 days)
    daily = df.groupby("TransactionDate")["Amount"].sum().reset_index()
    daily = daily.sort_values("TransactionDate").tail(30)
    results['daily_trend'] = {
        'labels': [d.strftime('%b %d') for d in daily["TransactionDate"]],
        'values': [round(float(v), 2) for v in daily["Amount"].values]
    }

    # 10. ML Models
    if len(df) > 20:
        df_ml = df.copy()
        le1, le2 = LabelEncoder(), LabelEncoder()
        df_ml["AccountType_enc"]     = le1.fit_transform(df_ml["AccountType"])
        df_ml["TransactionType_enc"] = le2.fit_transform(df_ml["TransactionType"])
        X = df_ml[["AccountType_enc","TransactionType_enc","Month","Day"]]
        y = df_ml["Amount"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        lr = LinearRegression()
        lr.fit(X_train, y_train)
        pred_lr = lr.predict(X_test)

        rf = RandomForestRegressor(n_estimators=100, random_state=42)
        rf.fit(X_train, y_train)
        pred_rf = rf.predict(X_test)

        n = min(15, len(y_test))
        results['ml_results'] = {
            'linear_regression': {
                'mae':  round(float(mean_absolute_error(y_test, pred_lr)), 2),
                'rmse': round(float(np.sqrt(mean_squared_error(y_test, pred_lr))), 2),
                'r2':   round(float(r2_score(y_test, pred_lr)), 4),
            },
            'random_forest': {
                'mae':  round(float(mean_absolute_error(y_test, pred_rf)), 2),
                'rmse': round(float(np.sqrt(mean_squared_error(y_test, pred_rf))), 2),
                'r2':   round(float(r2_score(y_test, pred_rf)), 4),
            },
            'sample_predictions': {
                'labels':        [f'T-{i+1}' for i in range(n)],
                'actual':        [round(float(v), 2) for v in y_test.values[:n]],
                'random_forest': [round(float(v), 2) for v in pred_rf[:n]],
            }
        }

    # 11. Pivot table
    pivot = pd.pivot_table(df, values="Amount", index="AccountType",
                           columns="TransactionType", aggfunc="sum", fill_value=0)
    pivot_records = []
    for acc_type in pivot.index:
        row = {'account_type': str(acc_type)}
        for col in pivot.columns:
            row[str(col)] = round(float(pivot.loc[acc_type, col]), 2)
        pivot_records.append(row)
    results['pivot_table']   = pivot_records
    results['pivot_columns'] = [str(c) for c in pivot.columns]

    # Generate Excel report
    report_path = os.path.join(REPORT_FOLDER, 'Banking_Analytics_Report.xlsx')
    with pd.ExcelWriter(report_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='CleanData', index=False)
        pd.DataFrame([results['summary']]).to_excel(writer, sheet_name='Summary', index=False)
        top10.to_excel(writer, sheet_name='Top_Transactions', index=False)
        if 'ml_results' in results:
            ml = results['ml_results']['sample_predictions']
            pd.DataFrame({
                'Sample':       ml['labels'],
                'Actual':       ml['actual'],
                'RF_Predicted': ml['random_forest'],
            }).to_excel(writer, sheet_name='ML_Predictions', index=False)

    results['report_path'] = report_path
    return results


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'Please upload an Excel file (.xlsx or .xls)'}), 400
    try:
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        results = analyze_banking_data(filepath)
        session['report_path'] = results.pop('report_path', None)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/download-report')
def download_report():
    report_path = session.get('report_path')
    if not report_path or not os.path.exists(report_path):
        return jsonify({'error': 'No report found. Upload data first.'}), 404
    return send_file(
        report_path,
        as_attachment=True,
        download_name='Banking_Analytics_Report.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
