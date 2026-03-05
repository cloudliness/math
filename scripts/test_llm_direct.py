import os
from llama_index.llms.openrouter import OpenRouter
from dotenv import load_dotenv

load_dotenv()

def test_llm():
    print("Testing OpenRouter LLM (Stepfun 3.5)...")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found.")
        return
    
    try:
        # Explicitly setting base_url just in case, though the provider usually handles it
        llm = OpenRouter(
            api_key=api_key, 
            model="stepfun/step-3.5-flash:free",
            temperature=0.1
        )
        response = llm.complete("Hello, are you working? Please reply with 'Yes' if you are.")
        print(f"Response: '{response}'")
    except Exception as e:
        print(f"LLM Test failed: {e}")

if __name__ == "__main__":
    test_llm()
