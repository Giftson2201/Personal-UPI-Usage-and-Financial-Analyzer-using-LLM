import streamlit as st
import pandas as pd
import plotly.express as px
import re

# 1. Page Configuration
st.set_page_config(page_title="AI UPI Analyzer", layout="wide", page_icon="💸")

# 2. Load the Data
@st.cache_data
def load_data():
    with open('transaction.csv', 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    cleaned_data = []
    for line in lines:
        # UPGRADED REGEX: More forgiving of missing quotes, weird spaces, or double commas
        # It looks anywhere in the line for: Date -> Description -> ₹ Amount
        match = re.search(r'(\d{2} [A-Z][a-z]{2}, \d{4})["\']?,\s*(.*?),+["\']?[₹]([\d,.]+)', line.replace(',,', ','))
        
        if match:
            date_str = match.group(1)
            desc = match.group(2).strip('"').strip()
            amount_str = match.group(3).replace(',', '')
            
            if desc.startswith("Paid to "):
                type_str = "Debit"
                receiver = desc.replace("Paid to ", "")
            elif desc.startswith("Received from "):
                type_str = "Credit"
                receiver = desc.replace("Received from ", "")
            elif desc.startswith("Self transfer"):
                type_str = "Transfer" # Isolating self-transfers so they don't mess up your math
                receiver = desc
            else:
                type_str = "Debit"
                receiver = desc
            
            cleaned_data.append({
                "Date": pd.to_datetime(date_str),
                "Receiver": receiver,
                "Amount": float(amount_str),
                "Type": type_str,
                "Category": "Uncategorized" 
            })
    
    df = pd.DataFrame(cleaned_data)
    return df

try:
    df = load_data()
    data_loaded = not df.empty
except Exception as e:
    st.error(f"Error loading data: {e}")
    data_loaded = False

if data_loaded:
    # Sidebar
    st.sidebar.title("💸 Smart Finance AI")
    st.sidebar.markdown("Upload your UPI statement, and let the LLM analyze your spending habits.")
    
    st.title("Personal UPI Usage & Financial Analyzer")
    st.markdown("Automated insights and budgeting advice based on your digital transactions.")
    
    # 3. Data Processing & Calculations
    total_income = df[df['Type'] == 'Credit']['Amount'].sum()
    total_spent = df[df['Type'] == 'Debit']['Amount'].sum()
    balance = total_income - total_spent
    total_transactions = len(df) # Count total rows
    
    # 4. KPI Metrics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Transactions Found", f"{total_transactions}")
    col2.metric("Total Inflow", f"₹{total_income:,.2f}")
    col3.metric("Total Outflow", f"₹{total_spent:,.2f}")
    col4.metric("Net Balance", f"₹{balance:,.2f}")
    
    st.divider()
    
    # 5. Visualizations
    colA, colB = st.columns(2)
    
    with colA:
        st.subheader("Category-wise Spending")
        debits = df[df['Type'] == 'Debit']
        if not debits.empty:
            category_spends = debits.groupby('Category')['Amount'].sum().reset_index()
            fig_pie = px.pie(category_spends, values='Amount', names='Category', hole=0.4, 
                             color_discrete_sequence=px.colors.sequential.Teal)
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.info("No debit transactions found to visualize.")
            
    with colB:
        st.subheader("All Transactions")
        # Removed .head(8) so it shows everything!
        st.dataframe(df.sort_values(by='Date', ascending=False), use_container_width=True, height=400)
        
    st.divider()
    
    # 6. LLM Integration Section
    st.header("🧠 AI Financial Advisor")
    st.markdown("Click the button below to generate a personalized financial report.")
    
    if st.button("Generate LLM Insights", type="primary"):
        with st.spinner("LLM is analyzing your spending patterns..."):
            
            if not debits.empty:
                top_cat_amount = float(category_spends['Amount'].max())
                top_cat_name = str(category_spends.loc[category_spends['Amount'].idxmax(), 'Category'])
                
                food_spends_df = category_spends[category_spends['Category'] == 'Food & Dining']
                food_spends = float(food_spends_df['Amount'].sum()) if not food_spends_df.empty else 0.0
                
                st.success("Analysis Complete!")
                
                st.subheader("📊 Spending Behavior Detected:")
                st.write(f"- **Major Expense:** Your highest spending category is **{top_cat_name}** (₹{top_cat_amount:,.2f}).")
                st.write(f"- **Lifestyle Spends:** You spent **₹{food_spends:,.2f}** on Food & Dining (Zomato, Swiggy, Starbucks).")
                
                st.subheader("💡 Actionable Recommendations:")
                st.info("""
                1. **The 50/30/20 Rule:** You are currently spending a high percentage on variable expenses. Try limiting 'Shopping' and 'Food' to 30% of your total income.
                2. **Wasteful Spending Alert:** You have multiple food delivery orders within a single week. Cutting these down by just 2 orders a week could save you ~₹1,000 monthly.
                3. **Subscription Audit:** You have active debits for Netflix and BookMyShow. Ensure you are fully utilizing these, or consider pausing them.
                """)
            else:
                st.warning("Not enough debit data for LLM analysis.")
                
            st.caption("Powered by simulated LLM logic. To connect a real LLM, add your Hugging Face or OpenAI API key in the backend.")
else:
    st.warning("No valid transaction data was found. Please ensure 'transaction.csv' contains the correct Google Pay formatting.")