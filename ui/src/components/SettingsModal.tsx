import { useState } from 'react';
import {
  X, FolderPlus, FolderOpen, Trash2, RefreshCw, CheckCircle2, HardDrive, Clock,
  Settings, SlidersHorizontal, Globe,
} from 'lucide-react';
import type { LocalFolder } from '@/types';

interface SettingsModalProps {
  open: boolean;
  onClose: () => void;
  folders: LocalFolder[];
  onAddFolder: (path: string) => void;
  onRemoveFolder: (id: string) => void;
  onRescan: (id: string) => void;
  uiScale: number;
  onUiScaleChange: (scale: number) => void;
  language: 'English' | 'Russian';
  onLanguageChange: (lang: 'English' | 'Russian') => void;
}

export default function SettingsModal({
  open, onClose, folders, onAddFolder, onRemoveFolder, onRescan,
  uiScale, onUiScaleChange, language, onLanguageChange,
}: SettingsModalProps) {
  const [newPath, setNewPath] = useState('');
  const [scanning, setScanning] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'folders' | 'appearance'>('folders');

  if (!open) return null;

  const handleAdd = () => {
    if (newPath.trim()) { onAddFolder(newPath.trim()); setNewPath(''); }
  };

  const handleRescan = (id: string) => {
    setScanning(id); onRescan(id); setTimeout(() => setScanning(null), 1500);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-6">
      <div className="absolute inset-0 bg-surface-0/80 backdrop-blur-sm animate-fade-in" onClick={onClose} />

      <div className="relative w-full max-w-lg overflow-hidden border border-surface-400 bg-surface-100 shadow-2xl shadow-black/50 animate-scale-in">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-surface-300 px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center bg-accent/10">
              <Settings className="h-4 w-4 text-accent" />
            </div>
            <h2 className="text-[14px] font-bold text-slate-100">Settings</h2>
          </div>
          <button onClick={onClose} className="flex h-7 w-7 items-center justify-center text-slate-500 transition-colors hover:bg-surface-300 hover:text-slate-200">
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-surface-300">
          <button onClick={() => setActiveTab('folders')} className={`flex items-center gap-1.5 px-4 py-2 text-[12px] font-medium border-b-2 transition-colors ${activeTab === 'folders' ? 'border-accent text-accent' : 'border-transparent text-slate-500 hover:text-slate-300'}`}>
            <FolderOpen className="h-3.5 w-3.5" /> Local Folders
          </button>
          <button onClick={() => setActiveTab('appearance')} className={`flex items-center gap-1.5 px-4 py-2 text-[12px] font-medium border-b-2 transition-colors ${activeTab === 'appearance' ? 'border-accent text-accent' : 'border-transparent text-slate-500 hover:text-slate-300'}`}>
            <SlidersHorizontal className="h-3.5 w-3.5" /> Appearance
          </button>
        </div>

        {activeTab === 'folders' && (
          <>
            {/* Add folder input */}
            <div className="border-b border-surface-300 px-5 py-3.5">
              <label className="mb-1 block text-[10px] font-bold uppercase tracking-wider text-slate-600">Add Local Folder</label>
              <div className="flex gap-1.5">
                <input type="text" value={newPath} onChange={(e) => setNewPath(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleAdd()}
                  placeholder="D:\3D_Assets\My_Pack"
                  className="flex-1 border border-surface-400 bg-surface-200 px-3 py-2 text-[13px] font-mono text-slate-200 placeholder:text-slate-600 focus:border-accent focus:outline-none" />
                <button onClick={handleAdd} disabled={!newPath.trim()}
                  className="flex items-center gap-1.5 bg-accent px-3 py-2 text-[13px] font-bold text-surface-50 transition-colors hover:bg-accent-600 disabled:opacity-40">
                  <FolderPlus className="h-3.5 w-3.5" /> Add
                </button>
              </div>
            </div>

            {/* Folder list */}
            <div className="max-h-56 overflow-y-auto scrollbar-thin px-5 py-2.5">
              {folders.length === 0 ? (
                <div className="py-6 text-center text-[12px] text-slate-600">No folders added yet.</div>
              ) : (
                folders.map((folder) => (
                  <div key={folder.id} className="group mb-1.5 flex items-center gap-3 border border-surface-300 bg-surface-200/50 px-3 py-2.5 transition-colors hover:border-surface-400 hover:bg-surface-200">
                    <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center bg-surface-300">
                      <HardDrive className="h-4 w-4 text-slate-400" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[12px] font-semibold text-slate-200 font-mono">{folder.path}</div>
                      <div className="mt-0.5 flex items-center gap-3 text-[10px] text-slate-500">
                        <span className="flex items-center gap-1"><FolderOpen className="h-2.5 w-2.5" />{folder.assetCount} assets</span>
                        {folder.lastScanned ? (
                          <span className="flex items-center gap-1"><CheckCircle2 className="h-2.5 w-2.5 text-emerald-500" />{folder.lastScanned}</span>
                        ) : (
                          <span className="flex items-center gap-1"><Clock className="h-2.5 w-2.5 text-amber-500" />Not scanned</span>
                        )}
                      </div>
                    </div>
                    <button onClick={() => handleRescan(folder.id)} className="flex h-7 w-7 items-center justify-center text-slate-500 transition-colors hover:bg-surface-400 hover:text-accent" title="Rescan folder">
                      <RefreshCw className={`h-3.5 w-3.5 ${scanning === folder.id ? 'animate-spin' : ''}`} />
                    </button>
                    <button onClick={() => onRemoveFolder(folder.id)} className="flex h-7 w-7 items-center justify-center text-slate-500 transition-colors hover:bg-rose-500/10 hover:text-rose-400" title="Remove folder">
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>

            <div className="border-t border-surface-300 px-5 py-2.5">
              <div className="flex items-center justify-between text-[10px] text-slate-600">
                <span>{folders.length} folder{folders.length !== 1 ? 's' : ''} connected</span>
                <span>Total: {folders.reduce((acc, f) => acc + f.assetCount, 0)} assets indexed</span>
              </div>
            </div>
          </>
        )}

        {activeTab === 'appearance' && (
          <div className="px-5 py-4">
            {/* UI Scale */}
            <div className="mb-5">
              <label className="mb-2 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <SlidersHorizontal className="h-3 w-3" /> UI Scale
              </label>
              <div className="flex items-center gap-3">
                <input type="range" min={80} max={120} step={5} value={uiScale}
                  onChange={(e) => onUiScaleChange(Number(e.target.value))}
                  className="h-1 flex-1 cursor-pointer appearance-none bg-surface-400 accent-accent" />
                <span className="w-10 text-right text-[12px] font-semibold tabular-nums text-slate-300">{uiScale}%</span>
              </div>
              <p className="mt-1 text-[10px] text-slate-600">Adjust the overall interface zoom level</p>
            </div>

            {/* Language */}
            <div className="mb-4">
              <label className="mb-2 flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-slate-500">
                <Globe className="h-3 w-3" /> Language
              </label>
              <div className="flex gap-1">
                {(['English', 'Russian'] as const).map((lang) => (
                  <button key={lang} onClick={() => onLanguageChange(lang)}
                    className={`flex items-center gap-1.5 border px-3 py-1.5 text-[12px] font-medium transition-colors ${language === lang ? 'border-accent/60 bg-accent/10 text-accent' : 'border-surface-400 text-slate-400 hover:border-surface-500 hover:text-slate-200'}`}>
                    {lang}
                  </button>
                ))}
              </div>
              <p className="mt-1 text-[10px] text-slate-600">Mock translation toggle (English / Russian)</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
