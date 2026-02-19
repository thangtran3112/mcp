import logging
import os

from dotenv import load_dotenv
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents import LlmAgent
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

load_dotenv()

_currency_agent_url = os.getenv("CURRENCY_AGENT_URL", "http://localhost:10000")
_orchestrator_port = int(os.getenv("ORCHESTRATOR_PORT", "10001"))

logger.info("--- 🤖 Creating Orchestrator Agent... ---")
logger.info("--- 🔗 Delegating to currency_agent at %s ---", _currency_agent_url)

currency_remote = RemoteA2aAgent(
    name="currency_agent",
    agent_card=f"{_currency_agent_url}/.well-known/agent.json",
    description="A specialized agent that handles currency conversion and exchange rate queries",
)

root_agent = LlmAgent(
    model="gemini-2.5-flash",
    name="orchestrator_agent",
    description="An orchestrator agent that delegates to specialized sub-agents via A2A",
    instruction=(
        "You are a general-purpose assistant. "
        "For any questions about currency conversions or exchange rates, "
        "delegate to the currency_agent sub-agent. "
        "For all other questions, answer directly using your own knowledge."
    ),
    sub_agents=[currency_remote],
)

# Make the orchestrator itself A2A-compatible so it can be called by other agents
a2a_app = to_a2a(root_agent, port=_orchestrator_port)
