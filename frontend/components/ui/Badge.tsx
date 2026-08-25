import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: 'amber' | 'indigo' | 'teal' | 'neutral' | 'success' | 'danger';
  size?: 'sm' | 'md';
}

export function Badge({
  className,
  variant = 'neutral',
  size = 'md',
  children,
  ...props
}: BadgeProps) {
  const baseStyles = 'inline-flex items-center font-mono font-medium rounded-md uppercase tracking-wider';

  const sizeStyles = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-xs',
  };

  const variantStyles = {
    amber: 'bg-forge-amber/15 text-forge-amber border border-forge-amber/30',
    indigo: 'bg-forge-indigo/15 text-forge-indigo border border-forge-indigo/30',
    teal: 'bg-forge-teal/15 text-forge-teal border border-forge-teal/30',
    neutral: 'bg-ink/10 text-ink-soft border border-ink/15',
    success: 'bg-emerald-500/15 text-emerald-600 border border-emerald-500/30',
    danger: 'bg-rose-500/15 text-rose-600 border border-rose-500/30',
  };

  return (
    <span
      className={twMerge(clsx(baseStyles, sizeStyles[size], variantStyles[variant], className))}
      {...props}
    >
      {children}
    </span>
  );
}
