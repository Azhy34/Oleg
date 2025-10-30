import { redirect } from 'next/navigation';

export default function HomePage() {
  redirect('/editor');
  return null; // This part will never be executed
}
