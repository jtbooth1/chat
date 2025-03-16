# Chat

Chat is a mild reimagining of a chat interface. The key objects are:
- Conversations: ordered collections of Messages. They also have Participants (Users) and Topics
- Pages: Markdown documents related to a Topic. Can be written manually or produced as a summary of a Conversation (by AI? :eyebrows:)
- Topics: Collections of Conversations and Pages
- Messages: Text, with an Author
- Users: Users can Participate in Conversations and Subscribe to Topics. 

# Architecture

The database is SQLite. The API is fastapi, with websockets. The frontend is htmx, including the htmx websocket extension. The websocket
is used only to communicate messages in your focused conversation, plus the set of topics that include activity. Otherwise, clicking on
another topic or conversation will replace the active window.

Python functions use type hints where possible. The database is accessed only through the database access class.

Frontend styling is handled with a single global css file, plus inline styles where necessary. Because the frontend will be updated
by partial replacement using HTMX, the major parts of the frontend should be templated and imported into the index.

# Frontend Layout

There's a header bar with a title, your username, and settings.

Below the header bar is the topics column, left aligned. It has a list of topics with metadata on each, tbd. The main body of the screen
has tabs to select between your open coversations & pages. Then, below that, the conversation (messages sorted by latest created_at). At
the bottom, a text entry box & "send".

The styles.css stylesheet is extremely concise. It creates a theme by combining rules that apply to many element types in a single declaration.
For example, there are only two padding rules, 8px and 4px. All elements that need padding should receive them in a single declaration. Copy this style
for any behavior that is shared by many elements, such as hovering or flex-column behavior.

Use variables to keep track of commonly used colors and spacings.

## Color

The app is grayscale with the exception of green, which is used for any button that will affect the server state. There are four shades of gray:
dark, medium, light, and gray-white, the lightest. 

# Steps

1. Database Schema DONE
2. Utility class for accessing database schema DONE
3. Unit tests for utility class DONE
4. Dummy seed data DONE
5. Basic FastAPI server for seeing pages/topics/seed conversation
  - (client trusted to say which user they are honestly, auth later)
6. Minimum viable client
7. Set up websocket and simulate a chat partner
8. Basic auth/signup stuff
9. Frontend fiddling mode
