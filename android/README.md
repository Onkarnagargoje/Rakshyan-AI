# SafeNest Android (Kotlin + Jetpack Compose)

This folder contains the **Android native** apps:

- `:parent` — Parent app (auth, children, pairing codes, alerts, push-token registration)
- `:child` — Child app (pairing/link + notification ingestion; background services will be native)
- `:shared` — Shared networking + DTOs for both apps

## Setup

1. Open `android/` in **Android Studio**.
2. Generate a Gradle wrapper (recommended): in Android Studio, open the Gradle tool window and sync once.
2. Set `ApiClient.baseUrl`:
   - Emulator: `http://10.0.2.2:8000`
   - Physical device: `http://<your-lan-ip>:8000`
3. Run backend from `backend/` (Uvicorn on `:8000`).

## Current MVP

- Parent app has a **login screen** that hits `POST /auth/login`.
- Next: add screens for children/pairing codes + alerts, then implement the child-side ingest service.

