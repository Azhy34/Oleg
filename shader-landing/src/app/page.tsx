import Logo from "@/components/ui/logo";
import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-center font-mono text-sm lg:flex">
        <Logo />
      </div>

      <div className="relative z-[-1] flex place-items-center text-center mt-12">
        <h1 className="text-4xl font-bold">AI Wallpaper Generator</h1>
      </div>

      <div className="mt-12">
        <Button asChild>
          <Link href="/editor">Get Started</Link>
        </Button>
      </div>
    </main>
  );
}
