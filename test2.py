from langchain_community.chat_models import ChatOllama
from langchain.tools import tool
from langgraph.prebuilt import create_react_agent

@tool
def hitung_matematika(ekspresi: str) -> str:
    """Gunakan tool ini HANYA ketika Anda perlu menghitung operasi matematika yang rumit."""
    return str(eval(ekspresi, {"__builtins__": None}))

llm = ChatOllama(model="qwen", base_url="http://localhost:11434")
tools = [hitung_matematika]

# test agent
agent = create_react_agent(llm, tools=tools, state_modifier="Anda adalah asisten AI ramah.")
try:
    # Just a small local test without hitting real network unless it works
    print("Agent created successfully.")
except Exception as e:
    print(f"Error: {e}")
