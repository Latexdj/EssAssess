"use client";
import { Component, type ReactNode, type ErrorInfo } from "react";

interface Props {
  children:  ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  message:  string;
}

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, message: "" };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, message: error.message };
  }

  componentDidCatch(_error: Error, info: ErrorInfo) {
    console.error("ErrorBoundary caught:", info.componentStack);
  }

  reset = () => this.setState({ hasError: false, message: "" });

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback;
      return (
        <div className="flex flex-col items-center justify-center gap-4 py-16 text-center">
          <div className="text-4xl">⚠</div>
          <h2 className="text-lg font-semibold text-gray-800">
            Something went wrong
          </h2>
          {this.state.message && (
            <p className="text-sm text-gray-500 max-w-sm">{this.state.message}</p>
          )}
          <button
            onClick={this.reset}
            className="mt-2 rounded-lg bg-blue-700 px-5 py-3 text-sm font-semibold text-white hover:bg-blue-800 min-h-[44px]"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
