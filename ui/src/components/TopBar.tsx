import { Search, LayoutGrid, List, FolderOpen, SlidersHorizontal } from 'lucide-react';
import type { ViewMode } from '@/types';

interface TopBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  viewMode: ViewMode;
  onViewModeChange: (mode: ViewMode) => void;
  resultCount: number;
  totalCount: number;
  hasActiveFilters: boolean;
  activeNavLabel: string;
}

export default function TopBar({
  search, onSearchChange, viewMode, onViewModeChange,
  resultCount, totalCount, hasActiveFilters, activeNavLabel,
}: TopBarProps) {
  return (
    <header className="flex items-center gap-4 border-b border-surface-300 bg-surface-100 px-5 py-2.5">
      <div className="flex items-center gap-2.5">
        <h1 className="text-[14px] font-bold text-slate-100">{activeNavLabel}</h1>
        <span className="flex items-center gap-1 text-[12px] text-slate-500">
          <span className="font-semibold text-slate-300">{resultCount}</span>
          <span>/</span>
          <span className="tabular-nums">{totalCount}</span>
          {hasActiveFilters && (
            <span className="ml-1.5 flex items-center gap-1 bg-accent/10 px-1.5 py-0.5 text-[9px] font-semibold text-accent">
              <SlidersHorizontal className="h-2 w-2" /> FILTERED
            </span>
          )}
        </span>
      </div>

      <div className="relative ml-2 max-w-xs">
        <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-600" />
        <input type="text" value={search} onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Search local files..."
          className="w-full border border-surface-400 bg-surface-200 py-1.5 pl-8 pr-8 text-[13px] text-slate-200 placeholder:text-slate-600 focus:border-accent focus:outline-none" />
        {search && (
          <button onClick={() => onSearchChange('')} className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-300 transition-colors">
            <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        )}
      </div>

      <div className="flex-1" />

      <div className="flex items-center border border-surface-400">
        <button onClick={() => onViewModeChange('grid')} className={`flex items-center gap-1 px-2 py-1.5 text-[12px] font-medium transition-colors ${viewMode === 'grid' ? 'bg-surface-400 text-slate-100' : 'text-slate-500 hover:text-slate-300'}`}>
          <LayoutGrid className="h-3.5 w-3.5" />
        </button>
        <div className="w-px h-5 bg-surface-300" />
        <button onClick={() => onViewModeChange('list')} className={`flex items-center gap-1 px-2 py-1.5 text-[12px] font-medium transition-colors ${viewMode === 'list' ? 'bg-surface-400 text-slate-100' : 'text-slate-500 hover:text-slate-300'}`}>
          <List className="h-3.5 w-3.5" />
        </button>
      </div>
    </header>
  );
}
