import streamlit as st
import pdfplumber
import pandas as pd
import io
import re

# Category rules
def categorize(description):
    description = description.lower()
    rules = {
        'Food': ['swiggy', 'zomato', 'restaurant', 'dominos'],
        'Groceries': ['bigbasket', 'dmart', 'reliance'],
        'Transport': ['uber', 'ola', 'fuel', 'petrol'],
        'Shopping': ['amazon', 'flipkart', 'myntra'],
        'Entertainment': ['netflix', 'hotstar', 'spotify'],
        'Salary': ['salary', 'credit'],
        'Bills': ['electricity', 'mobile', 'internet'],
        'Others': []
    }
    for cat, keys in rules.items():
        if any(k in description for k in keys):
            return cat
    return 'Others'

# Parser function
def parse_icici_pdf(file, password, account_type):
    transactions = []
    with pdfplumber.open(file, password=password) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split('\n')
            for line in lines:
                if re.match(r'\d{2}-\d{2}-\d{4}', line):
                    parts = line.split()
                    date = parts[0]
                    amount = parts[-2].replace(',', '')
                    balance = parts[-1].replace(',', '') if account_type == 'Debit' else None
                    description = ' '.join(parts[1:-2 if balance else -1])
                    try:
                        transactions.append([
                            pd.to_datetime(date, format='%d-%m-%Y'),
                            description,
                            float(amount),
                            float(balance) if balance else None,
                            account_type
                        ])
                    except:
                        continue
    df = pd.DataFrame(transactions, columns=['Date', 'Description', 'Amount', 'Balance', 'Account Type'])
    df['Category'] = df['Description'].apply(categorize)
    df['Type'] = df['Amount'].apply(lambda x: 'Income' if x > 0 else 'Expense')
    return df

# UI
st.title("💰 ICICI Personal Finance Tracker")

password = st.text_input("🔐 Enter PDF Password", type="password")

uploaded_debit = st.file_uploader("📄 Upload ICICI Debit Card Statement", type="pdf")
uploaded_credit = st.file_uploader("📄 Upload ICICI Credit Card Statement", type="pdf")

if password and (uploaded_debit or uploaded_credit):
    all_data = []

    if uploaded_debit:
        st.write("Processing Debit Card Statement...")
        df_debit = parse_icici_pdf(uploaded_debit, password, "Debit")
        all_data.append(df_debit)

    if uploaded_credit:
        st.write("Processing Credit Card Statement...")
        df_credit = parse_icici_pdf(uploaded_credit, password, "Credit")
        all_data.append(df_credit)

    if all_data:
        df = pd.concat(all_data)
        st.success("✅ Data Parsed Successfully!")

        # Summary
        st.subheader("📊 Summary")
        st.metric("Total Income", f"₹{df[df['Type']=='Income']['Amount'].sum():,.2f}")
        st.metric("Total Expenses", f"₹{df[df['Type']=='Expense']['Amount'].sum():,.2f}")

        # Category Pie
        st.subheader("🧾 Expenses by Category")
        cat_data = df[df['Type'] == 'Expense'].groupby('Category')['Amount'].sum().sort_values(ascending=False)
        st.bar_chart(cat_data)

        # Download Button
        st.subheader("⬇️ Export Data")
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        towrite.seek(0)
        st.download_button("📥 Download Excel Report", towrite, "icici_report.xlsx")

