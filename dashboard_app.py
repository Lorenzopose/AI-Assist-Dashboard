import streamlit as st
import pandas as pd
from google import genai 
import os
import matplotlib.pyplot as plt
from dotenv import load_dotenv

# ---------------------------
# 0. Load Environment Variables
# ---------------------------
load_dotenv()
MY_API_KEY = os.getenv("GEMINI_API_KEY")

# ---------------------------
# 1. Page Config & CSS
# ---------------------------
st.set_page_config(page_title="AI Business Dashboard", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #0E1117; color: #FAFAFA; }
section[data-testid="stSidebar"] { background-color: #111827; }
.stButton>button { background-color: #2563EB; color: white; border-radius: 6px; padding: 8px 14px; border: none; width: 100%; }
.stButton>button:hover { background-color: #1D4ED8; }
.stTextInput>div>div>input { background-color: #1F2937; color: white; }
</style>
""", unsafe_allow_html=True)

# ---------------------------
# 2. Gemini API Configuration
# ---------------------------
client = None
MODEL_ID = "gemini-2.5-flash-lite" 

if MY_API_KEY:
    try:
        client = genai.Client(api_key=MY_API_KEY)
    except Exception as e:
        st.sidebar.error(f"AI Initialization Failed: {e}")
else:
    st.sidebar.warning("⚠️ GEMINI_API_KEY not found in .env file.")

# ---------------------------
# 3. Header
# ---------------------------
st.title("AI Business Intelligence Dashboard")
st.write(f"Powered by: {MODEL_ID}")

# ---------------------------
# 4. Sidebar File Upload
# ---------------------------
st.sidebar.header("Data Input")
uploaded_file = st.sidebar.file_uploader("Upload CSV or XLSX", type=["csv", "xlsx"])

if uploaded_file:
    try:
        # Load Data
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"Loaded {uploaded_file.name} successfully!")
        tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "💡 AI Insights", "🤖 Ask AI"])

        # ---------------- DASHBOARD TAB ----------------
        with tab1:
            st.subheader("Data Overview")
            duplicate_count = df.duplicated().sum()

            # Metrics
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Rows", df.shape[0])
            m2.metric("Columns", df.shape[1])
            m3.metric("Missing Values", df.isnull().sum().sum())
            m4.metric("Duplicates", duplicate_count)

            # Previews
            col_a, col_b = st.columns(2)
            with col_a:
                st.write("**Data Preview**")
                st.dataframe(df.head(10), use_container_width=True)
            with col_b:
                st.write("**Summary Statistics**")
                st.dataframe(df.describe(), use_container_width=True)

            st.divider()
            
            # Duplicate Handling
            if duplicate_count > 0:
                st.warning(f"Found {duplicate_count} duplicate rows.")
                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("🔍 Show Duplicates"):
                        st.dataframe(df[df.duplicated(keep=False)])
                with btn2:
                    if st.button("🗑️ Remove Duplicates"):
                        df = df.drop_duplicates()
                        st.success("Duplicates removed!")
                        st.rerun()
            else:
                st.info("✅ No duplicate rows detected.")

            # --- VISUALIZATION SECTION (FIXED LABELS) ---
            st.divider()
            st.subheader("Quick Visualization")
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            
            if numeric_cols:
                plot_col = st.selectbox("Select a numeric column", numeric_cols)
                
                # Create the figure
                fig, ax = plt.subplots(figsize=(10, 4))
                
                # Dark Theme Styling for Matplotlib
                fig.patch.set_facecolor('#0E1117') 
                ax.set_facecolor('#1F2937')       
                
                # Draw the histogram
                df[plot_col].hist(ax=ax, bins=25, color='#2563EB', edgecolor='white')
                
                # EXPLICIT WHITE LABELS
                ax.set_title(f"Distribution of {plot_col}", color='white', fontsize=14)
                ax.set_xlabel(plot_col, color='white', fontsize=12)
                ax.set_ylabel("Frequency", color='white', fontsize=12)
                
                # Tick colors
                ax.tick_params(axis='x', colors='white')
                ax.tick_params(axis='y', colors='white')
                
                # Border colors
                for spine in ax.spines.values():
                    spine.set_edgecolor('white')
                
                fig.tight_layout()
                st.pyplot(fig)
            else:
                st.info("No numeric columns available for visualization.")

        # ---------------- INSIGHTS TAB ----------------
        with tab2:
            st.subheader("AI Data Analysis")
            if client:
                if st.button("✨ Generate AI Insights"):
                    with st.spinner("Analyzing..."):
                        prompt = f"Analyze these columns: {list(df.columns)}. Sample data: {df.head(3).to_string()}"
                        # Using the new model variable
                        response = client.models.generate_content(model=MODEL_ID, contents=prompt)
                        st.markdown(response.text)
            else:
                st.error("AI Client not initialized. Check your .env file.")

        # ---------------- CHAT TAB ----------------
        with tab3:
            st.subheader("Chat with your Data")
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            if client:
                user_input = st.text_input("Ask a question about the dataset", key="chat_input")
                if user_input:
                    with st.spinner("Thinking..."):
                        response = client.models.generate_content(
                            model=MODEL_ID, # Using the new model variable
                            contents=f"Context: {df.head().to_string()}\n\nQuestion: {user_input}"
                        )
                        st.session_state.chat_history.append(f"You: {user_input}")
                        st.session_state.chat_history.append(f"AI: {response.text}")
                    
                    for msg in reversed(st.session_state.chat_history):
                        st.info(msg)
            else:
                st.error("AI Client not initialized.")

    except Exception as e:
        st.error(f"App Error: {e}")
else:
    st.info("👋 Welcome! Please upload a CSV or Excel file to begin.")