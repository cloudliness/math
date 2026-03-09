import os
import chromadb
from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core.embeddings import BaseEmbedding
from llama_index.llms.openrouter import OpenRouter
from llama_index.core.llms import ChatMessage, MessageRole
import requests
from dotenv import load_dotenv

class OpenRouterEmbedding(BaseEmbedding):
    """Custom embedding class for OpenRouter API."""
    model_name: str
    api_key: str
    api_base: str = "https://openrouter.ai/api/v1"

    def __init__(self, model_name: str, api_key: str, **kwargs):
        super().__init__(model_name=model_name, api_key=api_key, **kwargs)

    def _get_query_embedding(self, query: str) -> list[float]:
        return self._get_text_embedding(query)

    def _get_text_embedding(self, text: str) -> list[float]:
        import time
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "input": [text],
            "model": self.model_name
        }
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(f"{self.api_base}/embeddings", headers=headers, json=payload, timeout=30)
                response.raise_for_status()
                data = response.json()
                return data["data"][0]["embedding"]
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Failed to get embedding after {max_retries} attempts: {e}")
                    raise
                time.sleep(2 ** attempt)  # Exponential backoff

    async def _aget_query_embedding(self, query: str) -> list[float]:
        return self._get_query_embedding(query)

    async def _aget_text_embedding(self, text: str) -> list[float]:
        return self._get_text_embedding(text)

# Load environment variables
load_dotenv()

SYSTEM_PROMPT = """You are a helpful discrete mathematics tutor. 
Answer the student's question using the provided context from a textbook.
Be clear and concise. Use proper mathematical notation where appropriate.

CRITICAL VISUALIZATION INSTRUCTIONS:
If the user asks for a visual representation (plot, graph, flowchart, tree, etc.), you MUST return a SINGLE JSON object. 
Do NOT provide Python code, scripts, or instructions to run external libraries (like matplotlib or numpy).
Do NOT wrap the JSON in markdown code blocks.
The entire response MUST be a pure, parseable JSON object with the following schema:

For FLOWCHARTS, TREES, GRAPHS, or AUTOMATA:
{
  "text_explanation": "Markdown text explanation here.",
  "react_flow_data": {
    "nodes": [{"id": "1", "data": {"label": "Node Label"}, "position": {"x": 100, "y": 100}}],
    "edges": [{"id": "e1-2", "source": "1", "target": "2"}]
  }
}

For COORDINATE PLOTS, FUNCTIONS, or GROWTH CHARTS (e.g. Big-O):
{
  "text_explanation": "Markdown text explanation here.",
  "mafs_data": {
    "functions": [{"expression": "x^2", "color": "blue"}],
    "points": [{"x": 5, "y": 25, "label": "P"}],
    "view_window": {"x": [-5, 5], "y": [-5, 50]}
  }
}

WARNING: If the user DOES NOT ask for a visual, respond with standard Markdown text normally. If they DO ask for a visual, you MUST use the JSON format above.
"""

# Max characters of context to send to the free model to avoid token limits
MAX_CONTEXT_CHARS = 1500

class RAGEngine:
    def __init__(self):
        self._initialize_settings()
        self.index = self._load_index()

    def _initialize_settings(self):
        # We use a custom class to avoid OpenAI-specific validation errors with OpenRouter
        Settings.embed_model = OpenRouterEmbedding(
            model_name="nvidia/llama-nemotron-embed-vl-1b-v2:free",
            api_key=os.environ.get("OPENROUTER_API_KEY")
        )
        self.llm = OpenRouter(
            api_key=os.environ.get("OPENROUTER_API_KEY"),
            model="google/gemini-2.0-flash-001",
            temperature=0.1,
            max_tokens=2000,
            max_retries=3
        )
        Settings.llm = self.llm

    def _load_index(self):
        self.db_path = os.environ.get("CHROMA_DB_DIR")
        if not self.db_path:
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
        
        # Add file_name to metadata for each document
        file_name = os.path.basename(file_path)
        for doc in documents:
            doc.metadata["file_name"] = file_name

        vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        self.index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        return len(documents)

    def delete_document(self, filename: str):
        """Delete all chunks associated with a specific file from the vector store."""
        print(f"Deleting document '{filename}' from ChromaDB.")
        # We need to query chromadb directly to delete by metadata
        self.chroma_collection.delete(where={"file_name": filename})
        # Reset the index connected to this updated collection
        vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
        self.index = VectorStoreIndex.from_vector_store(vector_store)

    def query(self, query_text, active_documents=None):
        # Step 1: Retrieve relevant chunks
        
        # Determine if we need to filter by document
        retriever_kwargs = {"similarity_top_k": 3}
        if active_documents is not None:
            if not active_documents:
                # If active_documents is an empty list, user toggled off ALL documents.
                return {"response": "You have disabled all documents for context. Please enable at least one to ask questions about them.", "sources": []}
            
            from llama_index.core.vector_stores import MetadataFilters, ExactMatchFilter
            # Build filters dynamically based on how many documents are active
            filters = [ExactMatchFilter(key="file_name", value=doc_name) for doc_name in active_documents]
            # When there are multiple filters with 'or', LlamaIndex might require specific Condition construction depending on version.
            # Using ChromaDB's built-in capability might be easier if LlamaIndex MetadataFilters complains about IN clauses, 
            # but we can try simple MetadataFilters with condition="or".
            from llama_index.core.vector_stores import MetadataFilter, FilterOperator, FilterCondition
            
            # Use 'in' operator for multiple documents
            metadata_filters = MetadataFilters(
                filters=[
                    MetadataFilter(key="file_name", value=active_documents, operator=FilterOperator.IN)
                ]
            )
            retriever_kwargs["filters"] = metadata_filters

        try:
            retriever = self.index.as_retriever(**retriever_kwargs)
            source_nodes = retriever.retrieve(query_text)
        except Exception as e:
            print(f"Error during retrieval with filters: {e}")
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
                content=f"Context:\n{context_str}\n\nQuestion: {query_text}\n\nIMPORTANT: If this question requires a visual, you MUST reply with a pure JSON object using the `mafs_data` or `react_flow_data` schema defined in your system prompt. Do NOT write Python code."
            ),
        ]

        try:
            print("Sending to LLM Chat API...")
            response = self.llm.chat(messages)
            raw_content = str(response.message.content).strip() if response and hasattr(response, 'message') and response.message.content else ""
            
            # Attempt to parse json if it looks like json
            response_text = raw_content
            flow_data = None
            mafs_data = None
            
            import json
            import re
            
            # Helper to safely try parsing JSON
            def try_parse_json(text):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return None

            json_str = raw_content
            parsed = None
            
            # 1. Try to extract an explicit JSON block if the model wrapped it
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', raw_content, re.DOTALL)
            if json_match:
                parsed = try_parse_json(json_match.group(1))
            
            # 2. If no code block, check if the ENTIRE response is just a JSON object
            if not parsed and raw_content.strip().startswith('{') and raw_content.strip().endswith('}'):
                parsed = try_parse_json(raw_content)

            # If we successfully parsed a JSON object that matches our schema, use it.
            # Otherwise, leave response_text as the FULL raw_content.
            recognized_keys = ["text_explanation", "react_flow_data", "mafs_data", "response", "text", "answer"]
            if parsed and isinstance(parsed, dict):
                has_recognized_key = any(k in parsed for k in recognized_keys)
                if has_recognized_key:
                    # Priority for our specific keys
                    if "text_explanation" in parsed: response_text = parsed["text_explanation"]
                    elif "response" in parsed: response_text = parsed["response"]
                    elif "text" in parsed: response_text = parsed["text"]
                    elif "answer" in parsed: response_text = parsed["answer"]
                    
                    if "react_flow_data" in parsed:
                        flow_data = parsed["react_flow_data"]
                    if "mafs_data" in parsed:
                        mafs_data = parsed["mafs_data"]
                
        except Exception as e:
            print(f"Exception during LLM chat: {e}")
            response_text = ""
            flow_data = None
            mafs_data = None
            
        # Fallback: if still empty, try complete() with a shorter prompt
        if not response_text.strip():
            print("Chat response empty, trying complete() fallback...")
            short_context = context_str[:500]
            fallback_prompt = f"Based on this: {short_context}\n\nAnswer briefly: {query_text}\n\nIMPORTANT: If this question requires a visual, you MUST reply with a pure JSON object using the `mafs_data` or `react_flow_data` schema defined in your system prompt. Do NOT write Python code."
            try:
                fallback_resp = self.llm.complete(fallback_prompt)
                fallback_text = str(fallback_resp).strip() if fallback_resp else ""
                
                if not fallback_text:
                    response_text = "I received your question but the model didn't generate a response (it returned an empty response). Please try rephrasing."
                else:
                    response_text = fallback_text
                    
                    # Apply the same JSON extraction logic
                    fallback_parsed = None
                    fb_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', fallback_text, re.DOTALL)
                    if fb_match:
                        fallback_parsed = try_parse_json(fb_match.group(1))
                    
                    if not fallback_parsed and fallback_text.strip().startswith('{') and fallback_text.strip().endswith('}'):
                        fallback_parsed = try_parse_json(fallback_text)

                    if fallback_parsed and isinstance(fallback_parsed, dict):
                        recognized_keys = ["text_explanation", "react_flow_data", "mafs_data", "response", "text", "answer"]
                        if any(k in fallback_parsed for k in recognized_keys):
                            if "text_explanation" in fallback_parsed: response_text = fallback_parsed["text_explanation"]
                            elif "response" in fallback_parsed: response_text = fallback_parsed["response"]
                            elif "text" in fallback_parsed: response_text = fallback_parsed["text"]
                            elif "answer" in fallback_parsed: response_text = fallback_parsed["answer"]

                            if "react_flow_data" in fallback_parsed:
                                flow_data = fallback_parsed["react_flow_data"]
                            if "mafs_data" in fallback_parsed:
                                mafs_data = fallback_parsed["mafs_data"]
                            
            except Exception as e:
                print(f"Exception during LLM complete: {e}")
                response_text = f"I received your question, but encountered an error connecting to the AI: {e}"

        return {
            "response": response_text,
            "flow_data": flow_data,
            "mafs_data": mafs_data,
            "sources": sources
        }

# Singleton instance
rag_engine = None

def get_rag_engine():
    global rag_engine
    if rag_engine is None:
        rag_engine = RAGEngine()
    return rag_engine
