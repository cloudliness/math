import os
import chromadb
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openrouter import OpenRouter
from llama_parse import LlamaParse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def ingest_document(file_path):
    print(f"Starting ingestion for: {file_path}")
    
    # 1. Setup Models (Matching skill.md)
    print("Initializing models...")
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
    Settings.llm = OpenRouter(
        api_key=os.environ.get("OPENROUTER_API_KEY"),
        model="stepfun/step-3.5-flash:free"
    )
    
    # 2. Initialize LlamaParse
    print("Parsing document with LlamaParse...")
    parser = LlamaParse(
        api_key=os.environ.get("LLAMA_CLOUD_API_KEY"),
        result_type="markdown",  # Encouraged for math RAG
        verbose=True
    )
    
    # 3. Parse Document
    documents = parser.load_data(file_path)
    print(f"Successfully parsed into {len(documents)} document objects.")
    
    # 4. Setup ChromaDB
    print("Setting up ChromaDB...")
    db = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = db.get_or_create_collection("discrete_math")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    
    # 5. Create Index
    print("Creating index and storing in ChromaDB...")
    index = VectorStoreIndex.from_documents(
        documents, 
        storage_context=storage_context,
        show_progress=True
    )
    
    print("Ingestion complete!")
    return index

if __name__ == "__main__":
    PDF_PATH = "data/08_1 The Foundations Logic and Proofs.pdf"
    if os.path.exists(PDF_PATH):
        ingest_document(PDF_PATH)
    else:
        print(f"Error: File {PDF_PATH} not found.")
