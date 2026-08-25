'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RoutingSegment, TierType } from '@/lib/types';
import { Badge } from './ui/Badge';
import { CheckCircle2, Clock, AlertTriangle, ShieldCheck, Cpu } from 'lucide-react';

interface RoutingTraceProps {
  segments: RoutingSegment[];
  isLive?: boolean;
}

export function RoutingTrace({ segments, isLive = false }: RoutingTraceProps) {
  const [activeSegment, setActiveSegment] = useState<RoutingSegment | null>(null);

  const getTierColor = (tier: TierType) => {
    switch (tier) {
      case 'fast':
        return {
          bg: 'bg-forge-amber',
          border: 'border-forge-amber',
          text: 'text-forge-amber',
          glow: 'shadow-[0_0_15px_rgba(216,154,59,0.4)]',
          badgeVariant: 'amber' as const,
        };
      case 'reasoning':
        return {
          bg: 'bg-forge-indigo',
          border: 'border-forge-indigo',
          text: 'text-forge-indigo',
          glow: 'shadow-[0_0_15px_rgba(79,95,224,0.4)]',
          badgeVariant: 'indigo' as const,
        };
      case 'critic':
        return {
          bg: 'bg-forge-teal',
          border: 'border-forge-teal',
          text: 'text-forge-teal',
          glow: 'shadow-[0_0_15px_rgba(31,158,142,0.4)]',
          badgeVariant: 'teal' as const,
        };
    }
  };

  const getTaskLabel = (taskType: string) => {
    switch (taskType) {
      case 'ui_scaffold':
        return 'UI Scaffold';
      case 'copy_generation':
        return 'Copy Generation';
      case 'data_models':
        return 'Data Models';
      case 'business_logic':
        return 'Business Logic';
      case 'security_review':
        return 'Security & RLS Review';
      default:
        return taskType.replace(/_/g, ' ');
    }
  };

  return (
    <div className="w-full bg-white rounded-xl p-5 border border-ink/10 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-md bg-ink/5 text-ink">
            <Cpu className="w-4 h-4" />
          </div>
          <h4 className="font-display font-bold text-sm tracking-tight text-ink uppercase">
            Multi-Model Routing Trace
          </h4>
          {isLive && (
            <span className="flex items-center gap-1.5 text-xs text-forge-indigo font-mono">
              <span className="w-2 h-2 rounded-full bg-forge-indigo animate-ping" />
              Routing Live
            </span>
          )}
        </div>
        <div className="flex items-center gap-4 text-xs font-mono text-ink-soft">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-forge-amber" /> Fast Tier
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-forge-indigo" /> Reasoning Tier
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-forge-teal" /> Critic Pass
          </span>
        </div>
      </div>

      {/* Horizontal Relay Strip */}
      <div className="relative mt-2 flex flex-col md:flex-row items-stretch gap-2 bg-paper/60 p-2 rounded-lg border border-ink/5 overflow-x-auto">
        {segments.map((seg, idx) => {
          const colors = getTierColor(seg.tier);
          const isRunning = seg.status === 'running';
          const isDone = seg.status === 'done';

          return (
            <motion.div
              key={`${seg.taskType}-${idx}`}
              initial={{ opacity: 0, x: -15 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.3, delay: idx * 0.1 }}
              onClick={() => setActiveSegment(seg)}
              className={`flex-1 min-w-[170px] p-3 rounded-lg border transition-all cursor-pointer select-none ${
                isRunning
                  ? `${colors.border} bg-white ${colors.glow} animate-pulse-slow ring-1 ring-offset-1`
                  : isDone
                  ? 'border-ink/10 bg-white hover:border-ink/30 hover:shadow-sm'
                  : 'border-ink/5 bg-paper/40 opacity-60'
              }`}
            >
              <div className="flex items-center justify-between gap-1 mb-1.5">
                <span className="text-[11px] font-bold text-ink truncate">
                  {getTaskLabel(seg.taskType)}
                </span>
                <Badge variant={colors.badgeVariant} size="sm">
                  {seg.tier}
                </Badge>
              </div>

              <div className="flex items-center justify-between text-[11px] font-mono text-ink-soft">
                <span className="truncate max-w-[100px]">{seg.modelUsed || 'Routing...'}</span>
                {seg.latencyMs ? (
                  <span className="flex items-center gap-0.5 text-[10px]">
                    <Clock className="w-3 h-3" />
                    {(seg.latencyMs / 1000).toFixed(1)}s
                  </span>
                ) : isRunning ? (
                  <span className="text-[10px] text-forge-indigo font-semibold">running</span>
                ) : null}
              </div>

              {/* Status bar */}
              <div className="mt-2 w-full h-1 rounded-full bg-paper overflow-hidden">
                <div
                  className={`h-full ${colors.bg} ${
                    isRunning ? 'w-2/3 animate-pulse' : isDone ? 'w-full' : 'w-0'
                  }`}
                />
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Segment Inspection Drawer */}
      <AnimatePresence>
        {activeSegment && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-3 p-4 rounded-lg bg-paper border border-ink/10 text-xs"
          >
            <div className="flex items-start justify-between">
              <div>
                <div className="flex items-center gap-2">
                  <h5 className="font-display font-bold text-sm text-ink">
                    {getTaskLabel(activeSegment.taskType)}
                  </h5>
                  <Badge variant={getTierColor(activeSegment.tier).badgeVariant}>
                    {activeSegment.tier} Tier
                  </Badge>
                </div>
                <p className="mt-1 text-ink-soft font-sans text-xs max-w-xl">
                  {activeSegment.routingReason}
                </p>
              </div>
              <button
                onClick={() => setActiveSegment(null)}
                className="text-ink-soft hover:text-ink font-mono text-xs"
              >
                Close ✕
              </button>
            </div>

            <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 pt-3 border-t border-ink/10 font-mono text-[11px]">
              <div>
                <span className="text-ink-muted block">Model Assigned</span>
                <span className="font-medium text-ink">{activeSegment.modelUsed}</span>
              </div>
              <div>
                <span className="text-ink-muted block">Latency</span>
                <span className="font-medium text-ink">
                  {activeSegment.latencyMs ? `${activeSegment.latencyMs} ms` : 'In progress'}
                </span>
              </div>
              <div>
                <span className="text-ink-muted block">Estimated Cost</span>
                <span className="font-medium text-ink">
                  ${activeSegment.costUsd?.toFixed(4) || '0.0000'}
                </span>
              </div>
              <div>
                <span className="text-ink-muted block">Target File</span>
                <span className="font-medium text-ink truncate block">
                  {activeSegment.filePath || 'Auto-assigned'}
                </span>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
