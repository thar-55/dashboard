import streamlit as st
import boto3
import json
import pandas as pd
import time

# ✅ AWS Configuration

# ✅ AWS Configuration
ssm = boto3.client("ssm", region_name="us-east-1")
s3_client = boto3.client("s3")


# ✅ AWS Configuration
S3_BUCKET = ssm.get_parameter(Name="mlopa-bucket", WithDecryption=True)["Parameter"]["Value"]
S3_MODEL_ARTIFACTS = ssm.get_parameter(Name="model-artifacts", WithDecryption=True)["Parameter"]["Value"]
# S3_BUCKET = "mlops-portfolio-bucket"
STRATEGY_SIMULATION_PATH = "strategy_simulation/"
INFERENCE_RESULTS_PATH = "inference_results/"
TRADE_PERFORMANCE_PATH = "trade_performance/"
USER_PREFERENCES_PATH = "user_preferences/"

# ✅ AWS Client
s3_client = boto3.client("s3")

# ✅ Fetch Strategy Simulation Results
def load_strategy_results():
    """Fetches strategy simulation results from Step 7."""
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=f"{STRATEGY_SIMULATION_PATH}strategy_performance.csv")
        df = pd.read_csv(obj["Body"])
        return df
    except Exception as e:
        st.error(f"❌ No strategy simulation results found. Error: {e}")
        return None

# ✅ Fetch Market Performance Reports (Step 6 Results)
def load_market_performance():
    """Fetches market performance data from Step 6."""
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=f"{TRADE_PERFORMANCE_PATH}trade_performance.csv")
        df = pd.read_csv(obj["Body"])
        return df
    except Exception as e:
        st.error(f"❌ No market performance data found. Error: {e}")
        return None

# ✅ Fetch Inference Results (Step 8 Results)
def load_inference_results():
    """Fetches live or batch inference results from Step 8."""
    try:
        obj = s3_client.get_object(Bucket=S3_BUCKET, Key=f"{INFERENCE_RESULTS_PATH}live_inference_results.csv")
        df = pd.read_csv(obj["Body"])
        return df
    except Exception as e:
        st.warning(f"⚠️ No live inference results found. Trying batch results.")
        return None

# ✅ Save User Preferences to S3
def save_user_preferences(trading_style, risk_settings):
    """Saves user-selected trading style and risk preferences to S3."""
    preferences = {
        "trading_style": trading_style,
        "risk_settings": risk_settings
    }
    try:
        s3_client.put_object(
            Bucket=S3_BUCKET,
            Key=f"{USER_PREFERENCES_PATH}user_preferences.json",
            Body=json.dumps(preferences)
        )
        st.success("✅ Preferences saved successfully!")
    except Exception as e:
        st.error(f"❌ Failed to save preferences. Error: {e}")

# ✅ User Dashboard UI
st.title("📈 User Dashboard: FatBird Trading & Analytics")

# ✅ Section 1: Trading Strategy Selection
st.header("🎯 Select Your Trading Strategy")
strategy_df = load_strategy_results()
if strategy_df is not None:
    selected_strategy = st.radio("📌 Choose a Trading Style", ["Trend", "Contrarian", "Hedging", "Swing"])
    st.success(f"📊 You have selected: **{selected_strategy}** strategy.")

# ✅ Section 2: Risk Control Adjustments
st.sidebar.header("⚙️ Risk Control Settings")
win_rate_threshold = st.sidebar.slider("Win Rate Threshold (%)", 50, 70, 55)
profit_factor_threshold = st.sidebar.slider("Profit Factor Threshold", 1.0, 2.0, 1.5)
risk_reward_threshold = st.sidebar.slider("Risk-Reward Ratio", 1.0, 3.0, 2.0)
max_drawdown_threshold = st.sidebar.slider("Max Drawdown (%)", 5, 20, 15)
positive_days_threshold = st.sidebar.slider("Positive Days Required", 1, 7, 3)

if st.sidebar.button("💾 Save Preferences"):
    save_user_preferences(selected_strategy, {
        "win_rate": win_rate_threshold,
        "profit_factor": profit_factor_threshold,
        "risk_reward": risk_reward_threshold,
        "max_drawdown": max_drawdown_threshold,
        "positive_days": positive_days_threshold
    })

# ✅ Section 3: Market Performance Reports
st.header("📊 Market Performance Reports (Step 6)")
market_df = load_market_performance()
if market_df is not None:
    st.dataframe(market_df)

# ✅ Section 4: Live Inference Results
st.header("📡 Live Inference Monitoring (Step 8)")
mode = st.radio("📈 Select Data Mode", ["📊 Batch Testing Data", "📡 Live Market Data"])
if mode == "📡 Live Market Data":
    inference_df = load_inference_results()
    if inference_df is not None:
        st.dataframe(inference_df)

# ✅ Section 5: Scenario Testing (Simulating Trade Outcomes)
st.header("🧪 Scenario Testing")
num_days = st.slider("⏳ Simulate Trading Performance Over Days", 7, 30, 14)
if st.button("🔄 Run Scenario Simulation"):
    st.success(f"✅ Simulated {num_days} days of trading based on {selected_strategy} strategy.")

# ✅ Auto-refresh live data every 30 seconds
st.text("🔄 Auto-refreshing live inference results every 30 seconds...")
time.sleep(30)
st.experimental_rerun()
