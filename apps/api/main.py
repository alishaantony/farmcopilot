from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title ="FarmCopilot API")

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





