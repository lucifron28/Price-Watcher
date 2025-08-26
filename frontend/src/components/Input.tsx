import { forwardRef } from 'react';
import type { InputHTMLAttributes } from 'react';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  variant?: 'default' | 'filled';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, variant = 'default', className = '', ...props }, ref) => {
    const baseClasses = `
      w-full px-4 py-3 text-sm rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2
      dark:focus:ring-offset-dark-bg
    `;

    const variantClasses = {
      default: `
        border border-light-border dark:border-dark-border
        bg-light-bg dark:bg-dark-card
        text-light-text-primary dark:text-dark-text-primary
        focus:ring-light-accent dark:focus:ring-dark-accent
        focus:border-light-accent dark:focus:border-dark-accent
        placeholder:text-light-text-secondary dark:placeholder:text-dark-text-secondary
      `,
      filled: `
        border-0 bg-gray-100 dark:bg-gray-800
        text-light-text-primary dark:text-dark-text-primary
        focus:ring-light-accent dark:focus:ring-dark-accent
        placeholder:text-light-text-secondary dark:placeholder:text-dark-text-secondary
      `,
    };

    const errorClasses = error ? `
      border-light-danger dark:border-dark-danger
      focus:ring-light-danger dark:focus:ring-dark-danger
      focus:border-light-danger dark:focus:border-dark-danger
    ` : '';

    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-light-text-primary dark:text-dark-text-primary mb-2">
            {label}
          </label>
        )}
        <input
          ref={ref}
          className={`${baseClasses} ${variantClasses[variant]} ${errorClasses} ${className}`.replace(/\s+/g, ' ').trim()}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-light-danger dark:text-dark-danger">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
