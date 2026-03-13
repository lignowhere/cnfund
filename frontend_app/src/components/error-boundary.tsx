"use client";

import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = { children: ReactNode; fallback?: ReactNode };
type State = { hasError: boolean; error: Error | null };

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("[ErrorBoundary]", error, info.componentStack);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex min-h-[50vh] flex-col items-center justify-center gap-4 p-6 text-center">
          <h2 className="text-lg font-semibold text-[var(--color-danger-text)]">
            Đã xảy ra lỗi
          </h2>
          <p className="text-sm text-[var(--color-muted)]">
            {this.state.error?.message || "Lỗi không xác định"}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="rounded-lg bg-[var(--color-primary)] px-4 py-2 text-sm text-white"
          >
            Thử lại
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
