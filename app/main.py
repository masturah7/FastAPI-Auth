from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from . import auth, cache, models, schemas
from .database import get_db, init_db

app = FastAPI(title="Auth & Cache for AI Apps")


@app.on_event("startup")
def on_startup():
    init_db()


def _register_user(email: str, password: str, db: Session):
    if auth.get_user_by_email(db, email):
        raise HTTPException(status_code=400, detail="Email already registered")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    user = models.User(email=email, hashed_password=auth.hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _owned_conversation(conv_id: int, current_user, db: Session):
    conv = (
        db.query(models.Conversation)
        .filter(models.Conversation.id == conv_id, models.Conversation.user_id == current_user.id)
        .first()
    )
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


# ---------- Auth ----------

@app.post("/register", response_model=schemas.UserRead, tags=["auth"])
@app.post("/auth/register", response_model=schemas.UserRead, tags=["auth"])
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    return _register_user(payload.email, payload.password, db)


@app.post("/login", response_model=schemas.Token, tags=["auth"])
@app.post("/auth/login", response_model=schemas.Token, tags=["auth"])
def login_json(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/token", response_model=schemas.Token, tags=["auth"])
@app.post("/auth/token", response_model=schemas.Token, tags=["auth"])
def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    token = auth.create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me", response_model=schemas.UserRead, tags=["auth"])
@app.get("/auth/me", response_model=schemas.UserRead, tags=["auth"])
def me(current_user=Depends(auth.get_current_user)):
    return current_user


# ---------- Conversations ----------

@app.post("/conversations", response_model=schemas.ConversationRead, tags=["conversations"])
@app.post("/chats", response_model=schemas.ConversationRead, tags=["conversations"])
def create_conversation(
    payload: schemas.ConversationCreate,
    current_user=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    conv = models.Conversation(user_id=current_user.id, title=payload.title)
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@app.get("/conversations", response_model=List[schemas.ConversationRead], tags=["conversations"])
@app.get("/chats", response_model=List[schemas.ConversationRead], tags=["conversations"])
def list_conversations(
    current_user=Depends(auth.get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == current_user.id)
        .all()
    )


@app.get("/conversations/{conversation_id}", response_model=schemas.ConversationRead, tags=["conversations"])
@app.get("/chats/{conversation_id}", response_model=schemas.ConversationRead, tags=["conversations"])
def get_conversation(
    conversation_id: int,
    current_user=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    return _owned_conversation(conversation_id, current_user, db)


@app.post(
    "/conversations/{conversation_id}/messages",
    response_model=schemas.MessageExchange,
    tags=["conversations"],
)
@app.post(
    "/conversations/{conversation_id}/message",
    response_model=schemas.MessageExchange,
    tags=["conversations"],
)
@app.post(
    "/chats/{conversation_id}/messages",
    response_model=schemas.MessageExchange,
    tags=["conversations"],
)
def add_message(
    conversation_id: int,
    payload: schemas.MessageCreate,
    current_user=Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    conv = _owned_conversation(conversation_id, current_user, db)

    user_msg = models.Message(conversation_id=conv.id, role="user", content=payload.content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)

    assistant_content, cached = cache.ai_generate(payload.content)
    assistant_msg = models.Message(
        conversation_id=conv.id, role="assistant", content=assistant_content
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {
        "user_message": user_msg,
        "assistant_message": assistant_msg,
        "cached": cached,
    }


# ---------- Cache demo ----------

@app.get("/cache/demo", tags=["cache"])
def cache_demo(q: str = "hello"):
    result, cached = cache.ai_generate(q)
    return {"result": result, "cached": cached}
