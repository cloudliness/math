import os
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

def query_rag(query_text):
    print(f"--- RAG QUERY TEST ---")
    print(f"Query: {query_text}")
    
    try:
        # 1. Models
        print("Initializing models...")
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
        Settings.llm = OpenAI(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            api_base="https://openrouter.ai/api/v1",
            model="stepfun/step-3.5-flash:free",
            temperature=0.1,
            timeout=60.0 # Add timeout
        )
        
        # 2. Storage
        print("Connecting to ChromaDB...")
        db = chromadb.PersistentClient(path="./chroma_db")
        chroma_collection = db.get_collection("discrete_math")
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        index = VectorStoreIndex.from_vector_store(vector_store)
        
        # 3. Retrieval
        print("Retrieving context...")
        retriever = index.as_retriever(similarity_top_k=3)
        source_nodes = retriever.retrieve(query_text)
        
        if not source_nodes:
            print("FAILURE: No context retrieved!")
            return
            
        print(f"Retrieved {len(source_nodes)} context chunks.")
        for i, node in enumerate(source_nodes):
            print(f"Source {i+1} (Score: {node.score:.4f}): {node.node.get_content()[:150]}...")
            
        # 4. LLM Generation
        print("Generating LLM Response...")
        query_engine = index.as_query_engine(streaming=False)
        response = query_engine.query(query_text)
        
        if not str(response).strip():
            print("FAILURE: LLM returned an empty response.")
            # Let's try a direct chat test with the retrieved context
            context_str = "\n\n".join([n.node.get_content() for n in source_nodes])
            print("Attempting direct context-injected chat test...")
            prompt = f"Context:\n{context_str}\n\nQuestion: {query_text}\n\nAnswer based ON THE CONTEXT ONLY:"
            direct_resp = Settings.llm.complete(prompt)
            print(f"Direct Prompt Response: {direct_resp}")
        else:
            print("\n--- RESPONSE ---")
            print(response)
            
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    query_rag("Explain propositional equivalences.")
