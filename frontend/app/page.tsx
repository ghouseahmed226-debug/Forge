'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { PromptChips } from '@/components/PromptChips';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { generateProject } from '@/lib/api';
import { Sparkles, ArrowRight, ShieldCheck, Zap, Cpu, CheckCircle2, Globe, Database } from 'lucide-react';

export default function HomePage() {
  const router = useRouter();
  const [prompt, setPrompt] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Ambiguity Confirmation State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [ambiguityDetails, setAmbiguityDetails] = useState('');

  const handleBuild = async (overrideType?: 'website' | 'application') => {
    if (!prompt.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const res = await generateProject(prompt, overrideType);

      if (res.requires_confirmation) {
        setAmbiguityDetails(res.ambiguity_details || 'Please clarify project scope.');
        setIsModalOpen(true);
        setIsLoading(false);
      } else {
        router.push(`/generate/${res.project_id}`);
      }
    } catch (err: any) {
      setError(err.message || 'Generation request failed');
      setIsLoading(false);
    }
  };

  const handleSelectChip = (chipPrompt: string, chipType: 'website' | 'application') => {
    setPrompt(chipPrompt);
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-16 py-4 sm:py-8">
      {/* Hero Section */}
      <div className="text-center max-w-3xl space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-forge-indigo/10 border border-forge-indigo/20 text-xs font-mono text-forge-indigo">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Multi-Model Orchestration Engine</span>
        </div>
        <h1 className="font-display font-bold text-4xl sm:text-5xl md:text-6xl tracking-tight text-ink">
          Build anything.{' '}
          <span className="text-forge-indigo">Route to the right model.</span>
        </h1>
        <p className="text-base sm:text-lg text-ink-soft max-w-2xl mx-auto leading-relaxed">
          Fast models for scaffolding. Strong reasoning models for business logic. Mandatory critic pass for auth and security. Full routing transparency on every line of generated code.
        </p>
      </div>

      {/* Main Generation Input Box */}
      <div className="w-full max-w-3xl bg-white rounded-2xl p-6 shadow-sm border border-ink/10 space-y-4">
        <div className="relative">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Describe what you want to build... (e.g. A team task management board with user roles, auth, and database)"
            rows={4}
            className="w-full p-4 rounded-xl bg-paper/50 border border-ink/15 text-ink text-sm sm:text-base placeholder:text-ink-muted focus:outline-none focus:ring-2 focus:ring-ink focus:bg-white transition-all resize-none"
          />
          <div className="absolute right-3 bottom-3 text-xs font-mono text-ink-muted">
            {prompt.length} chars
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-xs text-rose-600 font-mono">
            {error}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
          <PromptChips onSelect={handleSelectChip} />
        </div>

        <div className="pt-2 flex justify-end">
          <Button
            size="lg"
            variant="primary"
            isLoading={isLoading}
            onClick={() => handleBuild()}
            disabled={!prompt.trim()}
            className="w-full sm:w-auto px-8"
          >
            <span>Build</span>
            <ArrowRight className="w-4 h-4 ml-2" />
          </Button>
        </div>
      </div>

      {/* Confirmation Modal for Ambiguous Prompts */}
      <Modal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        title="Confirm Project Architecture"
      >
        <div className="space-y-4 text-sm">
          <p className="text-ink-soft">{ambiguityDetails}</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
            <button
              onClick={() => {
                setIsModalOpen(false);
                handleBuild('website');
              }}
              className="p-4 rounded-xl border border-forge-amber/30 bg-forge-amber/5 hover:bg-forge-amber/10 text-left transition-all group"
            >
              <div className="flex items-center gap-2 text-forge-amber font-display font-bold mb-1">
                <Globe className="w-4 h-4" />
                <span>Static Website</span>
              </div>
              <p className="text-xs text-ink-soft">
                Marketing, content, or portfolio. Lightweight static export with no database provisioned.
              </p>
            </button>

            <button
              onClick={() => {
                setIsModalOpen(false);
                handleBuild('application');
              }}
              className="p-4 rounded-xl border border-forge-indigo/30 bg-forge-indigo/5 hover:bg-forge-indigo/10 text-left transition-all group"
            >
              <div className="flex items-center gap-2 text-forge-indigo font-display font-bold mb-1">
                <Database className="w-4 h-4" />
                <span>Full-Stack App</span>
              </div>
              <p className="text-xs text-ink-soft">
                Data-backed with user auth, Postgres database, business logic, and security critic pass.
              </p>
            </button>
          </div>
        </div>
      </Modal>

      {/* How it Works / Routing Table Legend */}
      <div className="w-full max-w-5xl space-y-8">
        <div className="text-center space-y-2">
          <h3 className="font-display font-bold text-2xl text-ink">
            Explicit Multi-Model Routing Logic
          </h3>
          <p className="text-sm text-ink-soft">
            No single model is optimal for every step. Forge routes subtasks by complexity, risk, and security profile.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-2xl border border-forge-amber/30 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-forge-amber/10 text-forge-amber flex items-center justify-center">
              <Zap className="w-5 h-5" />
            </div>
            <h4 className="font-display font-bold text-lg text-ink">Fast Tier</h4>
            <p className="text-xs font-mono text-forge-amber">Claude Haiku / GPT-4o-mini / Gemini Flash</p>
            <p className="text-xs text-ink-soft leading-relaxed">
              Handles high-volume UI component scaffolding and copy generation. Fast execution, low token cost, style consistency.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-forge-indigo/30 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-forge-indigo/10 text-forge-indigo flex items-center justify-center">
              <Cpu className="w-5 h-5" />
            </div>
            <h4 className="font-display font-bold text-lg text-ink">Reasoning Tier</h4>
            <p className="text-xs font-mono text-forge-indigo">Claude Opus / GPT-4o / Gemini Pro</p>
            <p className="text-xs text-ink-soft leading-relaxed">
              Designs database schemas, normalization rules, and complex business logic. Prevents architectural mistakes from compounding.
            </p>
          </div>

          <div className="bg-white p-6 rounded-2xl border border-forge-teal/30 shadow-sm space-y-3">
            <div className="w-10 h-10 rounded-xl bg-forge-teal/10 text-forge-teal flex items-center justify-center">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <h4 className="font-display font-bold text-lg text-ink">Mandatory Critic Pass</h4>
            <p className="text-xs font-mono text-forge-teal">Rigorous Adversarial Security Audit</p>
            <p className="text-xs text-ink-soft leading-relaxed">
              Audits auth logic, Row-Level Security policies, and payment flows. Code with vulnerabilities is rejected and rewritten before shipping.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
