import { forwardRef } from 'react';
import { clsx } from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  leftIcon?: React.ReactNode;
  rightElement?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, helperText, leftIcon, rightElement, className, id, ...props }, ref) => {
    const inputId = id ?? label?.toLowerCase().replace(/\s+/g, '-');
    const hasError = !!error;

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-gray-700 mb-1.5"
          >
            {label}
            {props.required && <span className="text-danger-500 ml-0.5">*</span>}
          </label>
        )}

        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            className={clsx(
              'w-full px-3.5 py-2.5 text-sm rounded-xl border outline-none transition-colors',
              'placeholder:text-gray-400',
              'focus:ring-2',
              hasError
                ? 'border-danger-500 bg-danger-50 focus:ring-danger-300 focus:border-danger-500 text-danger-900'
                : 'border-gray-300 bg-white hover:border-gray-400 focus:ring-accent-300 focus:border-accent-500',
              'disabled:bg-gray-50 disabled:text-gray-400 disabled:cursor-not-allowed',
              leftIcon && 'pl-9',
              rightElement && 'pr-10',
              className
            )}
            {...props}
          />
          {rightElement && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2">{rightElement}</div>
          )}
        </div>

        {(error || helperText) && (
          <p
            className={clsx(
              'mt-1.5 text-xs',
              hasError ? 'text-danger-600' : 'text-gray-500'
            )}
          >
            {error ?? helperText}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
