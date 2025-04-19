import pandas as pd
import numpy as np
import logging
import os
import boto3
import json
import streamlit as st  # ✅ Interactive dashboard for monitoring
import subprocess

# ✅ AWS Configuration
ssm = boto3.client("ssm", region_name="us-east-1")
s3_client = boto3.client("s3")


# ✅ AWS Configuration
BUCKET_NAME = ssm.get_parameter(Name="mlopa-bucket", WithDecryption=True)["Parameter"]["Value"]
S3_MODEL_ARTIFACTS = ssm.get_parameter(Name="model-artifacts", WithDecryption=True)["Parameter"]["Value"]
INFERENCE_RESULTS_PATH = "inference_results/"
STRATEGY_SIMULATION_PATH = "strategy_simulation/"
LOCAL_STRATEGY_FILE = "strategy_performance.csv"
STAGING_INFERENCE_FILE = "staging_inference_results.csv"
LIVE_INFERENCE_FILE = "live_inference_results.csv"

# ✅ AWS Clients
s3_client = boto3.client("s3")

# ✅ Configure Logging
logging.basicConfig(
    filename="strategy_simulation.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# ✅ Default Performance Thresholds
DEFAULT_THRESHOLDS = {
    "win_rate": 55,
    "profit_factor": 1.5,
    "risk_reward": 2.0,
    "max_drawdown": 15,
    "positive_days": 3
}

# ✅ Monte Carlo Simulation Parameters
MC_SIMULATIONS = 1000  # Number of random strategy simulations

# ✅ Load Inference Results from S3
def fetch_inference_results(is_live=False):
    """Loads the latest inference results (staging or live) from S3."""
    file_name = LIVE_INFERENCE_FILE if is_live else STAGING_INFERENCE_FILE
    s3_path = f"{INFERENCE_RESULTS_PATH}{file_name}"
    
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_path)
        df = pd.read_csv(response["Body"])
        logging.info(f"✅ Loaded inference results from {s3_path}")
        return df
    except Exception as e:
        logging.error(f"❌ Failed to load inference results: {e}")
        return pd.DataFrame()

# ✅ Monte Carlo Strategy Simulation
def monte_carlo_simulation(inference_df):
    """Runs Monte Carlo simulations on trading strategies using inference data."""
    if inference_df.empty:
        logging.error("❌ No valid inference data for strategy simulation.")
        return pd.DataFrame()

    np.random.seed(42)  # Ensures reproducibility
    strategies = ["Trend", "Contrarian", "Hedging", "Swing"]
    simulation_results = []

    for strategy in strategies:
        for _ in range(MC_SIMULATIONS):
            simulated_trades = np.random.choice(inference_df["predicted_price"], size=30, replace=True)
            profit = simulated_trades.mean()
            drawdown = np.random.uniform(5, 15)  # Randomized drawdown % for simulation
            win_rate = np.random.uniform(50, 70)  # Randomized win rate % for simulation

            # ✅ Compute Strategy Score
            strategy_score = (
                (win_rate * 0.4) +
                (profit * 0.3) +
                (profit / drawdown * 0.2) -
                (drawdown * 0.1)
            )

            simulation_results.append({
                "strategy": strategy,
                "profit": profit,
                "drawdown": drawdown,
                "win_rate": win_rate,
                "strategy_score": strategy_score
            })

    final_df = pd.DataFrame(simulation_results)
    logging.info("✅ Strategy simulation completed.")
    return final_df

# ✅ Upload Strategy Results to S3
def upload_strategy_results(strategy_df):
    """Uploads strategy simulation results to S3 for performance monitoring."""
    if strategy_df.empty:
        logging.error("❌ No strategy results to upload.")
        return

    strategy_df.to_csv(LOCAL_STRATEGY_FILE, index=False)
    
    try:
        s3_path = f"{STRATEGY_SIMULATION_PATH}{LOCAL_STRATEGY_FILE}"
        s3_client.upload_file(LOCAL_STRATEGY_FILE, BUCKET_NAME, s3_path)
        logging.info(f"✅ Strategy simulation results uploaded to S3: s3://{BUCKET_NAME}/{s3_path}")
    except Exception as e:
        logging.error(f"❌ Failed to upload strategy results: {e}")

# ✅ Evaluate Best Strategy for Deployment
def check_best_strategy(strategy_df):
    """Identifies the best strategy based on multi-metric evaluation before transitioning to live trading."""
    if strategy_df.empty:
        logging.error("❌ No strategy data to evaluate.")
        return None

    best_strategy = strategy_df.groupby("strategy")["strategy_score"].mean().idxmax()
    best_strategy_score = strategy_df.groupby("strategy")["strategy_score"].mean().max()

    logging.info(f"🏆 Best Strategy Selected: {best_strategy} with Score: {best_strategy_score:.2f}")

    # ✅ Check if strategy meets deployment conditions
    strategy_df = strategy_df[strategy_df["strategy"] == best_strategy]
    avg_win_rate = strategy_df["win_rate"].mean()
    avg_profit_factor = strategy_df["profit"].sum() / abs(strategy_df[strategy_df["profit"] < 0]["profit"].sum()) if any(strategy_df["profit"] < 0) else float("inf")
    avg_risk_reward = strategy_df["profit"].mean() / abs(strategy_df["drawdown"].mean()) if strategy_df["drawdown"].mean() != 0 else float("inf")

    if (
        avg_win_rate >= DEFAULT_THRESHOLDS["win_rate"]
        and avg_profit_factor >= DEFAULT_THRESHOLDS["profit_factor"]
        and avg_risk_reward >= DEFAULT_THRESHOLDS["risk_reward"]
    ):
        logging.info(f"🚀 Deploying {best_strategy} strategy to live trading.")
        return best_strategy
    else:
        logging.info("⚠️ No strategy met the threshold for live deployment.")
        return None

# ✅ Streamlit UI for Strategy Simulation
st.title("📊 Strategy Simulation & Monte Carlo Analysis")

# ✅ Toggle Between Staging & Live Data
use_live = st.sidebar.checkbox("Use Live Inference Data", value=False)

# ✅ Run Strategy Simulation
if st.button("🔄 Run Strategy Simulation"):
    inference_df = fetch_inference_results(is_live=use_live)
    strategy_results_df = monte_carlo_simulation(inference_df)
    
    if not strategy_results_df.empty:
        upload_strategy_results(strategy_results_df)
        best_strategy = check_best_strategy(strategy_results_df)
        
        st.success(f"✅ Strategy simulation completed! Best strategy: {best_strategy if best_strategy else 'None'}")
        st.dataframe(strategy_results_df)
    else:
        st.error("❌ No valid strategy results.")

