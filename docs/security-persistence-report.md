# Security & Persistence Report

## Database schema

Three tables (SQLAlchemy models in `app/models.py`):

- `users`
  - `id` (PK)
  - `email` (unique, indexed)
  - `hashed_password` (bcrypt hash; raw password is never stored)
  - `created_at`
- `conversations`
  - `id` (PK)
  - `user_id` (FK -> users.id, indexed)
  - `title`
  - `created_at`
- `messages`
  - `id` (PK)
  - `conversation_id` (FK -> conversations.id, indexed)
  - `role` (`user` or `assistant`)
  - `content`
  - `created_at`

Relationships use cascade delete so removing a user removes their conversations and messages.

## Auth flow

1. `POST /register` creates a user with a bcrypt password hash.
2. `POST /login` (or `/token`) verifies credentials and returns a JWT access token
   (`Authorization: Bearer <token>`).
3. `get_current_user` dependency decodes the JWT, looks up the user, and is applied to
   all conversation endpoints.

## Ownership rule

Every conversation query is filtered by `user_id == current_user.id`. A conversation
that does not belong to the current user is treated as not found (HTTP 404), so
existence is not leaked and no read or modification is possible.

## Cache vs database

The in-memory cache (`app/cache.py`) stores repeated, non-sensitive AI results with a
short TTL. It is temporary and process-local: it is lost on restart and may be
evicted at any time. The SQLite database is the permanent source of truth for users,
conversations, and messages.

## Test proving private data protection

`tests/test_app.py::test_private_data_protection`:

1. Registers User A and User B.
2. User B creates a conversation.
3. User A's GET and POST (add message) to that conversation return 404.
4. User B can read and append messages; both user and assistant messages persist.
5. User A's conversation list does not contain User B's conversation.
