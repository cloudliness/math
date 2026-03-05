import os
from llama_index.llms.openrouter import OpenRouter
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))

def test_llm():
    print("Testing OpenRouter LLM (Stepfun 3.5)...")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found.")
        return
    
    try:
        llm = OpenRouter(
            api_key=api_key, 
            model="stepfun/step-3.5-flash:free",
            temperature=0.1
        )
        
        from llama_index.core.llms import ChatMessage, MessageRole
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            ChatMessage(role=MessageRole.USER, content="Hello, are you working? Please reply with 'Yes if you are.'")
        ]
        
        print("Testing .chat()")
        response = llm.chat(messages)
        print("Chat Response object:", response)
        
        content = response.message.content if hasattr(response, 'message') and hasattr(response.message, 'content') else None
        print(f"Response content: '{content}'")
        
        print(f"Response text using str(response.message.content): '{str(response.message.content) if response.message and response.message.content else ''}'")
        
    except Exception as e:
        print(f"LLM Test failed: {e}")

if __name__ == "__main__":
    test_llm()
