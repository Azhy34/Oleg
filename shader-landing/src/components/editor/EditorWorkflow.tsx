'use client';

import React, { useState, useMemo, useCallback, useEffect } from 'react';
import { useAppStore } from '@/lib/store';
import { useSam } from '@/hooks/useSam';
import { createSession, generateWallpaper, pollStatus } from '@/lib/api';
import { getOriginalCoords } from '@/lib/utils';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

/**
 * A centralized error handler for API calls.
 * @param err - The error object.
 * @param setError - The state setter function for errors from the app store.
 */
const handleApiError = (err: unknown, setError: (message: string) => void) => {
  const message = err instanceof Error ? err.message : 'An unknown error occurred.';
  setError(message);
};

/**
 * @component EditorWorkflow
 * @description A multi-step workflow component for uploading an image, creating a mask using the SAM model,
 * and generating a new wallpaper based on the mask and a provided wallpaper URL.
 * It manages the entire state of the process, from file selection to displaying the final result.
 */
export default function EditorWorkflow() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [wallpaperUrl, setWallpaperUrl] = useState('');

  const { sessionId, status, resultUrl, error, reset, startSession, startGeneration, setSuccess, setError } = useAppStore();

  const imageUrl = useMemo(() => {
    if (!imageFile) return null;
    return URL.createObjectURL(imageFile);
  }, [imageFile]);

  const { mask, isLoading: isSamLoading, error: samError, handleImageClick } = useSam(imageUrl);

  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      reset();
      setImageFile(file);
      try {
        const session = await createSession(file);
        startSession(session.session_id);
      } catch (err) {
        handleApiError(err, setError);
      }
    }
  }, [reset, startSession, setError]);

  /**
   * Handles the wallpaper generation request.
   */
  const handleGenerate = useCallback(async () => {
    if (!sessionId || !mask) return;
    try {
      startGeneration();
      await generateWallpaper(sessionId, mask, wallpaperUrl);
    } catch (err) {
      handleApiError(err, setError);
    }
  }, [sessionId, mask, wallpaperUrl, startGeneration, setError]);

  /**
   * Handles user clicks on the image to create positive or negative points for the mask.
   * @param e - The mouse event.
   * @param isPositive - True for a left-click (positive point), false for a right-click (negative point).
   */
  const handleImageInteraction = useCallback((e: React.MouseEvent<HTMLImageElement>, isPositive: boolean) => {
    e.preventDefault();
    const { x, y } = getOriginalCoords(e);
    handleImageClick(x, y, isPositive);
  }, [handleImageClick]);

  // Effect for polling status
  useEffect(() => {
    if (status !== 'generating' || !sessionId) return;

    const interval = setInterval(async () => {
      try {
        const data = await pollStatus(sessionId);
        if (data.status === 'completed') {
          // Assuming result_s3_path gives a full URL or can be constructed
          setSuccess(data.result_s3_path || ''); 
          clearInterval(interval);
        } else if (data.status === 'failed') {
          setError(data.error || 'Generation failed.');
          clearInterval(interval);
        }
      } catch (err) {
        handleApiError(err, setError);
        clearInterval(interval);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [status, sessionId, setSuccess, setError]);

  return (
    <div className="space-y-8 max-w-2xl mx-auto">
      <div className="p-6 border rounded-lg shadow-sm bg-card text-card-foreground">
        <h2 className="text-xl font-semibold mb-4">1. Upload Your Image</h2>
        <Input type="file" onChange={handleFileChange} className="cursor-pointer" />
      </div>

      {imageUrl && (
        <div className="p-6 border rounded-lg shadow-sm bg-card text-card-foreground">
          <h2 className="text-xl font-semibold mb-4">2. Create Mask</h2>
          <p className="text-sm text-muted-foreground mb-2">Click on the wall to create a mask. Left-click to add a positive point, right-click for a negative point.</p>
          <div className="relative">
            <img 
              src={imageUrl} 
              onClick={(e) => handleImageInteraction(e, true)}
              onContextMenu={(e) => handleImageInteraction(e, false)}
              alt="Interior to edit" 
              className="rounded-md cursor-crosshair"
            />
            {isSamLoading && <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center rounded-md"><p className="text-white">Loading SAM model...</p></div>}
          </div>
          {samError && <p className="text-red-500 mt-2">{samError}</p>}
        </div>
      )}

      {mask && (
        <div className="p-6 border rounded-lg shadow-sm bg-card text-card-foreground">
          <h2 className="text-xl font-semibold mb-4">3. Generate Wallpaper</h2>
          <div className="flex gap-4">
            <Input
              type="text"
              value={wallpaperUrl}
              onChange={(e) => setWallpaperUrl(e.target.value)}
              placeholder="Enter wallpaper image URL"
              className="flex-grow"
            />
            <Button onClick={handleGenerate} disabled={status === 'generating' || !wallpaperUrl}>
              {status === 'generating' ? 'Generating...' : 'Generate'}
            </Button>
          </div>
        </div>
      )}

      {status === 'success' && resultUrl && (
        <div className="p-6 border rounded-lg shadow-sm bg-card text-card-foreground">
          <h2 className="text-xl font-semibold mb-4">4. Result</h2>
          <img src={resultUrl} alt="Generated wallpaper" className="rounded-md" />
        </div>
      )}
      
      {error && <p className="text-red-500 mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">{error}</p>}
    </div>
  );
}
