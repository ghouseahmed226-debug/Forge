import type { Metadata } from 'next';
import './globals.css';
import Link from 'next/link';
import { Cpu, Layers, Github } from 'lucide-react';

export const metadata: Metadata = {
  title: 'Forge — Multi-Model App Orchestration Platform',
  description: 'Generate production-ready websites and full-stack apps with visible multi-model routing and mandatory security review.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-paper text-ink selection:bg-forge-indigo/20 selection:text-forge-indigo">
        {/* Navigation Bar */}
        <header className="sticky top-0 z-40 w-full border-b border-ink/10 bg-paper/80 backdrop-blur-md">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2.5 group">
              <div className="w-8 h-8 rounded-lg bg-ink flex items-center justify-center text-white group-hover:bg-forge-indigo transition-colors shadow-sm">
                <Layers className="w-4 h-4" />
              </div>
              <div className="flex flex-col">
                <span className="font-display font-bold text-lg leading-tight tracking-tight text-ink">
                  FORGE
                </span>
                <span className="text-[10px] font-mono text-ink-muted -mt-0.5">
                  Multi-Model Orchestrator
                </span>
              </div>
            </Link>

            <nav className="flex items-center gap-6">
              <Link
                href="/projects"
                className="text-xs font-mono text-ink-soft hover:text-ink transition-colors"
              >
                Projects
              </Link>
              <Link
                href="https://github.com/ghouseahmed226-debug/Forge"
                target="_blank"
                rel="noreferrer"
                className="flex items-center gap-1.5 text-xs font-mono text-ink-soft hover:text-ink transition-colors"
              >
                <Github className="w-3.5 h-3.5" />
                GitHub
              </Link>
            </nav>
          </div>
        </header>

        {/* Main Content Area */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>

        {/* Footer */}
        <footer className="w-full border-t border-ink/10 bg-white py-6">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-mono text-ink-soft">
            <div className="flex items-center gap-2">
              <span>© {new Date().getFullYear()} Forge. You own all generated code.</span>
            </div>
            <div className="flex items-center gap-4">
              <Link href="/terms.md" className="hover:text-ink underline">
                Terms of Service & IP
              </Link>
              <span>•</span>
              <span>Claude + OpenAI + Gemini Multi-Tier Architecture</span>
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
