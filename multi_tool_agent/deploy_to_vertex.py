import vertexai
from vertexai.preview import reasoning_engines
from vertexai import agent_engines
from agent import root_agent

# === CONFIGURE THESE ===
PROJECT_ID = "your-gcp-project-id"  # <-- Replace with your GCP project ID
LOCATION = "us-central1"            # Or another supported region
STAGING_BUCKET = "gs://your-bucket-name"  # <-- Replace with your GCS bucket

# === Initialize Vertex AI ===
vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

# === Wrap your root agent for Agent Engine ===
app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,  # Optional: enables trace logs for debugging
)

# === (Optional) Test locally ===
if __name__ == "__main__":
    print("Testing agent locally...")
    session = app.create_session(user_id="test_user")
    for event in app.stream_query(
        user_id="test_user",
        session_id=session.id,
        message="What is the account value?",
    ):
        print(event)

    print("\nDeploying agent to Vertex AI Agent Engine...")
    remote_app = agent_engines.create(
        agent_engine=root_agent,
        requirements=[
            "google-cloud-aiplatform[adk,agent_engines]",
            "alpaca-trade-api",
            "finvizfinance",
            "yfinance",
            "pandas",
            "numpy"
        ]
    )
    print("Deployed agent resource name:", remote_app.resource_name) 