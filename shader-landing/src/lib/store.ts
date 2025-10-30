import { create } from 'zustand';

/**
 * Represents the possible states of the wallpaper generation process from the user's perspective.
 */
export type GenerationStatus = 'idle' | 'loading' | 'generating' | 'success' | 'error';

/**
 * Defines the shape of the application's global state.
 */
interface AppState {
  /** The unique identifier for the current user session. */
  sessionId: string | null;
  /** The current status of the wallpaper generation process. */
  status: GenerationStatus;
  /** The URL of the successfully generated wallpaper. */
  resultUrl: string | null;
  /** Any error message that occurred during the process. */
  error: string | null;

  // --- Actions ---
  /** Starts a new session. */
  startSession: (sessionId: string) => void;
  /** Sets the state to indicate that wallpaper generation has started. */
  startGeneration: () => void;
  /** Sets the state to reflect a successful generation. */
  setSuccess: (resultUrl: string) => void;
  /** Sets the state to reflect a failure. */
  setError: (error: string) => void;
  /** Resets the store to its initial state for a new workflow. */
  reset: () => void;
}

const initialState = {
  sessionId: null,
  status: 'idle' as GenerationStatus,
  resultUrl: null,
  error: null,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  startSession: (sessionId) => set({ sessionId, status: 'idle', error: null }),
  startGeneration: () => set({ status: 'generating', error: null }),
  setSuccess: (resultUrl) => set({ status: 'success', resultUrl }),
  setError: (error) => set({ status: 'error', error }),
  reset: () => set(initialState),
}));
