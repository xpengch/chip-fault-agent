import sys
sys.path.insert(0, ".")

print("Testing imports...")

try:
    from src.agents.agent1 import Agent1, Agent1State
    print("OK Agent1 import")
except Exception as e:
    print(f"FAIL Agent1 import: {e}")

try:
    from src.agents.agent2 import Agent2, Agent2State
    print("OK Agent2 import")
except Exception as e:
    print(f"FAIL Agent2 import: {e}")

try:
    from src.agents.workflow import ChipFaultWorkflow, get_workflow
    print("OK Workflow import")
except Exception as e:
    print(f"FAIL Workflow import: {e}")

try:
    from src.auth import AuthService
    print("OK Auth service import")
except Exception as e:
    print(f"FAIL Auth service import: {e}")

try:
    from src.api.app import app
    print("OK API app import")
except Exception as e:
    print(f"FAIL API app import: {e}")

print("\nAll imports tested!")
