from dotenv import load_dotenv
load_dotenv(dotenv_path="/Users/charleneannecordero/glow-app/.env")
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from orchestrator import handle_message
from memory import save_memory, save_to_cosmos

app = FastAPI()

# 🔐 Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    user_id: str


@app.get("/")
def root():
    return {"message": "GLOW API is running 🚀"}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        response, intent = handle_message(req.message, req.user_id)
        
        # Save to memory
        try:
            save_memory(req.user_id, req.message, intent)
        except Exception as e:
            print(f"Memory save warning: {e}")

        # Auto-sync chat to Cosmos DB
        try:
            save_to_cosmos(req.message, response, intent, req.user_id)
        except Exception as e:
            print(f"Cosmos sync warning: {e}")

        return {
            "response": response,
            "intent": intent
        }
    except Exception as e:
        print(f"Chat error: {e}")
        return {
            "response": "An error occurred. Please try again.",
            "intent": "error"
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
