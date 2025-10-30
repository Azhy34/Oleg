# AI Wallpaper Generator

## 1. Overview

This project is a full-stack application that allows users to generate custom wallpapers. A user can upload an image of an interior, create a mask on a specific wall using an AI-powered segmentation model (SAM), and then generate a new wallpaper on that wall based on a provided wallpaper image URL.

The application is designed with a modern, decoupled architecture, featuring a Next.js frontend and a Python backend with a Celery worker for asynchronous processing.

## 2. Tech Stack

- **Frontend:**
  - **Framework:** Next.js (React)
  - **Language:** TypeScript
  - **UI:** Tailwind CSS, Shadcn UI
  - **State Management:** Zustand
  - **AI Model:** ONNX Runtime Web with SAM (Segment Anything Model) for in-browser masking.

- **Backend:**
  - **Framework:** FastAPI
  - **Language:** Python
  - **Async Tasks:** Celery
  - **Database/Cache:** Redis (for session storage and as a Celery broker)
  - **File Storage:** AWS S3 (or compatible service like MinIO)

- **DevOps:**
  - **Containerization:** Docker (implied by dependencies, setup not included)
  - **Version Control:** Git

## 3. Architecture

The system consists of three main components:

1.  **Frontend (`shader-landing`):** A Next.js application that provides the user interface. It handles image uploads, allows users to interactively create a mask by clicking on the image, and displays the final result. The heavy lifting of mask prediction is done client-side using the ONNX SAM model.

2.  **Backend (`backend`):** A FastAPI application that serves as the main API. It manages user sessions, handles file uploads to S3, and queues generation tasks for the worker.

3.  **Worker (`backend/worker`):** A Celery worker that processes tasks asynchronously. It fetches the original image and mask, calls a diffusion model (via `diffusion_client`), and uploads the generated wallpaper back to S3.

## 4. User Flow

1.  **Upload Image:** The user visits the web application and uploads an image of an interior (e.g., a room).
2.  **Create Session:** The backend receives the image, saves it to S3, and creates a new session record in Redis, returning a unique `session_id` to the client.
3.  **Create Mask:** The user clicks on the image in the browser. The SAM model, running via ONNX Runtime, predicts the wall segment and creates a mask. The user can add positive (include) or negative (exclude) points to refine the mask.
4.  **Generate Wallpaper:** The user provides a URL to a wallpaper image and clicks "Generate". The frontend sends the `session_id`, the generated mask (as Base64), and the wallpaper URL to the backend.
5.  **Queue Task:** The backend validates the request and queues a new task for the Celery worker.
6.  **Async Processing:** The Celery worker picks up the task. It downloads the original image, the wallpaper, decodes the mask, and calls an external diffusion service to generate the final image.
7.  **Store Result:** The worker uploads the resulting image to S3 and updates the session status in Redis to "completed".
8.  **Polling and Display:** The frontend periodically polls the backend's status endpoint. Once the status is "completed", it fetches the result URL from the session data and displays the final image to the user.

## 5. Project Structure

```
.
├── backend/
│   ├── api/v1/sessions.py  # API endpoints for sessions
│   ├── core/               # Configuration, constants, security
│   ├── services/           # Business logic (session, s3, redis)
│   ├── worker/worker.py    # Celery worker for async tasks
│   └── main.py             # FastAPI application entrypoint
└── shader-landing/
    ├── src/
    │   ├── app/            # Next.js pages and layouts
    │   ├── components/     # React components (UI, editor workflow)
    │   ├── hooks/          # Custom hooks (e.g., useSam)
    │   ├── lib/            # Utilities, API client, state store
    │   └── public/         # Static assets, including the ONNX model
    └── package.json
```

## 6. Setup and Installation

*(Instructions to be added. Requires setting up environment variables for Redis, S3, etc., in a `.env` file.)*

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Azhy34/Oleg.git
    cd Oleg
    ```
2.  **Install frontend dependencies:**
    ```bash
    cd shader-landing
    npm install
    ```
3.  **Install backend dependencies:**
    ```bash
    cd ../backend
    pip install -r requirements.txt
    ```
4.  **Configure environment variables:**
    - Create a `.env` file in the `backend` directory.
    - Add necessary variables for `REDIS_URL`, `S3_BUCKET_NAME`, AWS credentials, etc.
5.  **Run the application:**
    - Start the backend FastAPI server.
    - Start the frontend Next.js development server.
    - Start the Celery worker.
