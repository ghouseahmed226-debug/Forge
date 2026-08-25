'use client';

import React, { useState } from 'react';
import { ProjectFile } from '@/lib/types';
import { Badge } from './ui/Badge';
import { Button } from './ui/Button';
import { HelpCircle, Copy, Check, Edit3, Eye } from 'lucide-react';

interface CodePreviewProps {
  file?: ProjectFile;
  onEdit?: (newContent: string) => void;
}

export function CodePreview({ file, onEdit }: CodePreviewProps) {
  const [copied, setCopied] = useState(false);
  const [showReason, setShowReason] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [content, setContent] = useState(file?.content || '');

  React.useEffect(() => {
    setContent(file?.content || '');
    setIsEditing(false);
  }, [file]);

  if (!file) {
    return (
      <div className="w-full h-full min-h-[400px] bg-ink rounded-xl flex items-center justify-center border border-ink/20 p-8 text-center">
        <div>
          <p className="font-mono text-sm text-ink-muted">Select a file from the explorer to view code</p>
        </div>
      </div>
    );
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const isReasoning =
    file.generated_by_model.includes('opus') ||
    file.generated_by_model.includes('gpt-4o') ||
    file.generated_by_model.includes('pro');

  const tier = isReasoning ? 'reasoning' : 'fast';

  return (
    <div className="w-full h-full flex flex-col bg-ink text-paper rounded-xl border border-ink/20 shadow-sm overflow-hidden">
      {/* Top bar */}
      <div className="flex items-center justify-between px-4 py-2.5 bg-ink/90 border-b border-white/10">
        <div className="flex items-center gap-3">
          <span className="font-mono text-xs text-white font-medium">{file.path}</span>
          <Badge variant={tier === 'reasoning' ? 'indigo' : 'amber'} size="sm">
            {file.generated_by_model}
          </Badge>
          <button
            onClick={() => setShowReason(!showReason)}
            className="flex items-center gap-1 text-[11px] font-mono text-ink-muted hover:text-white transition-colors"
          >
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Why this model?</span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsEditing(!isEditing)}
            className="text-white/80 hover:text-white hover:bg-white/10"
          >
            <Edit3 className="w-3.5 h-3.5 mr-1" />
            {isEditing ? 'Preview' : 'Edit'}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleCopy}
            className="text-white/80 hover:text-white hover:bg-white/10"
          >
            {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
          </Button>
        </div>
      </div>

      {/* Why This Model Reveal Drawer */}
      {showReason && (
        <div className="px-4 py-3 bg-white/5 border-b border-white/10 font-mono text-xs text-white/90">
          <div className="flex items-center justify-between">
            <span className="font-bold text-forge-amber">Routing Transparency:</span>
            <span className="text-[10px] text-white/60">Explicit routing rule applied</span>
          </div>
          <p className="mt-1 text-white/80 font-sans text-xs">
            {tier === 'fast'
              ? 'Routed to Fast Tier: High volume scaffolding and markup generation. Optimized for speed and low cost with style consistency.'
              : 'Routed to Reasoning Tier: Security-sensitive logic and schema normalization. Requires deep logical correctness to prevent downstream security issues.'}
          </p>
        </div>
      )}

      {/* Code Editor / Viewer */}
      <div className="flex-1 p-4 overflow-auto font-mono text-xs leading-relaxed bg-[#0D0E11]">
        {isEditing ? (
          <textarea
            value={content}
            onChange={(e) => {
              setContent(e.target.value);
              if (onEdit) onEdit(e.target.value);
            }}
            className="w-full h-full min-h-[350px] bg-transparent text-white font-mono text-xs resize-none focus:outline-none"
            spellCheck={false}
          />
        ) : (
          <pre className="text-white/90">
            <code>{content}</code>
          </pre>
        )}
      </div>
    </div>
  );
}
