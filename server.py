from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from db import DatabaseAccess
import logging

app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the database with seed data
db = DatabaseAccess(db_path="chat.db", seed_data=True)

# Configure logging
logging.basicConfig(level=logging.INFO)

# In-memory store for active WebSocket connections
active_connections = {}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, x_user: int = Header(default=1)):
    logging.info(f"Received WebSocket connection request with x_user: {x_user}")
    if x_user is None:
        await websocket.close(code=4001)
        logging.error("Missing x_user header")
        return

    user = db.get_user(x_user)
    if not user:
        await websocket.close(code=4004)
        logging.error(f"User {x_user} not found")
        return

    # Add the connection to the in-memory store
    active_connections[x_user] = websocket
    logging.info(f"User {x_user} connected via WebSocket.")
    try:
        await websocket.accept()
        while True:
            data = await websocket.receive_json()
            logging.info(f"Received message from user {x_user}: {data}")
            message = data.get("message")
            logging.info(f"Author: {user}, Message: {message}")

            if not user or not message:
                await websocket.send_text("Invalid message format.")
                continue

            # Save the message to the database
            db.add_message(data.get("conversation_id"), user.id, message)

            # Broadcast the message as an HTML snippet
            # This snipped will be inserted as the last child of the 'messages' element.
            # Careful if the user changes conversations!
            html_snippet = f"<p id=\"messages\" hx-swap-oob=\"beforeend\"><strong>{user.username}:</strong> {message}</p>"
            for user_id, connection in active_connections.items():
                # DO send the message back to the sender
                await connection.send_text(html_snippet)
    except WebSocketDisconnect:
        logging.info(f"User {x_user} disconnected.")
    finally:
        # Remove the connection from the in-memory store
        active_connections.pop(x_user, None)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request, x_user: int = Header(default=1)):
    if x_user is None:
        raise HTTPException(status_code=400, detail="Missing x_user header")

    user = db.get_user(x_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    topics = db.get_subscribed_topics(user.id)
    conversations = []
    for topic in topics:
        topic_conversations = db.get_conversations_by_topic(topic.id)
        conversations.extend(topic_conversations)

    messages = db.get_messages(conversations[0].id, limit=10, offset=0) if conversations else []

    data = {
        "request": request,
        "username": user.username,
        "topics": topics,
        "tabs": conversations,
        "conversation_id": conversations[0].id if conversations else None,
        "messages": messages,
    }
    return templates.TemplateResponse("index.html", data)

@app.get("/conversation/{id}", response_class=HTMLResponse)
async def get_conversation(request: Request, id: int, x_user: int = Header(default=1)):
    logging.info(f"Received request at '/conversation/{id}' with x_user: {x_user}")
    if x_user is None:
        raise HTTPException(status_code=400, detail="Missing x_user header")

    user = db.get_user(x_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    conversation = db.get_conversation(id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.get_messages(conversation.id, limit=10, offset=0)
    print("Messages: ", messages)
    data = {
        "request": request,
        "conversation_id": conversation.id,
        "messages": messages,
    }
    return templates.TemplateResponse("conversation.html", data)
