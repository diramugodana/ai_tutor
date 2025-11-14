import os
from dotenv import load_dotenv

load_dotenv()

# Load critical environment variables (may be None in local dev)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Optional: helper to assert required envs during startup
def require_env(name: str):
	val = os.getenv(name)
	if not val:
		raise EnvironmentError(f"Required environment variable '{name}' is not set")
	return val
