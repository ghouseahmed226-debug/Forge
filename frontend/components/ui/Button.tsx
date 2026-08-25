import React from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { Spinner } from './Spinner';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'amber' | 'indigo' | 'teal';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
}

export function Button({
  className,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const baseStyles = 'inline-flex items-center justify-center font-medium rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const sizeStyles = {
    sm: 'px-3 py-1.5 text-xs',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const variantStyles = {
    primary: 'bg-ink text-white hover:bg-ink-soft focus:ring-ink shadow-sm',
    secondary: 'bg-paper text-ink border border-ink/20 hover:bg-white hover:border-ink/40 focus:ring-ink/20',
    ghost: 'text-ink-soft hover:bg-ink/5 hover:text-ink',
    amber: 'bg-forge-amber text-white hover:brightness-110 focus:ring-forge-amber',
    indigo: 'bg-forge-indigo text-white hover:brightness-110 focus:ring-forge-indigo',
    teal: 'bg-forge-teal text-white hover:brightness-110 focus:ring-forge-teal',
  };

  return (
    <button
      className={twMerge(clsx(baseStyles, sizeStyles[size], variantStyles[variant], className))}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading && <Spinner className="w-4 h-4 mr-2" />}
      {children}
    </button>
  );
}
