from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
from io import BytesIO
from sentence_transformers import SentenceTransformer 
import faiss
import numpy as np
import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = FastAPI(title ="FarmCopilot API")

embedding_model = SentenceTransformer('all-MiniLM-L6-V2')

# Initialize the OpenAI client for OpenRouter
client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=os.getenv("OPENROUTER_API_KEY"),
)

index= None
text_chunks = []

if os.path.exists("faiss_index.index"):
    index = faiss.read_index("faiss_index.index")
    with open("chunks.json","r") as f:
        text_chunks = json.load(f)

# Allow local Next.js (localhost:3000) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    
    
class ChatResponse(BaseModel):
    response: str

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    global index, text_chunks
    if index is None:
        
        return {"response":"The file has not yet been uploaded"}
    question_embedding = embedding_model.encode([request.message])
    distances, indices = index.search(question_embedding, k=3) 
    
    retrieved_chunks = [text_chunks[i] for i in indices[0]]
                        
    response = "\n\n---\n\n".join(retrieved_chunks)
    
    completion = client.chat.completions.create(
      model="meta-llama/llama-3-8b-instruct", # A powerful free model on OpenRouter
      messages=[
        {
          "role": "system",
          "content": "You are an expert assistant. Answer the user's question based ONLY on the following context. If the answer is not in the context, say you don't know.",
        },
        {
          "role": "user",
          "content": f"Context: {response}\n\nQuestion: {request.message}",
        },
      ],
    )
    
    final_response = completion.choices[0].message.content
    return {"response": final_response}
    
def chunk_text(text: str,chunk_size: int = 100, overlap: int =50)->list[str]:
    chunks = []
    i=0
    text_lenght = len(text)
    step = chunk_size - overlap
    
    while(i<text_lenght):
        chunk = text[i: i+chunk_size].strip()
        chunks.append(chunk)
        i+= step
    return chunks


def create_embeddings(chunks: list[str])->list [list[float]]:
    
    embeddings = embedding_model.encode(chunks)
    return embeddings.tolist()



@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global index, text_chunks
    
    file_content = await file.read()
    reader= PdfReader(BytesIO(file_content))
    
    full_text = ""
    for page in reader.pages:
        full_text+= page.extract_text()+ "\n"
    
    text_chunks = chunk_text(full_text)
    text_embedded = create_embeddings(text_chunks)
    
    if text_embedded:
        
        embedding_dim = len(text_embedded[0]) if text_embedded else 0
        embedding_array = np.array(text_embedded, dtype=np.float32)
        index = faiss.IndexFlatL2(embedding_dim)
        index.add(embedding_array)
        
    faiss.write_index(index, "faiss_index.index")
    
    with open("chunks.json","w") as f:
        
        json.dump(text_chunks, f)
    
    
    
    return{"Filename": file.filename, 
           "Content Type":file.content_type,
           "Total Pages": len(reader.pages),
           "chunk_count ": len(text_chunks),
           "first_chunk_preview": text_chunks[0] if text_chunks else "No text found",
           "embedding count": len(text_embedded),
           "first_embedding_preview": text_embedded[0] if text_embedded else "No embedding found",
           "Embedding dimension": len(text_embedded[0]) if text_embedded else 0,
           "message": "File processed and embeddings created successfully, with a serchable index with {index.ntotal} vectors."
           }
    







