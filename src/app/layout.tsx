import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "Taste Library",
  description: "Design inspiration we've saved — and the style vocabulary Claude draws on for website builds.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <div className="mx-auto max-w-6xl px-6 py-8">
          <header className="mb-8 flex items-center justify-between">
            <Link href="/" className="text-lg font-semibold tracking-tight">
              Taste Library
            </Link>
            <nav className="flex gap-4 text-sm text-ink/70">
              <Link href="/" className="hover:text-ink">Gallery</Link>
              <Link href="/upload" className="hover:text-ink">Save a reference</Link>
            </nav>
          </header>
          {children}
        </div>
      </body>
    </html>
  );
}
