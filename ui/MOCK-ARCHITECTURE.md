# Mock-Only UI Architecture

This build of **Job Market Agent** runs entirely on local, deterministic data. All network calls and backend dependencies have been removed so designers and stakeholders can explore the experience without standing up any services.

## Authentication
- Credentials are stored in-memory with optional persistence per session.
- Any new email/password combination registers automatically and signs in with mock JWT-style tokens.
- Refresh, logout, and user profile endpoints all use the same local store.

## Jobs & Materials
- The workspace seeds two representative job applications on first load.
- Creating, updating, and deleting jobs or materials updates the shared local store instantly.
- File uploads simulate progress, store metadata, and remain available for later sessions.

## Conversations & Documents
- Chat answers return curated example responses that mirror the production tone and structure.
- Document exports and downloads generate markdown locally with shareable placeholders.
- LLM response history returns a consistent timeline for demos.

## Learning & Settings
- Learn pages, bookmarks, and progress tracking rely on the existing mock content library.
- User preferences are saved to `localStorage`, mimicking realistic settings flows without a server.

## Why This Matters
- Designers can test navigation flows, empty states, and content without worrying about API availability.
- Product demos are deterministic—no rate limits, latency, or flaky credentials.
- Engineers retain the same service interfaces, making it easy to reintroduce real endpoints later.
