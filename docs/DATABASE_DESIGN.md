# MongoDB Design

| Collection | Key indexes |
|---|---|
| users | uniq_email (unique) |
| documents | owner_recent, text_title_summary (text), uniq_owner_file_hash (unique compound) |
| chunks | doc_chunk, chunks_text (text), chunks_vector_index (Atlas Vector Search) |
| conversations | user_recent |
| messages | conv_chrono |
| search_logs | user_recent, ttl_90d (TTL) |

## Design decisions

- chunks stored separately from documents (16MB limit + independent vector search)
- denormalized owner_id/category on chunks enables vectorSearch.filter pre-filtering
- compound unique (owner_id, file_hash) = per-user dedupe
- $jsonSchema validators on every collection
