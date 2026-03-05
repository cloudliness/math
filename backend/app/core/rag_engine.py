import os
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.openrouter import OpenRouter
from llama_index.core.llms import ChatMessage, MessageRole
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """You are a helpful discrete mathematics tutor. 
Answer the student's question using the provided context from a textbook.
Be clear and concise. Use proper mathematical notation where appropriate."""

# Max characters of context to send to the free model to avoid token limits
MAX_CONTEXT_CHARS = 1500

class RAGEngine:
    def __init__(self):
        self._initialize_settings()
        self.index = self._load_index()

    def _initialize_settings(self):
        Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")
        self.llm = OpenRouter(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            model="nvidia/nemotron-3-nano-30b-a3b:free",
            temperature=0.1,
            max_retries=3
        )
        Settings.llm = self.llm

    def _load_index(self):
        self.db_path = os.path.join(os.getcwd(), "..", "chroma_db")
        if not os.path.exists(self.db_path):
            self.db_path = os.path.join(os.getcwd(), "chroma_db")

        print(f"Connecting to ChromaDB at: {self.db_path}")
        self.db = chromadb.PersistentClient(path=self.db_path)
        self.chroma_collection = self.db.get_or_create_collection("discrete_math")
        vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        return VectorStoreIndex.from_vector_store(vector_store)

    def ingest_file(self, file_path):
        """Ingest a PDF file into the vector store."""
        from llama_parse import LlamaParse
        from llama_index.core import StorageContext

        parser = LlamaParse(
            api_key=os.environ.get("LLAMA_CLOUD_API_KEY"),
            result_type="markdown",
            verbose=True
        )
        documents = parser.load_data(file_path)

        vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        return len(documents)

    def query(self, query_text):
        # Step 1: Retrieve relevant chunks
        retriever = self.index.as_retriever(similarity_top_k=3)
        source_nodes = retriever.retrieve(query_text)

        if not source_nodes:
            return {"response": "I couldn't find relevant information in the textbook.", "sources": []}

        # Step 2: Build context string, truncating to fit free model limits
        context_parts = []
        sources = []
        total_chars = 0
        for node in source_nodes:
            content = node.node.get_content()
            sources.append({
                "score": node.score,
                "text": content[:200] + "..."
            })
            if total_chars + len(content) > MAX_CONTEXT_CHARS:
                remaining = MAX_CONTEXT_CHARS - total_chars
                if remaining > 100:
                    context_parts.append(content[:remaining])
                break
            context_parts.append(content)
            total_chars += len(content)
        
        context_str = "\n\n".join(context_parts)

        # Step 3: Use chat() API with structured messages
        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=SYSTEM_PROMPT),
            ChatMessage(
                role=MessageRole.USER,
                content=f"Context:\n{context_str}\n\nQuestion: {query_text}"
            ),
        ]

        try:
            print("Sending to LLM Chat API...")
            response = self.llm.chat(messages)
            print("LLM Chat API Raw Response:", response)
            response_text = str(response.message.content).strip() if response and hasattr(response, 'message') and response.message.content else ""
        except Exception as e:
            print(f"Exception during LLM chat: {e}")
            response_text = ""
            
        # Fallback: if still empty, try complete() with a shorter prompt
        if not response_text.strip():
            print("Chat response empty, trying complete() fallback...")
            short_context = context_str[:500]
            fallback_prompt = f"Based on this: {short_context}\n\nAnswer briefly: {query_text}"
            try:
                fallback_resp = self.llm.complete(fallback_prompt)
                fallback_text = str(fallback_resp).strip() if fallback_resp else ""
                
                # If still empty, supply the error message
                if not fallback_text:
                    response_text = "I received your question but the model didn't generate a response (it returned an empty response). Please try rephrasing."
                else:
                    response_text = fallback_text
            except Exception as e:
                print(f"Exception during LLM complete: {e}")
                response_text = f"I received your question, but encountered an error connecting to the AI: {e}"

        return {
            "response": response_text,
            "sources": sources
        }

# Singleton instance
rag_engine = None

def get_rag_engine():
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine
