'use client';

import { Component, type ReactNode, type ErrorInfo } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
  onError?: (error: Error, errorInfo: ErrorInfo) => void;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('[ErrorBoundary]', error, errorInfo);
    this.props.onError?.(error, errorInfo);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="flex flex-col items-center justify-center gap-4 py-16 px-6 text-center">
          <div className="w-14 h-14 rounded-full bg-danger-100 flex items-center justify-center">
            <AlertTriangle className="w-7 h-7 text-danger-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900 mb-1">
              Что-то пошло не так
            </h3>
            <p className="text-sm text-gray-500 max-w-xs">
              Произошла непредвиденная ошибка. Попробуйте обновить страницу.
            </p>
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <pre className="mt-3 text-left text-xs bg-gray-100 rounded-lg p-3 max-w-sm overflow-auto text-danger-700">
                {this.state.error.message}
              </pre>
            )}
          </div>
          <button
            onClick={this.handleReset}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary-800 text-white text-sm font-medium hover:bg-primary-900 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Попробовать снова
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
