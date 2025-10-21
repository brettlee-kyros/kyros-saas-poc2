'use client';

import { useEffect, useState } from 'react';

/**
 * Toast Notification System
 *
 * Provides global toast notifications for user feedback.
 * Used for token expiry, session refresh, and other system events.
 *
 * Story 5.3: Token Expiry Handling
 */

type ToastType = 'info' | 'success' | 'warning' | 'error';

interface ToastMessage {
  id: string;
  type: ToastType;
  message: string;
  duration: number;
}

// Global state for toasts
let toasts: ToastMessage[] = [];
let listeners: ((toasts: ToastMessage[]) => void)[] = [];

function notify(newToasts: ToastMessage[]) {
  listeners.forEach(listener => listener(newToasts));
}

function dismiss(id: string) {
  toasts = toasts.filter(t => t.id !== id);
  notify(toasts);
}

/**
 * Global toast API
 *
 * Usage:
 * import { toast } from '@/components/ui/Toast';
 * toast.success('Session refreshed');
 * toast.error('Your session has expired');
 */
export const toast = {
  info: (message: string, duration = 5000) => {
    const id = Date.now().toString() + Math.random();
    const newToast = { id, type: 'info' as ToastType, message, duration };
    toasts = [...toasts, newToast];
    notify(toasts);
    setTimeout(() => dismiss(id), duration);
  },

  success: (message: string, duration = 5000) => {
    const id = Date.now().toString() + Math.random();
    const newToast = { id, type: 'success' as ToastType, message, duration };
    toasts = [...toasts, newToast];
    notify(toasts);
    setTimeout(() => dismiss(id), duration);
  },

  warning: (message: string, duration = 5000) => {
    const id = Date.now().toString() + Math.random();
    const newToast = { id, type: 'warning' as ToastType, message, duration };
    toasts = [...toasts, newToast];
    notify(toasts);
    setTimeout(() => dismiss(id), duration);
  },

  error: (message: string, duration = 5000) => {
    const id = Date.now().toString() + Math.random();
    const newToast = { id, type: 'error' as ToastType, message, duration };
    toasts = [...toasts, newToast];
    notify(toasts);
    setTimeout(() => dismiss(id), duration);
  },
};

/**
 * Toast Container Component
 *
 * Add this to root layout to display toasts globally.
 */
export function ToastContainer() {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  useEffect(() => {
    listeners.push(setMessages);
    return () => {
      listeners = listeners.filter(l => l !== setMessages);
    };
  }, []);

  const getToastStyles = (type: ToastType): string => {
    const baseStyles = 'mb-3 px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in';

    switch (type) {
      case 'info':
        return `${baseStyles} bg-blue-600 text-white`;
      case 'success':
        return `${baseStyles} bg-green-600 text-white`;
      case 'warning':
        return `${baseStyles} bg-yellow-500 text-gray-900`;
      case 'error':
        return `${baseStyles} bg-red-600 text-white`;
      default:
        return `${baseStyles} bg-gray-800 text-white`;
    }
  };

  const getIcon = (type: ToastType): string => {
    switch (type) {
      case 'info':
        return 'ℹ️';
      case 'success':
        return '✓';
      case 'warning':
        return '⚠️';
      case 'error':
        return '✕';
      default:
        return '';
    }
  };

  if (messages.length === 0) {
    return null;
  }

  return (
    <div className="fixed top-20 right-4 z-50 max-w-md">
      {messages.map((toastMsg) => (
        <div key={toastMsg.id} className={getToastStyles(toastMsg.type)}>
          <span className="text-xl">{getIcon(toastMsg.type)}</span>
          <p className="flex-1 font-medium">{toastMsg.message}</p>
          <button
            onClick={() => dismiss(toastMsg.id)}
            className="text-white hover:opacity-75 transition-opacity"
            aria-label="Dismiss notification"
          >
            ✕
          </button>
        </div>
      ))}
    </div>
  );
}
