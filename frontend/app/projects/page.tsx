'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { Project } from '@/lib/types';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Plus, Folder, ArrowRight, Clock, Layers } from 'lucide-react';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function fetchProjects() {
      try {
        const res = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/projects`
        );
        if (res.ok) {
          const data = await res.json();
          setProjects(data.projects || []);
        }
      } catch (e) {
        // Mock fallback projects
        setProjects([
          {
            id: 'sample-project-1',
            title: 'SaaS Analytics Platform',
            prompt: 'Create a full-stack SaaS metrics dashboard with user accounts, Stripe subscriptions, and PostgreSQL database.',
            project_type: 'application',
            status: 'ready',
            owner_id: '1',
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          },
          {
            id: 'sample-project-2',
            title: 'Minimalist Architect Portfolio',
            prompt: 'Build a high-performance static portfolio website for an architecture studio with project galleries and contact form.',
            project_type: 'website',
            status: 'ready',
            owner_id: '1',
            created_at: new Date(Date.now() - 86400000).toISOString(),
            updated_at: new Date(Date.now() - 86400000).toISOString(),
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    }
    fetchProjects();
  }, []);

  return (
    <div className="space-y-8">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="font-display font-bold text-3xl text-ink">Your Projects</h1>
          <p className="text-sm text-ink-soft mt-1">
            Manage your generated websites and full-stack applications.
          </p>
        </div>
        <Link href="/">
          <Button variant="primary">
            <Plus className="w-4 h-4 mr-1.5" />
            New Build
          </Button>
        </Link>
      </div>

      {projects.length === 0 && !isLoading ? (
        <div className="bg-white rounded-2xl p-12 border border-ink/10 text-center space-y-4">
          <div className="w-12 h-12 rounded-xl bg-ink/5 text-ink mx-auto flex items-center justify-center">
            <Folder className="w-6 h-6" />
          </div>
          <h3 className="font-display font-bold text-lg text-ink">No projects built yet</h3>
          <p className="text-sm text-ink-soft max-w-sm mx-auto">
            Submit your first prompt to generate a production-ready website or application.
          </p>
          <Link href="/">
            <Button variant="primary" size="md">
              Start Building
            </Button>
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((proj) => (
            <Link
              key={proj.id}
              href={`/projects/${proj.id}`}
              className="group block bg-white rounded-2xl p-6 border border-ink/10 shadow-sm hover:border-ink/30 hover:shadow-md transition-all"
            >
              <div className="flex items-start justify-between gap-2 mb-3">
                <Badge variant={proj.project_type === 'website' ? 'amber' : 'indigo'}>
                  {proj.project_type}
                </Badge>
                <span className="flex items-center gap-1 text-[11px] font-mono text-ink-muted">
                  <Clock className="w-3 h-3" />
                  {new Date(proj.created_at).toLocaleDateString()}
                </span>
              </div>

              <h3 className="font-display font-bold text-lg text-ink group-hover:text-forge-indigo transition-colors line-clamp-1 mb-2">
                {proj.title}
              </h3>

              <p className="text-xs text-ink-soft line-clamp-2 mb-4 leading-relaxed">
                {proj.prompt}
              </p>

              <div className="pt-4 border-t border-ink/5 flex items-center justify-between text-xs font-mono text-ink-soft">
                <span className="flex items-center gap-1 text-emerald-600 font-semibold">
                  ● Ready
                </span>
                <span className="flex items-center gap-1 group-hover:text-ink font-bold">
                  Open Studio <ArrowRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
