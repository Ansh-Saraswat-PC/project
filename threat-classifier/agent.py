import os
import logging
import google.cloud.logging
from dotenv import load_dotenv
from google.adk import Agent

# Setup Google Cloud Logging
try:
    cloud_logging_client = google.cloud.logging.Client()
    cloud_logging_client.setup_logging()
except Exception as e:
    logging.warning(f"Cloud logging not initialized: {e}")

load_dotenv()

CYBER_INSTRUCTIONS = """
You are a highly skilled cybersecurity triage AI.
Your task is to review the provided IT situation, code snippet, network condition, or user prompt and determine if it represents a security risk.

Format your response strictly as follows:
STATUS: [SAFE or UNSAFE]
REASONING: [Provide a concise, technical explanation of the potential risk or why the situation is secure. Highlight any specific vulnerabilities like XSS, SQLi, or open ports.]
MITIGATION: [If UNSAFE, provide a brief recommendation to secure it. If SAFE, output N/A.]
"""

root_agent = Agent(
    name="CyberSecurityTriage",
    model=os.getenv("MODEL", "gemini-2.5-flash"),
    instruction=CYBER_INSTRUCTIONS
)