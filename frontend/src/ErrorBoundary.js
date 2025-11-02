import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    // Check if this is a ResizeObserver error
    const resizeObserverErrRe = /ResizeObserver loop (completed with undelivered notifications|limit exceeded)/;
    
    if (error && error.message && resizeObserverErrRe.test(error.message)) {
      // Suppress ResizeObserver errors
      return { hasError: false };
    }
    
    // For other errors, show error UI
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    const resizeObserverErrRe = /ResizeObserver loop (completed with undelivered notifications|limit exceeded)/;
    
    // Only log non-ResizeObserver errors
    if (!resizeObserverErrRe.test(error.message)) {
      console.error('Error caught by boundary:', error, errorInfo);
    }
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          padding: '2rem',
          textAlign: 'center'
        }}>
          <h1 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Something went wrong</h1>
          <p style={{ marginBottom: '1rem' }}>Please refresh the page to continue.</p>
          <button 
            onClick={() => window.location.reload()}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: '#000',
              color: '#fff',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            Refresh Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
