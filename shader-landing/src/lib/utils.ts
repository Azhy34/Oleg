import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"
import * as ort from 'onnxruntime-web';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// Helper function to scale the image and clicks to the model's input size.
export const handleImageScale = (image: HTMLImageElement) => {
  const MODEL_INPUT_SIZE = 1024;
  const { width, height } = image;
  const scale = MODEL_INPUT_SIZE / Math.max(width, height);
  return {
    scale,
    scaledWidth: width * scale,
    scaledHeight: height * scale,
  };
};

// Prepares the image data for the ONNX model.
export const getTensor = async (image: HTMLImageElement, scaledWidth: number, scaledHeight: number) => {
  const canvas = document.createElement('canvas');
  canvas.width = scaledWidth;
  canvas.height = scaledHeight;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Could not get canvas context');

  ctx.drawImage(image, 0, 0, scaledWidth, scaledHeight);
  const data = ctx.getImageData(0, 0, scaledWidth, scaledHeight).data;
  const float32Data = new Float32Array(3 * scaledWidth * scaledHeight);

  for (let i = 0; i < scaledWidth * scaledHeight; i++) {
    float32Data[i] = data[i * 4]; // R
    float32Data[i + scaledWidth * scaledHeight] = data[i * 4 + 1]; // G
    float32Data[i + 2 * scaledWidth * scaledHeight] = data[i * 4 + 2]; // B
  }

  return new ort.Tensor('float32', float32Data, [1, 3, scaledHeight, scaledWidth]);
};

// Prepares the click data for the ONNX model.
export const getClicksTensor = (clicks: any[], scale: number) => {
  const n = clicks.length;
  const clicksData = new Float32Array(2 * (n + 1));
  for (let i = 0; i < n; i++) {
    clicksData[2 * i] = clicks[i].x * scale;
    clicksData[2 * i + 1] = clicks[i].y * scale;
  }
  // Add a padding click
  clicksData[2 * n] = -1.0;
  clicksData[2 * n + 1] = -1.0;
  return new ort.Tensor('float32', clicksData, [1, n + 1, 2]);
};

// Decodes the Run-Length Encoded mask from the model output.
export const rleToMask = (rle: number[], width: number, height: number) => {
  const canvas = document.createElement('canvas');
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('Could not get canvas context');

  const imageData = ctx.createImageData(width, height);
  const data = imageData.data;
  let p = 0;
  for (let i = 0; i < rle.length; i++) {
    const count = rle[i];
    const color = i % 2 === 0 ? 0 : 1; // 0 for background, 1 for mask
    for (let j = 0; j < count; j++) {
      if (p < data.length) {
        data[p++] = 87;   // R
        data[p++] = 13,    // G
        data[p++] = 244;   // B
        data[p++] = color * 128; // A (50% opacity for the mask)
      }
    }
  }
  ctx.putImageData(imageData, 0, 0);
  return canvas.toDataURL();
};

/**
 * Calculates the click coordinates on the original image based on a click event.
 * @param event - The mouse event.
 * @returns The coordinates { x, y } on the original image.
 */
export const getOriginalCoords = (event: React.MouseEvent<HTMLImageElement>) => {
  const image = event.currentTarget;
  const rect = image.getBoundingClientRect();

  // Get the original image dimensions
  const { naturalWidth, naturalHeight } = image;
  // Get the displayed image dimensions
  const { clientWidth, clientHeight } = image;

  // Calculate the scale factor
  const scaleX = naturalWidth / clientWidth;
  const scaleY = naturalHeight / clientHeight;

  // Calculate the click coordinates relative to the image element
  const clickX = event.clientX - rect.left;
  const clickY = event.clientY - rect.top;

  // Scale the coordinates to the original image size
  const originalX = clickX * scaleX;
  const originalY = clickY * scaleY;

  return { x: originalX, y: originalY };
};
