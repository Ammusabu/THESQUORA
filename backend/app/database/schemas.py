"""
MongoDB JSON Schema validators ($jsonSchema).

Why use server-side validation?
- Guarantees data shape even if a rogue script inserts directly.
- Documents that violate the schema are rejected by MongoDB itself.
- Complements Pydantic (which validates *incoming requests* only).

We use a moderate `validationLevel="strict"` so inserts AND updates are checked.
"""
from typing import Any


USER_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["name", "email", "password_hash", "role", "created_at"],
        "additionalProperties": False,
        "properties": {
            "_id": {"bsonType": "objectId"},
            "name": {"bsonType": "string", "minLength": 1, "maxLength": 120},
            "email": {
                "bsonType": "string",
                "pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            },
            "password_hash": {"bsonType": "string", "minLength": 20},
            "role": {"enum": ["admin", "user"]},
            "department": {"bsonType": ["string", "null"]},
            "created_at": {"bsonType": "date"},
        },
    }
}


DOCUMENT_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": [
            "title",
            "filename",
            "file_type",
            "storage_key",
            "owner_id",
            "upload_date",
            "processing_status",
        ],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "title": {"bsonType": "string", "minLength": 1, "maxLength": 300},
            "filename": {"bsonType": "string"},
            "file_type": {"enum": ["pdf", "docx", "txt"]},
            "storage_key": {"bsonType": "string"},
            "file_hash": {"bsonType": "string"},  # sha256 for dedupe
            "owner_id": {"bsonType": "objectId"},
            "department": {"bsonType": ["string", "null"]},
            "category": {
                "bsonType": ["string", "null"],
                "enum": [
                    "HR", "Technical", "Finance", "Research",
                    "Business", "Legal", "General", None,
                ],
            },
            "classification_confidence": {
                "bsonType": ["double", "null"],
                "minimum": 0,
                "maximum": 1,
            },
            "upload_date": {"bsonType": "date"},
            "processing_status": {
                "enum": ["pending", "processing", "processed", "failed"],
            },
            "total_chunks": {"bsonType": "int", "minimum": 0},
            "file_size": {"bsonType": "int", "minimum": 0},
            "summary": {"bsonType": ["string", "null"]},
            "error": {"bsonType": ["string", "null"]},
            "cluster_id": {"bsonType": ["int", "null"]},
        },
    }
}


CHUNK_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["document_id", "chunk_index", "text", "created_at"],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "document_id": {"bsonType": "objectId"},
            "chunk_index": {"bsonType": "int", "minimum": 0},
            "text": {"bsonType": "string", "minLength": 1},
            "page_number": {"bsonType": ["int", "null"]},
            "category": {"bsonType": ["string", "null"]},
            "department": {"bsonType": ["string", "null"]},
            "owner_id": {"bsonType": ["objectId", "null"]},  # denormalised for permission filters
            "embedding": {
                "bsonType": ["array", "null"],
                "items": {"bsonType": "double"},
            },
            "metadata": {"bsonType": ["object", "null"]},
            "created_at": {"bsonType": "date"},
        },
    }
}


CONVERSATION_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["user_id", "title", "created_at", "updated_at"],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "user_id": {"bsonType": "objectId"},
            "title": {"bsonType": "string", "minLength": 1, "maxLength": 200},
            "created_at": {"bsonType": "date"},
            "updated_at": {"bsonType": "date"},
        },
    }
}


MESSAGE_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["conversation_id", "user_id", "role", "content", "created_at"],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "conversation_id": {"bsonType": "objectId"},
            "user_id": {"bsonType": "objectId"},
            "role": {"enum": ["user", "assistant", "system"]},
            "content": {"bsonType": "string"},
            "source_references": {
                "bsonType": "array",
                "items": {
                    "bsonType": "object",
                    "required": ["document_id", "title"],
                    "properties": {
                        "document_id": {"bsonType": "objectId"},
                        "title": {"bsonType": "string"},
                        "page_number": {"bsonType": ["int", "null"]},
                        "chunk_index": {"bsonType": ["int", "null"]},
                        "snippet": {"bsonType": ["string", "null"]},
                    },
                },
            },
            "created_at": {"bsonType": "date"},
            "feedback": {
                "bsonType": ["string", "null"],
                "enum": ["up", "down", None],
            },
        },
    }
}


SEARCH_LOG_SCHEMA: dict[str, Any] = {
    "$jsonSchema": {
        "bsonType": "object",
        "required": ["user_id", "query", "created_at"],
        "properties": {
            "_id": {"bsonType": "objectId"},
            "user_id": {"bsonType": "objectId"},
            "query": {"bsonType": "string"},
            "mode": {"enum": ["vector", "keyword", "hybrid"]},
            "retrieved_document_ids": {
                "bsonType": "array",
                "items": {"bsonType": "objectId"},
            },
            "result_count": {"bsonType": "int", "minimum": 0},
            "latency_ms": {"bsonType": ["int", "null"], "minimum": 0},
            "created_at": {"bsonType": "date"},
        },
    }
}
