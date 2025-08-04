from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, auth
from database import SessionLocal, engine
from perplexity_client import perplexity_client, is_prompt_allowed
import os
from dotenv import load_dotenv

load_dotenv()

# Create database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Company AI Chatbot API", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {
        "access_token": access_token, 
        "token_type": "bearer", 
        "user": {
            "id": user.id,
            "username": user.username,
            "name": user.name,
            "role": user.role,
            "departments": user.departments
        }
    }

@app.post("/chat")
async def chat_with_ai(
    message: dict,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    department = message.get("department")
    user_message = message.get("content")
    
    # Validate user access to department
    if "all" not in current_user.departments and department not in current_user.departments:
        raise HTTPException(
        status_code=403,
        detail="Access denied to this department"
    )

    
    # Get department info for blocked keywords
    dept = db.query(models.Department).filter(
        models.Department.key == department
    ).first()
    
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if prompt is allowed
    if not is_prompt_allowed(user_message, dept.blocked_keywords or []):
        raise HTTPException(
            status_code=400, 
            detail="This type of question is not allowed. Please ask about company-related topics only."
        )
    
    # Generate AI response using Perplexity
    try:
        result = await perplexity_client.generate_response(
            user_message, 
            department, 
            current_user.id,
            db
        )
        return result
    except Exception as e:
        print(f"Error generating response: {e}")
        raise HTTPException(
            status_code=500, 
            detail="Error generating AI response"
        )

@app.get("/departments")
async def get_departments(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role == "admin":
        return db.query(models.Department).all()
    else:
        return db.query(models.Department).filter(
            models.Department.key.in_(current_user.departments)
        ).all()

@app.get("/conversations")
async def get_conversations(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    conversations = db.query(models.Conversation).filter(
        models.Conversation.user_id == current_user.id
    ).order_by(models.Conversation.created_at.desc()).all()
    
    return [
        {
            "id": conv.id,
            "department": conv.department,
            "user_message": conv.user_message,
            "ai_response": conv.ai_response,
            "citations": conv.citations,
            "created_at": conv.created_at.isoformat()
        }
        for conv in conversations
    ]

@app.delete("/conversations/{conv_id}")
async def delete_conversation(
    conv_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conv_id,
        models.Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return {"detail": "Conversation deleted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
