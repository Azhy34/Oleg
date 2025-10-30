import { useAppStore } from './store';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// --- API Types ---
interface SessionResponse {
  session_id: string;
}

interface StatusResponse {
  status: 'new' | 'embedding_completed' | 'queued' | 'processing' | 'completed' | 'failed';
  result_s3_path?: string;
  s3_embedding_path?: string;
  error?: string;
}

// --- API Functions ---

/**
 * Creates a new session on the backend by uploading an image.
 * @param imageFile The image file to upload.
 * @returns The session data containing the new session_id.
 */
export const createSession = async (imageFile: File): Promise<SessionResponse> => {
  const formData = new FormData();
  formData.append('file', imageFile);

  const response = await fetch(`${API_BASE_URL}/v1/sessions/create`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to create session.' }));
    throw new Error(errorData.detail || 'Server error');
  }

  return response.json();
};

/**
 * Triggers the embedding generation process on the backend.
 * @param sessionId The ID of the current session.
 */
export const generateEmbedding = async (sessionId: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/v1/sessions/${sessionId}/embed`, {
    method: 'POST',
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to start embedding generation.' }));
    throw new Error(errorData.detail || 'Server error');
  }
};

/**
 * Starts the wallpaper generation process.
 * @param sessionId The ID of the current session.
 * @param mask The base64 encoded mask.
 * @param wallpaperUrl The URL of the wallpaper pattern.
 */
export const generateWallpaper = async (sessionId: string, mask: string, wallpaperUrl: string): Promise<void> => {
  const response = await fetch(`${API_BASE_URL}/v1/sessions/${sessionId}/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mask, wallpaper_url: wallpaperUrl }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to start generation.' }));
    throw new Error(errorData.detail || 'Server error');
  }
};

/**
 * Polls the backend for the status of a generation session.
 * @param sessionId The ID of the session to poll.
 */
export const pollStatus = async (sessionId: string): Promise<StatusResponse> => {
  const response = await fetch(`${API_BASE_URL}/v1/sessions/${sessionId}/status`);
  if (!response.ok) {
    throw new Error('Failed to fetch session status.');
  }
  return response.json();
};
