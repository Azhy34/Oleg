'use client';

import EditorWorkflow from '@/components/editor/EditorWorkflow';

export default function EditorPage() {
  return (
    <main className="container mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">AI Wallpaper Editor</h1>
      <EditorWorkflow />
    </main>
  );
}
