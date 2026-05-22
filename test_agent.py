import traceback
from Backend.rag_pipeline import get_agent_executor

try:
    agent = get_agent_executor()
    result = agent.invoke({'input': 'How can I book a meeting?'})
    print("SUCCESS:", result)
except Exception as e:
    print("ERROR CAUGHT:")
    traceback.print_exc()
