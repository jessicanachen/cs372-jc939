"use client";

import ChatLayout from "@/components/chat/ChatLayout";

export default function HomePage() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-slate-100 flex items-center justify-center px-4 py-6">
      <ChatLayout />
    </main>
  );
}
