"""
Single source of truth for collection names.
Never hardcode collection names elsewhere — import from here.
"""
USERS = "users"
DOCUMENTS = "documents"
CHUNKS = "chunks"
CONVERSATIONS = "conversations"
MESSAGES = "messages"
SEARCH_LOGS = "search_logs"

ALL_COLLECTIONS = [
    USERS,
    DOCUMENTS,
    CHUNKS,
    CONVERSATIONS,
    MESSAGES,
    SEARCH_LOGS,
]
