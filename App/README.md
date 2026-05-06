## SafeNest AI — Flutter App

Flutter mobile client for the **SafeNest AI – Child Cyber Safety Platform**, integrating with the existing FastAPI backend in this workspace.

### Backend endpoints used (exact)

- **POST** `/analyze-chat`
- **GET** `/get-risk-report/{analysis_id}`
- **GET** `/agent-status`
- **GET** `/logs?analysis_id=&limit=`
- **Auth (used by Login/Register)**:
  - **POST** `/auth/register`
  - **POST** `/auth/login`
  - **GET** `/auth/me`

### Run instructions

1) Start the backend (from repo root):

```powershell
cd backend
.\scripts\run_api_dev.ps1
```

2) Run Flutter app:

```powershell
cd ..\App
flutter pub get
flutter run
```

### Windows note (plugins + symlinks)

If you see `Building with plugins requires symlink support`, enable **Developer Mode** in Windows:

```powershell
start ms-settings:developers
```

### API base URL (important on Android emulator)

The app defaults to:
- Android emulator: `http://10.0.2.2:8000`
- iOS simulator / desktop: `http://127.0.0.1:8000`

You can change this in **Settings** inside the app.

### App navigation

- **Splash**: checks saved token → calls `/auth/me` to route to Parent/Admin; otherwise goes to Login.
- **Login/Register**: uses backend `/auth/*`.
- **Continue as Child (no login)**: opens the Child dashboard and calls `/analyze-chat` without auth (backend supports optional auth for this endpoint).
- **Parent dashboard**: risk overview, alerts, trend chart (from recent analysis history), logs viewer.
- **Admin dashboard**: agent health table via `/agent-status`, logs viewer via `/logs`.

# safenest_ai_app

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
