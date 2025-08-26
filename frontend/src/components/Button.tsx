import type { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  isLoading?: boolean;
  children: ReactNode;
}

export function Button({ 
  variant = 'primary', 
  size = 'md', 
  isLoading = false, 
  disabled,
  children, 
  className = '', 
  ...props 
}: ButtonProps) {
  const baseClasses = `
    inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 
    focus:outline-none focus:ring-2 focus:ring-offset-2 dark:focus:ring-offset-dark-bg
    disabled:opacity-50 disabled:cursor-not-allowed
  `;

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const variantClasses = {
    primary: `
      bg-light-accent dark:bg-dark-accent text-white
      hover:bg-blue-700 dark:hover:bg-blue-600
      focus:ring-light-accent dark:focus:ring-dark-accent
      shadow-sm hover:shadow-md
    `,
    secondary: `
      bg-light-text-secondary dark:bg-dark-text-secondary text-white
      hover:bg-gray-600 dark:hover:bg-gray-400
      focus:ring-light-text-secondary dark:focus:ring-dark-text-secondary
      shadow-sm hover:shadow-md
    `,
    outline: `
      border-2 border-light-accent dark:border-dark-accent
      text-light-accent dark:text-dark-accent bg-transparent
      hover:bg-light-accent hover:text-white
      dark:hover:bg-dark-accent dark:hover:text-white
      focus:ring-light-accent dark:focus:ring-dark-accent
    `,
    ghost: `
      text-light-text-primary dark:text-dark-text-primary bg-transparent
      hover:bg-gray-100 dark:hover:bg-gray-800
      focus:ring-gray-300 dark:focus:ring-gray-600
    `,
  };

  const isDisabled = disabled || isLoading;

  return (
    <button
      className={`${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${className}`.replace(/\s+/g, ' ').trim()}
      disabled={isDisabled}
      {...props}
    >
      {isLoading && (
        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-current" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {children}
    </button>
  );
}
