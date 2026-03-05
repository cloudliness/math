import os
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openrouter import OpenRouter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def query_rag(query_text):
    print(f"Querying RAG system: {query_text}")
    
    # 1. Setup Models (Matching skill.md)
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
    from llama_index.llms.openai import OpenAI
    Settings.llm = OpenAI(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        api_base="https://openrouter.ai/api/v1",
        model="stepfun/step-3.5-flash:free",
        temperature=0.1,
    )
    
    # 2. Setup ChromaDB
    db = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = db.get_collection("discrete_math")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    
    # 3. Load Index
    index = VectorStoreIndex.from_vector_store(vector_store)
    
    # 4. Query
    query_engine = index.as_query_engine(streaming=False)
    response = query_engine.query(query_text)
    
    print("\n--- RESPONSE ---")
    print(response)
    print("\n--- SOURCES ---")
    for node in response.source_nodes:
        print(f"Score: {node.score:.4f} | Content Preview: {node.node.get_content()[:200]}...")
    
    return response

if __name__ == "__main__":
    # The previous query might have been too specific or outside the retrieved window
    TEST_QUERY = "What are propositional equivalences? Explain based on the provided text."
    query_rag(TEST_QUERY)
