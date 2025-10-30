'use client';

import React, { useState, useMemo, useCallback } from 'react';
import dynamic from 'next/dynamic';
import { useAppStore } from '@/lib/store';
import { createSession, generateWallpaper, pollStatus } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

const MaskEditor = dynamic(
  () => import('react-canvas-masker').then(mod => mod.MaskEditor),
  { 
    ssr: false,
    loading: () => <div className="w-full h-96 bg-muted animate-pulse rounded-md" /> 
  }
);

const handleApiError = (err: unknown, setError: (message: string) => void) => {
  const message = err instanceof Error ? err.message : 'An unknown error occurred.';
  setError(message);
};

export default function EditorWorkflow() {
  const [imageFile, setImageFile] = useState<File | null>(null);
  const [wallpaperUrl, setWallpaperUrl] = useState('');
  const [maskDataUrl, setMaskDataUrl] = useState<string | null>(null);
  const [drawing, setDrawing] = useState<any>(null); // State for the drawing history

  const { sessionId, status, resultUrl, error, reset, startSession, startGeneration, setSuccess, setError } = useAppStore();

  const imageUrl = useMemo(() => (imageFile ? URL.createObjectURL(imageFile) : null), [imageFile]);

  const handleFileChange = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      reset();
      setImageFile(file);
      setMaskDataUrl(null);
      try {
        const session = await createSession(file);
        startSession(session.session_id);
      } catch (err) {
        handleApiError(err, setError);
      }
    }
  }, [reset, startSession, setError]);

  const handleGenerate = useCallback(async () => {
    if (!sessionId || !maskDataUrl) return;
    try {
      startGeneration();
      await generateWallpaper(sessionId, maskDataUrl, wallpaperUrl);
    } catch (err) {
      handleApiError(err, setError);
    }
  }, [sessionId, maskDataUrl, wallpaperUrl, startGeneration, setError]);

  // Effect for polling status for final result
  React.useEffect(() => {
    if (status !== 'generating' || !sessionId) return;
    const interval = setInterval(async () => {
      try {
        const data = await pollStatus(sessionId);
        if (data.status === 'completed' && data.result_s3_path) {
          setSuccess(data.result_s3_path);
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
          <p className="text-sm text-muted-foreground mb-2">Draw on the image to create a mask. Use the toolbar to undo, redo, and adjust the brush.</p>
          <div className="relative border rounded-md overflow-hidden">
            <MaskEditor
              src={imageUrl}
              onDrawingChange={setDrawing}
              onMaskChange={setMaskDataUrl}
            />
          </div>
        </div>
      )}

      {maskDataUrl && (
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
