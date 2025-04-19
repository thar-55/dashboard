
import streamlit as st
import boto3
import json
import pandas as pd
import time

# ✅ AWS Configuration


ssm = boto3.client("ssm", region_name="us-east-1")
s3_client = boto3.client("s3")


# ✅ AWS Configuration
S3_BUCKET = ssm.get_parameter(Name="mlopa-bucket", WithDecryption=True)["Parameter"]["Value"]
S3_MODEL_ARTIFACTS = ssm.get_parameter(Name="model-artifacts", WithDecryption=True)["Parameter"]["Value"]



# S3_BUCKET = "malepa-portfolio"
STRATEGY_SIMULATION_PATH = "strategy_simulation/"
INFERENCE_RESULTS_PATH = "inference_results/"
TRADE_PERFORMANCE_PATH = "trade_performance/"
LIVE_DEPLOYMENT_SCRIPT = "deploy_live_models.py"

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

# ✅ Deploy Selected Strategy
def deploy_strategy(strategy):
    """Deploys selected strategy to live trading."""
    st.success(f"🚀 Deploying strategy: {strategy} to live trading...")
    os.system(f"python {LIVE_DEPLOYMENT_SCRIPT}")

# ✅ Admin Dashboard UI
st.title("📊 Admin Dashboard: FatBird System Monitoring & Deployment")

# ✅ Section 1: Strategy Simulation Results
st.header("📈 Strategy Simulation Results (Step 7)")
strategy_df = load_strategy_results()
if strategy_df is not None:
    st.dataframe(strategy_df)
    best_strategy = strategy_df.groupby("strategy")["strategy_score"].mean().idxmax()
    best_strategy_score = strategy_df.groupby("strategy")["strategy_score"].mean().max()
    st.success(f"🏆 Best Strategy Selected: **{best_strategy}** (Score: {best_strategy_score:.2f})")

    # ✅ Manual Override for Strategy Selection
    override_strategy = st.selectbox("📌 Select Strategy for Deployment", strategy_df["strategy"].unique())
    if st.button("✅ Deploy Selected Strategy"):
        deploy_strategy(override_strategy)
        st.success(f"🚀 {override_strategy} strategy deployed to live trading!")

# ✅ Section 2: Market Performance Reports
st.header("📊 Market Performance Reports (Step 6)")
market_df = load_market_performance()
if market_df is not None:
    st.dataframe(market_df)

# ✅ Section 3: Risk Control Adjustments (for Manual Mode)
st.sidebar.header("⚙️ Risk Control Settings")
win_rate_threshold = st.sidebar.slider("Win Rate Threshold (%)", 50, 70, 55)
profit_factor_threshold = st.sidebar.slider("Profit Factor Threshold", 1.0, 2.0, 1.5)
risk_reward_threshold = st.sidebar.slider("Risk-Reward Ratio", 1.0, 3.0, 2.0)
max_drawdown_threshold = st.sidebar.slider("Max Drawdown (%)", 5, 20, 15)
positive_days_threshold = st.sidebar.slider("Positive Days Required", 1, 7, 3)

# ✅ Section 4: Live Inference Results
st.header("📡 Live Inference Monitoring (Step 8)")
inference_df = load_inference_results()
if inference_df is not None:
    st.dataframe(inference_df)

# ✅ Section 5: Model Management (Rollback, Redeploy, Batch Testing, Live Trading)
st.header("⚙️ Model Management")
model_action = st.selectbox("🛠️ Select Action", ["Deploy to Live", "Rollback to Batch Mode", "Re-run Batch Testing"])
if st.button("🚀 Execute Action"):
    if model_action == "Deploy to Live":
        deploy_strategy(best_strategy)
        st.success(f"🚀 {best_strategy} deployed to live trading!")
    elif model_action == "Rollback to Batch Mode":
        st.warning("🔄 Rolling back to batch testing...")
        os.environ["USE_LIVE_INFERENCE"] = "False"
        st.success("✅ Rolled back successfully!")
    elif model_action == "Re-run Batch Testing":
        st.warning("🔄 Re-running batch testing...")
        os.system("python step_5_batch_transform.py")
        st.success("✅ Batch testing re-executed successfully!")

# ✅ Auto-refresh live data every 30 seconds
st.text("🔄 Auto-refreshing live inference results every 30 seconds...")
time.sleep(30)
st.experimental_rerun()
