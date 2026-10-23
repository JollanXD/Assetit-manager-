import { useEffect, useState } from 'react';
import { CheckCircle2, X } from 'lucide-react';

export interface ToastData {
  id: number;
  message: string;
  subtitle: string;
}

function Toast({ toast, onDismiss }: { toast: ToastData; onDismiss: () => void }) {
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setLeaving(true);
      setTimeout(onDismiss, 200);
    }, 3500);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      className={`pointer-events-auto flex items-start gap-2.5 border border-emerald-500/30 bg-surface-200 p-3 shadow-xl shadow-black/40 ${
        leaving ? 'animate-fade-in' : 'animate-slide-in-right'
      }`}
      style={leaving ? { animation: 'fadeIn 0.2s ease-out reverse' } : undefined}
    >
      <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center bg-emerald-500/15">
        <CheckCircle2 className="h-4 w-4 text-emerald-400" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-[12px] font-semibold text-slate-100">{toast.message}</p>
        <p className="mt-0.5 text-[10px] text-slate-500">{toast.subtitle}</p>
      </div>
      <button
        onClick={() => { setLeaving(true); setTimeout(onDismiss, 200); }}
        className="flex-shrink-0 text-slate-600 transition-colors hover:text-slate-300"
      >
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export default function ToastContainer({ toasts, onDismiss }: { toasts: ToastData[]; onDismiss: (id: number) => void }) {
  return (
    <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-72 flex-col gap-1.5">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={() => onDismiss(toast.id)} />
      ))}
    </div>
  );
}
