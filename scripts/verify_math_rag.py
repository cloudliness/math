import os
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from llama_index.llms.openrouter import OpenRouter

# This is a verification script to ensure the core components are working as expected.

def verify_embedding_model():
    print("Testing BGE-large-en-v1.5 Embedding Model...")
    try:
        embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
        test_text = "The Pigeonhole Principle states that if n items are put into m containers, with n > m, then at least one container must contain more than one item."
        embedding = embed_model.get_text_embedding(test_text)
        print(f"Embedding successful! Vector length: {len(embedding)}")
        return True
    except Exception as e:
        print(f"Embedding failed: {e}")
        return False

def verify_llm_setup():
    print("\nTesting OpenRouter LLM Setup (Stepfun 3.5)...")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in environment.")
        return False
    
    try:
        llm = OpenRouter(api_key=api_key, model="stepfun/step-3.5-flash:free")
        response = llm.complete("What is discrete math in one sentence?")
        print(f"LLM Response: {response}")
        return True
    except Exception as e:
        print(f"LLM Setup failed: {e}")
        return False

if __name__ == "__main__":
    # Note: Llama Cloud API key will be tested during the actual parsing phase
    embedding_ok = verify_embedding_model()
    # LLM test requires the key to be set in the shell
    # llm_ok = verify_llm_setup() 
    
    if embedding_ok:
        print("\nCore component verification successful.")
    else:
        print("\nVerification failed.")
