import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Вход в систему',
};

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-900 via-primary-800 to-primary-700 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo / App name */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-white/10 backdrop-blur-sm mb-4">
            <svg
              className="w-8 h-8 text-white"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-white">Корпоративный портал</h1>
          <p className="text-primary-300 text-sm mt-1">HR-система компании</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-modal p-8">{children}</div>

        <p className="text-center text-primary-400 text-xs mt-6">
          © {new Date().getFullYear()} Корпоративный портал. Все права защищены.
        </p>
      </div>
    </div>
  );
}
