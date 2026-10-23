import { Star, Download, Layers, Package, Palette } from 'lucide-react';
import type { Asset, ViewMode } from '@/types';
import { iconRegistry } from '@/lib/nav';

interface AssetCardProps {
  asset: Asset;
  viewMode: ViewMode;
  isSelected: boolean;
  onSelect: (asset: Asset) => void;
  onQuickImport: (asset: Asset) => void;
  onToggleFavorite: (asset: Asset) => void;
}

const typeIcons = { Kit: Layers, Model: Package, Material: Palette };

export default function AssetCard({ asset, viewMode, isSelected, onSelect, onQuickImport, onToggleFavorite }: AssetCardProps) {
  const CatIcon = iconRegistry[asset.category] ?? Layers;
  const TypeIcon = typeIcons[asset.type];

  if (viewMode === 'list') {
    return (
      <div onClick={() => onSelect(asset)}
        className={`group flex cursor-pointer items-center gap-3 border-l-2 px-3 py-2 transition-colors ${isSelected ? 'border-l-accent bg-accent/5' : 'border-l-transparent hover:bg-surface-200'}`}>
        <div className="relative h-12 w-16 flex-shrink-0 overflow-hidden bg-surface-200">
          <img src={asset.thumbnail} alt={asset.name} loading="lazy" className="h-full w-full object-cover" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate text-[13px] font-medium text-slate-200">{asset.name}</span>
            <button onClick={(e) => { e.stopPropagation(); onToggleFavorite(asset); }} className="flex-shrink-0">
              <Star className={`h-3 w-3 transition-colors ${asset.favorite ? 'fill-amber-400 text-amber-400' : 'text-slate-600 hover:text-slate-400'}`} />
            </button>
          </div>
          <div className="truncate text-[11px] text-slate-500">{asset.kitName}</div>
          <div className="mt-0.5 flex gap-1">
            {asset.tags.slice(0, 3).map((tag) => (
              <span key={tag} className="flex-shrink-0 bg-surface-300 px-1.5 py-px text-[9px] font-medium text-slate-500">{tag}</span>
            ))}
          </div>
        </div>
        <div className="hidden md:flex items-center gap-1.5 w-24"><CatIcon className="h-3 w-3 text-slate-500" /><span className="text-[12px] text-slate-400">{asset.category}</span></div>
        <div className="hidden lg:flex items-center gap-1.5 w-20"><TypeIcon className="h-3 w-3 text-slate-500" /><span className="text-[12px] text-slate-400">{asset.type}</span></div>
        <div className="hidden xl:block w-14 text-center text-[11px] font-mono text-slate-500">{asset.fileFormat}</div>
        <div className="hidden xl:block w-14 text-right text-[11px] tabular-nums text-slate-500">{asset.fileSizeMB.toFixed(0)}MB</div>
        <button onClick={(e) => { e.stopPropagation(); onQuickImport(asset); }} className="flex flex-shrink-0 items-center gap-1 bg-accent/10 px-2.5 py-1 text-[11px] font-semibold text-accent opacity-0 transition-opacity hover:bg-accent/20 group-hover:opacity-100">
          <Download className="h-3 w-3" /> Import
        </button>
      </div>
    );
  }

  return (
    <div onClick={() => onSelect(asset)}
      className={`group relative cursor-pointer overflow-hidden border transition-colors ${isSelected ? 'border-accent' : 'border-surface-300 hover:border-surface-500'}`}>
      <div className="relative aspect-[4/3] overflow-hidden bg-surface-200">
        <img src={asset.thumbnail} alt={asset.name} loading="lazy" className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105" />
        <div className="absolute left-0 top-0">
          <span className="flex items-center gap-1 bg-surface-0/80 px-1.5 py-0.5 text-[9px] font-semibold text-slate-200 backdrop-blur-sm"><CatIcon className="h-2.5 w-2.5" />{asset.category}</span>
        </div>
        <button onClick={(e) => { e.stopPropagation(); onToggleFavorite(asset); }} className="absolute right-0 top-0 flex h-6 w-6 items-center justify-center bg-surface-0/70 backdrop-blur-sm transition-colors hover:bg-surface-0/90">
          <Star className={`h-3 w-3 transition-colors ${asset.favorite ? 'fill-amber-400 text-amber-400' : 'text-slate-400'}`} />
        </button>
        <div className="absolute bottom-0 right-0">
          <span className="flex items-center gap-0.5 bg-surface-0/80 px-1.5 py-0.5 text-[9px] font-medium text-slate-300 backdrop-blur-sm"><TypeIcon className="h-2.5 w-2.5" />{asset.type}</span>
        </div>
        {/* Hover info overlay */}
        <div className="absolute inset-0 flex flex-col justify-end bg-gradient-to-t from-surface-0/90 via-transparent to-transparent opacity-0 transition-opacity group-hover:opacity-100">
          <div className="px-2 pb-2">
            <div className="flex items-center justify-between gap-1 mb-1.5">
              <span className="text-[10px] font-mono text-slate-300">{asset.fileFormat}</span>
              <span className="text-[10px] tabular-nums text-slate-400">{asset.fileSizeMB.toFixed(0)} MB</span>
            </div>
            <button onClick={(e) => { e.stopPropagation(); onQuickImport(asset); }} className="flex w-full items-center justify-center gap-1.5 bg-accent py-1.5 text-[11px] font-bold text-surface-50 transition-colors hover:bg-accent-600">
              <Download className="h-3 w-3" /> Quick Import
            </button>
          </div>
        </div>
      </div>
      <div className="px-2 py-1.5">
        <div className="flex items-center justify-between gap-2">
          <h3 className="truncate text-[12px] font-semibold text-slate-200">{asset.name}</h3>
          <span className="flex-shrink-0 text-[9px] font-mono text-slate-600">{asset.fileFormat}</span>
        </div>
        <p className="truncate text-[10px] text-slate-500">{asset.kitName}</p>
        <div className="mt-1 flex flex-wrap gap-0.5">
          {asset.tags.slice(0, 3).map((tag) => (
            <span key={tag} className="flex items-center gap-0.5 bg-surface-300 px-1 py-px text-[8px] font-medium text-slate-500">
              <span className={`h-0.5 w-0.5 rounded-full ${tag.includes('poly') ? 'bg-accent' : 'bg-slate-600'}`} />{tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
