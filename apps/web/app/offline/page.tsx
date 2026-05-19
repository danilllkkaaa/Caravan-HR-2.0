export default function OfflinePage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <section className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 text-center shadow-card">
        <h1 className="text-lg font-semibold text-slate-900">Нет соединения</h1>
        <p className="mt-2 text-sm text-slate-600">
          Проверьте интернет и повторите попытку. Доступные ранее данные могут открываться из кеша.
        </p>
      </section>
    </main>
  );
}
