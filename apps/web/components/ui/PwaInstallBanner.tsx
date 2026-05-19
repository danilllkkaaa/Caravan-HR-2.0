'use client';

import { useEffect, useState } from 'react';
import { X, Download, Share } from 'lucide-react';

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>;
}

function isIos(): boolean {
  if (typeof navigator === 'undefined') return false;
  return /iphone|ipad|ipod/i.test(navigator.userAgent);
}

function isInStandaloneMode(): boolean {
  if (typeof window === 'undefined') return false;
  return (
    window.matchMedia('(display-mode: standalone)').matches ||
    ('standalone' in window.navigator && (window.navigator as { standalone?: boolean }).standalone === true)
  );
}

const DISMISSED_KEY = 'pwa_install_dismissed';

export function PwaInstallBanner() {
  const [show, setShow] = useState(false);
  const [isIosDevice, setIsIosDevice] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<BeforeInstallPromptEvent | null>(null);
  const [installing, setInstalling] = useState(false);

  useEffect(() => {
    // Don't show if already installed or previously dismissed
    if (isInStandaloneMode()) return;
    if (sessionStorage.getItem(DISMISSED_KEY)) return;

    const ios = isIos();
    setIsIosDevice(ios);

    if (ios) {
      // iOS: show manual instructions after a short delay
      const timer = setTimeout(() => setShow(true), 3000);
      return () => clearTimeout(timer);
    }

    // Android/Chrome: listen for the install prompt
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e as BeforeInstallPromptEvent);
      setShow(true);
    };
    window.addEventListener('beforeinstallprompt', handler);
    return () => window.removeEventListener('beforeinstallprompt', handler);
  }, []);

  const dismiss = () => {
    setShow(false);
    sessionStorage.setItem(DISMISSED_KEY, '1');
  };

  const handleInstall = async () => {
    if (!deferredPrompt) return;
    setInstalling(true);
    await deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setShow(false);
    }
    setDeferredPrompt(null);
    setInstalling(false);
  };

  if (!show) return null;

  return (
    <div className="fixed bottom-[calc(3.5rem+env(safe-area-inset-bottom,0px)+8px)] left-3 right-3 z-20 md:hidden">
      <div className="bg-primary-800 text-white rounded-2xl px-4 py-3.5 shadow-modal flex items-start gap-3">
        <div className="flex-shrink-0 w-8 h-8 rounded-xl bg-white/20 flex items-center justify-center mt-0.5">
          {isIosDevice ? (
            <Share className="w-4 h-4 text-white" />
          ) : (
            <Download className="w-4 h-4 text-white" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <p className="text-sm font-semibold leading-tight">
            Добавить на экран Домой
          </p>
          {isIosDevice ? (
            <p className="text-xs text-white/80 mt-0.5 leading-relaxed">
              Нажмите{' '}
              <span className="inline-flex items-center gap-0.5 font-medium">
                <Share className="w-3 h-3 inline" /> «Поделиться»
              </span>{' '}
              → «На экран Домой» — и приложение появится без магазина.
            </p>
          ) : (
            <p className="text-xs text-white/80 mt-0.5">
              Установите как приложение — работает без браузера и интернета.
            </p>
          )}

          {!isIosDevice && deferredPrompt && (
            <button
              onClick={handleInstall}
              disabled={installing}
              className="mt-2 px-3 py-1.5 bg-white text-primary-800 text-xs font-semibold rounded-xl hover:bg-gray-100 transition-colors disabled:opacity-60"
            >
              {installing ? 'Установка…' : 'Установить'}
            </button>
          )}
        </div>

        <button
          onClick={dismiss}
          className="flex-shrink-0 p-1 rounded-lg hover:bg-white/20 transition-colors"
        >
          <X className="w-4 h-4 text-white/80" />
        </button>
      </div>
    </div>
  );
}
