from fastapi import FastAPI, Header, HTTPException, Request, WebSocket, WebSocketDisconnect, Form
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
            html_snippet = f"<p class=\"message\" id=\"messages\" hx-swap-oob=\"beforeend\"><strong>{user.username}:</strong> {message}</p>"
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
    
    # Collect all conversations from all topics
    conversations = []
    for topic in topics:
        conversations.extend(topic.conversations)

    messages = db.get_messages(conversations[0].id, limit=10, offset=0) if conversations else []

    data = {
        "request": request,
        "username": user.username,
        "topics": topics,
        "tabs": conversations,
        "conversation_id": conversations[0].id if conversations else None,
        "messages": messages,
        "user": user,
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
        "user": user,
    }
    return templates.TemplateResponse("conversation.html", data)

@app.api_route("/topics", methods=["GET", "POST"], response_class=HTMLResponse)
async def topics(request: Request, x_user: int = Header(default=1), topic_name: str = Form(default=None)):
    if x_user is None:
        raise HTTPException(status_code=400, detail="Missing x_user header")

    user = db.get_user(x_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.method == "POST":
        if not topic_name:
            raise HTTPException(status_code=400, detail="Topic name is required")
        topic = db.create_topic(topic_name, description=None)
        db.subscribe_to_topic(topic.id, user.id)

    topics = db.get_subscribed_topics(user.id)
    # No need to enhance topics with conversations anymore since they're included
    
    data = {
        "request": request,
        "topics": topics,
        "user": user,
    }
    return templates.TemplateResponse("topics.html", data)

@app.get("/topics/{topic_id}/conversations", response_class=HTMLResponse)
async def get_conversations_for_topic(request: Request, topic_id: int, x_user: int = Header(default=1)):
    if x_user is None:
        raise HTTPException(status_code=400, detail="Missing x_user header")

    user = db.get_user(x_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    topic = db.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")

    conversations = db.get_conversations_by_topic(topic_id)
    data = {
        "request": request,
        "conversations": conversations,
        "user": user,
        "topic": topic,
    }
    return templates.TemplateResponse("conversations.html", data)

@app.api_route("/create_conversation/topic/{topic_id}", methods=["GET", "POST"], response_class=HTMLResponse)
async def create_conversation(
    request: Request, 
    topic_id: int,
    x_user: int = Header(default=1), 
    conversation_name: str = Form(None),
    first_message: str = Form(None)
):
    if x_user is None:
        raise HTTPException(status_code=400, detail="Missing x_user header")

    user = db.get_user(x_user)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if request.method == "POST":
        if not topic_id or not conversation_name or not first_message:
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        # Create the conversation
        conversation = db.create_conversation(topic_id, conversation_name)
        
        # Add the first message
        db.add_message(conversation.id, user.id, first_message)
        
        # Get messages to display in the conversation view
        messages = db.get_messages(conversation.id, limit=10, offset=0)
        
        # Return the conversation template
        data = {
            "request": request,
            "conversation_id": conversation.id,
            "messages": messages,
        }
        return templates.TemplateResponse("conversation.html", data)
    
    # For GET requests, return the create conversation form
    if not topic_id:
        raise HTTPException(status_code=400, detail="Topic ID is required")
    topic = db.get_topic(topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
        
    data = {
        "request": request,
        "topic": topic,
        "user": user,
    }
    return templates.TemplateResponse("create_conversation.html", data)
