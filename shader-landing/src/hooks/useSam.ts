import { useState, useEffect, useCallback, useRef } from 'react';
import { InferenceSession } from 'onnxruntime-web';
import { handleImageScale, getTensor, getClicksTensor, rleToMask } from '@/lib/utils';

// --- Types ---
interface SamClick {
  x: number;
  y: number;
  isPositive: boolean;
}

// --- Model Singleton ---
let modelSingleton: InferenceSession | null = null;

const loadModel = async (): Promise<InferenceSession> => {
  if (modelSingleton) return modelSingleton;

  const ort = await import('onnxruntime-web');
  ort.env.wasm.wasmPaths = "/";
  const modelUrl = '/sam_model.onnx'; // Assuming the model is in the public folder
  const sessionOptions: InferenceSession.SessionOptions = {
    executionProviders: ['wasm'],
    graphOptimizationLevel: 'basic',
  };
  const session = await ort.InferenceSession.create(modelUrl, sessionOptions);
  modelSingleton = session;
  return session;
};

// --- Hook ---
export const useSam = (imageUrl: string | null) => {
  const [model, setModel] = useState<InferenceSession | null>(null);
  const [clicks, setClicks] = useState<SamClick[]>([]);
  const [mask, setMask] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true); // Start with loading true for model loading
  const [error, setError] = useState<string | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);

  // Effect to load the ONNX model once
  useEffect(() => {
    loadModel()
      .then(setModel)
      .catch(e => {
        console.error("Error loading ONNX model:", e);
        setError(`Failed to load segmentation model: ${e instanceof Error ? e.message : String(e)}`);
      })
      .finally(() => setIsLoading(false));
  }, []);

  // Effect to run inference whenever clicks change
  useEffect(() => {
    const runInference = async () => {
      if (!model || !imageUrl || clicks.length === 0) return;

      setIsLoading(true);
      setError(null);

      try {
        if (!imageRef.current) {
          const img = new Image();
          img.src = imageUrl;
          await new Promise(resolve => { img.onload = resolve; });
          imageRef.current = img;
        }
        const image = imageRef.current;

        const { scale, scaledWidth, scaledHeight } = handleImageScale(image);
        const imageTensor = await getTensor(image, scaledWidth, scaledHeight);
        const clicksTensor = getClicksTensor(clicks, scale);
        const ort = await import('onnxruntime-web');

        const feeds = {
          "image": imageTensor,
          "point_coords": clicksTensor,
          "point_labels": new ort.Tensor('float32', new Float32Array([...clicks.map(c => c.isPositive ? 1 : 0), -1]), [1, clicks.length + 1]),
        };

        const results = await model.run(feeds);
        const maskData = rleToMask(results.mask.data as unknown as number[], image.width, image.height);
        setMask(maskData);
      } catch (e) {
        console.error("Inference error:", e);
        setError('Failed to generate mask.');
      } finally {
        setIsLoading(false);
      }
    };

    runInference();
  }, [model, imageUrl, clicks]);

  const handleImageClick = (x: number, y: number, isPositive: boolean) => {
    if (isLoading) return; // Prevent clicks while model or mask is loading
    if (error) {
      console.warn("Cannot add clicks while an error is present.");
      return;
    }
    if (!imageUrl) {
      setError('Cannot add clicks before an image is loaded.');
      return;
    }
    setClicks(prevClicks => [...prevClicks, { x, y, isPositive }]);
  };

  return { mask, isLoading, error, handleImageClick };
};
