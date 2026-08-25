'use client';

import React from 'react';
import { Sparkles, Globe, Database } from 'lucide-react';

interface PromptChipsProps {
  onSelect: (prompt: string, type: 'website' | 'application') => void;
}

const EXAMPLE_PROMPTS = [
  {
    type: 'website' as const,
    label: 'Portfolio site for a product designer',
    prompt: 'Create a clean, minimalist portfolio website for a product designer featuring case study cards, an interactive about me section, and a contact form.',
  },
  {
    type: 'website' as const,
    label: 'Marketing page for a SaaS tool',
    prompt: 'Build a high-converting marketing landing page for a developer productivity tool with hero section, feature grid, pricing table, and interactive FAQ.',
  },
  {
    type: 'website' as const,
    label: 'Recipe blog with category filter',
    prompt: 'Build a modern food and recipe blog with searchable recipe cards, dietary tags, cooking time badges, and a newsletter sign-up footer.',
  },
  {
    type: 'application' as const,
    label: 'Project tracker for small teams',
    prompt: 'Build a data-backed team project tracking application with Supabase authentication, Kanban boards, task assignments, role-based permissions, and RLS policies.',
  },
  {
    type: 'application' as const,
    label: 'Customer support ticket system',
    prompt: 'Create a customer support ticketing system with user authentication, ticket status workflows, priority tags, response threads, and admin analytics.',
  },
  {
    type: 'application' as const,
    label: 'E-commerce store with catalog',
    prompt: 'Build a full-stack e-commerce store with user accounts, product catalog, category filters, shopping cart state management, and Stripe checkout logic.',
  },
];

export function PromptChips({ onSelect }: PromptChipsProps) {
  return (
    <div className="w-full">
      <div className="flex items-center gap-1.5 text-xs font-mono text-ink-soft mb-2.5">
        <Sparkles className="w-3.5 h-3.5 text-forge-amber" />
        <span>Try an example prompt to start:</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {EXAMPLE_PROMPTS.map((item, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => onSelect(item.prompt, item.type)}
            className={`group inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-white border transition-all text-left hover:scale-[1.02] active:scale-[0.98] ${
              item.type === 'website'
                ? 'border-forge-amber/30 hover:border-forge-amber hover:bg-forge-amber/5 text-ink'
                : 'border-forge-indigo/30 hover:border-forge-indigo hover:bg-forge-indigo/5 text-ink'
            }`}
          >
            {item.type === 'website' ? (
              <Globe className="w-3 h-3 text-forge-amber shrink-0" />
            ) : (
              <Database className="w-3 h-3 text-forge-indigo shrink-0" />
            )}
            <span className="text-ink-soft group-hover:text-ink transition-colors">
              {item.label}
            </span>
            <span
              className={`text-[10px] font-mono px-1 py-0.2 rounded uppercase ${
                item.type === 'website'
                  ? 'bg-forge-amber/10 text-forge-amber'
                  : 'bg-forge-indigo/10 text-forge-indigo'
              }`}
            >
              {item.type}
            </span>
          </button>
        ))}
      </div>
    </div>
  );
}
