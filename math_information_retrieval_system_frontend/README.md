# math_information_retrieval_system_frontend


# MIR System - Frontend

This is the **frontend** of the Mathematical Information Retrieval (MIR) system.  
It provides a user interface for entering mathematical queries (LaTeX/MathML) and displaying retrieval results from the backend.  

The frontend is **platform-aware** and uses different approaches to render HTML content depending on whether it is running on **web** or **mobile (Android/iOS)**.

---

## Features

- Input math expressions in LaTeX/MathML format.
- Send queries to the backend API.
- Display retrieved results file names.
- View the particular file content. 
- Responsive and interactive UI for web and mobile.
- Platform-specific HTML viewers:
  - **Web:** Uses `HtmlElementView` and modern web APIs with an `<iframe>` for enhanced MathML support.
  - **Mobile (Android/iOS):** Uses `WebView` or `flutter_html` package for rendering HTML content with MathJax support.

---

## Platform-Specific HTML Viewer Details

### 1. **Web Viewer (`web_html_viewer.dart`)**
- Uses **iframe** via `HtmlElementView`.
- Enhances HTML content by injecting **MathJax** for better MathML rendering.
- Registers a unique `viewId` for each file to render independently.
- Handles loading states and errors with retry option.
- Modern web API usage ensures fast and safe HTML rendering.

**Flow:**
1. Fetch HTML content from backend using HTTP GET request.
2. Inject MathJax script and styling for proper math rendering.
3. Create an iframe element and register it via `platformViewRegistry`.
4. Display HTML content in the `HtmlElementView`.

---

### 2. **Mobile Viewer (`mobile_html_viewer.dart`)**
- Uses **WebView** for Android/iOS.
- Injects **MathJax script** into the HTML content to render math properly.
- Includes fallback using `flutter_html` for web compatibility if running in a browser.
- Handles loading states, errors, and provides retry options.
- Initializes `WebViewController` with unrestricted JavaScript for dynamic content.

**Flow:**
1. Fetch HTML content from backend via HTTP GET request.
2. Inject MathJax scripts for rendering LaTeX/MathML.
3. Load HTML into WebView or use `Html` widget if running on web.
4. Handle loading and error states gracefully with UI feedback.

---

## Tech Stack

- **Framework:** Flutter (supports Web, Android, iOS)
- **HTML Rendering:** `HtmlElementView` (Web), `WebView`/`flutter_html` (Mobile)
- **API Calls:** HTTP requests to FastAPI backend
- **Math Rendering:** MathJax (injected into HTML)

---

## Setup

1. **Clone the repository**:

```bash
git clone https://github.com/yourusername/mir-system.git
cd mir-system/frontend
Install dependencies (for Flutter Web/Mobile):


flutter pub get
Run locally:

flutter run -d chrome       # Web
flutter run -d android      # Android
flutter run -d ios          # iOS
Connect to backend API:

Ensure the frontend API endpoint points to your backend URL, e.g.:

const API_URL = "http://127.0.0.1:8000";
Usage
Open the frontend in the browser or mobile emulator.

Enter a mathematical expression in LaTeX/MathML.

Click Search to retrieve results.

Displays the result's document name , Enter the particular document then you will see the rendered webpage.

Loading and error states are handled with feedback and retry buttons.

Folder Structure
frontend/
├── lib/
│   ├── web_html_viewer.dart      # Web-specific HTML viewer
│   ├── mobile_html_viewer.dart   # Mobile-specific HTML viewer
│   ├── main.dart                 # App entry point
├── pubspec.yaml
└── assets/
Contributing
Fork the repo, create a branch, make changes, and submit a pull request.

Ensure API endpoints match the backend configuration.

Platform-specific rendering must maintain MathJax support for accurate math display.

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.
