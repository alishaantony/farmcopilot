from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(title ="FarmCopilot API")

# Allow local Next.js (localhost:3000) to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class chat_request(BaseModel):
    message: str
    
    
class chat_response(BaseModel):
    response: str

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/chat", response_model=chat_response)
def chat(request: chat_request):
    
    user_message = request.message.strip().lower()
    if not user_message:
        return {"response": "No message provided."}
    else:
        return {"response":f"Echo: {user_message}"}





