import type { Asset, ViewMode } from '@/types';
import AssetCard from './AssetCard';

interface AssetGridProps {
  assets: Asset[];
  viewMode: ViewMode;
  selectedAssetId: string | null;
  onSelect: (asset: Asset) => void;
  onQuickImport: (asset: Asset) => void;
  onToggleFavorite: (asset: Asset) => void;
  thumbnailSize: number;
  onThumbnailSizeChange: (size: number) => void;
}

export default function AssetGrid({
  assets, viewMode, selectedAssetId, onSelect, onQuickImport, onToggleFavorite,
  thumbnailSize, onThumbnailSizeChange,
}: AssetGridProps) {
  if (assets.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center text-slate-600">
        <div className="flex h-16 w-16 items-center justify-center border border-surface-400 bg-surface-200">
          <svg className="h-8 w-8 text-slate-700" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
          </svg>
        </div>
        <p className="mt-3 text-[13px] font-medium text-slate-400">No assets found</p>
        <p className="mt-0.5 text-[11px] text-slate-600">Try adjusting your filters or search query</p>
      </div>
    );
  }

  // Map slider value (0-100) to grid columns
  const cols = viewMode === 'list' ? 1 : Math.max(2, Math.round(12 - (thumbnailSize / 100) * 10));

  return (
    <div className="flex h-full flex-col">
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {viewMode === 'list' ? (
          <div className="flex flex-col p-2">
            <div className="flex items-center gap-3 px-3 pb-1.5 text-[9px] font-bold uppercase tracking-wider text-slate-600 border-b border-surface-300">
              <span className="w-16 flex-shrink-0">Thumb</span>
              <span className="flex-1">Name</span>
              <span className="hidden md:block w-24">Category</span>
              <span className="hidden lg:block w-20">Type</span>
              <span className="hidden xl:block w-14 text-center">Format</span>
              <span className="hidden xl:block w-14 text-right">Size</span>
              <span className="w-16" />
            </div>
            <div className="mt-1 flex flex-col gap-px">
              {assets.map((asset) => (
                <AssetCard key={asset.id} asset={asset} viewMode="list" isSelected={selectedAssetId === asset.id}
                  onSelect={onSelect} onQuickImport={onQuickImport} onToggleFavorite={onToggleFavorite} />
              ))}
            </div>
          </div>
        ) : (
          <div className="grid gap-1 p-1.5" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
            {assets.map((asset) => (
              <AssetCard key={asset.id} asset={asset} viewMode="grid" isSelected={selectedAssetId === asset.id}
                onSelect={onSelect} onQuickImport={onQuickImport} onToggleFavorite={onToggleFavorite} />
            ))}
          </div>
        )}
      </div>

      {/* Thumbnail size slider */}
      {viewMode === 'grid' && (
        <div className="flex items-center gap-3 border-t border-surface-300 bg-surface-100 px-4 py-1.5">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-600">Thumb Size</span>
          <input type="range" min={0} max={100} value={thumbnailSize}
            onChange={(e) => onThumbnailSizeChange(Number(e.target.value))}
            className="h-1 flex-1 max-w-xs cursor-pointer appearance-none bg-surface-400 accent-accent" />
          <span className="text-[10px] tabular-nums text-slate-500">{cols} cols</span>
        </div>
      )}
    </div>
  );
}
