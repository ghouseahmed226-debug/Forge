'use client';

import React, { useState } from 'react';
import { GateResult, ProjectType } from '@/lib/types';
import { ShieldCheck, CheckCircle, XCircle, ChevronDown, ChevronUp, Award } from 'lucide-react';
import { Badge } from './ui/Badge';

interface QualityGatePanelProps {
  gates: GateResult[];
  projectType: ProjectType;
}

export function QualityGatePanel({ gates, projectType }: QualityGatePanelProps) {
  const [isOpen, setIsOpen] = useState(false);

  const passedCount = gates.filter((g) => g.passed).length;
  const totalCount = gates.length || (projectType === 'website' ? 9 : 10);
  const allPassed = passedCount === totalCount && totalCount > 0;

  return (
    <div className="w-full bg-white rounded-xl border border-ink/10 shadow-sm overflow-hidden">
      {/* Header Bar */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-paper/40 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${allPassed ? 'bg-emerald-500/10 text-emerald-600' : 'bg-forge-amber/10 text-forge-amber'}`}>
            <Award className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h4 className="font-display font-bold text-sm text-ink">
                Quality Pipeline Verification
              </h4>
              <Badge variant={allPassed ? 'success' : 'amber'} size="sm">
                {passedCount}/{totalCount} Gates Passed
              </Badge>
            </div>
            <p className="text-xs text-ink-soft mt-0.5">
              11 automated quality checks: WCAG 2.1 AA, Core Web Vitals, Responsive, Security Critic, and Smoke Tests
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-ink-soft">
          <span className="text-xs font-mono">{isOpen ? 'Hide Details' : 'View Audit'}</span>
          {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </button>

      {/* Expanded Gate Details */}
      {isOpen && (
        <div className="p-4 pt-0 border-t border-ink/5 bg-paper/30">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-3">
            {gates.map((gate, idx) => (
              <div
                key={idx}
                className="p-3 bg-white rounded-lg border border-ink/10 flex items-start gap-2.5"
              >
                {gate.passed ? (
                  <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0 mt-0.5" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5" />
                )}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-bold text-ink uppercase">
                      {gate.gate_name.replace(/_/g, ' ')}
                    </span>
                    {gate.score !== undefined && (
                      <span className="text-[10px] font-mono text-ink-muted">
                        Score: {(gate.score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-ink-soft mt-0.5">{gate.details}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
