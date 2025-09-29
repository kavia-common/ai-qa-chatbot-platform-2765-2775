Weather Q&A Backend API

Summary
- Django REST backend for a weather Q&A chatbot using LangChain + OpenAI with a simulated MCP weather tool (no live data).
- Provides session-based auth, question submission, and conversation history.

Environment
- OPENAI_API_KEY: Optional. If not set, responses are generated without LLM but still include simulated forecast info.
- OPENAI_MODEL: Optional. Default "gpt-4o-mini".

Auth
- POST /api/auth/register/ {"username","password","email?"}
- POST /api/auth/login/ {"username","password"}
- POST /api/auth/logout/

Chat
- POST /api/chat/ask/ {"question": "What is the weather in Paris tomorrow?", "conversation_id"?: 1}
  - Returns {"conversation_id", "question", "answer"}
  - Creates a new conversation if conversation_id is not provided.
- GET /api/chat/conversations/
- GET /api/chat/conversations/{conversation_id}/

Notes
- CORS is open and credentials allowed. Use fetch with credentials: 'include' for session cookies from the frontend.
- The MCP tool is simulated; it returns deterministic pseudo forecasts based on question text.
