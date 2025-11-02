import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import ErrorBoundary from "@/ErrorBoundary";
import { Toaster } from "sonner";

// Comprehensive ResizeObserver error suppression
const resizeObserverLoopErrRe = /^ResizeObserver loop (completed with undelivered notifications|limit exceeded)/;

// Suppress console errors
const originalError = console.error;
console.error = (...args) => {
  if (typeof args[0] === 'string' && resizeObserverLoopErrRe.test(args[0])) {
    return;
  }
  originalError.call(console, ...args);
};

// Suppress window errors (prevents React error overlay)
window.addEventListener('error', (event) => {
  if (resizeObserverLoopErrRe.test(event.message)) {
    event.stopImmediatePropagation();
    event.preventDefault();
    return true;
  }
});

// Suppress unhandled promise rejections
window.addEventListener('unhandledrejection', (event) => {
  if (event.reason && typeof event.reason.message === 'string' && resizeObserverLoopErrRe.test(event.reason.message)) {
    event.stopImmediatePropagation();
    event.preventDefault();
  }
});

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
      <Toaster position="top-center" richColors />
    </ErrorBoundary>
  </React.StrictMode>,
);
