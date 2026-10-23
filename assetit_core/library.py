"""Local asset discovery primitives; source files are never modified."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tif', '.tiff', '.exr', '.hdr', '.tx'}
MODEL_EXTS = {'.fbx', '.obj', '.abc', '.usd', '.usda', '.usdc', '.glb', '.gltf', '.stl', '.ply', '.vdb'}
PROJECT_EXTS = {'.ma', '.mb', '.blend', '.c4d', '.hip', '.hiplc', '.max', '.3ds', '.ztl'}
ASSET_EXTS = IMAGE_EXTS | MODEL_EXTS | PROJECT_EXTS

@dataclass(frozen=True, slots=True)
class AssetRecord:
    path: str
    name: str
    extension: str
    asset_type: str
    size_bytes: int
    modified_utc: str
    library_root: str
    def to_dict(self):
        return asdict(self)

class LibraryService:
    """Discover supported assets inside explicitly selected local folders."""
    def __init__(self, supported_extensions: Iterable[str] | None = None):
        self.supported_extensions = {str(ext).lower() if str(ext).startswith('.') else f'.{str(ext).lower()}' for ext in (supported_extensions or ASSET_EXTS)}

    def validate_root(self, root: str | Path) -> Path:
        path = Path(root).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f'Library folder does not exist: {path}')
        if not path.is_dir():
            raise NotADirectoryError(f'Library path is not a folder: {path}')
        return path

    def scan(self, root: str | Path, *, recursive: bool = True) -> list[AssetRecord]:
        library_root = self.validate_root(root)
        iterator = library_root.rglob('*') if recursive else library_root.iterdir()
        records = []
        for path in iterator:
            try:
                if not path.is_file() or path.suffix.lower() not in self.supported_extensions:
                    continue
                stat = path.stat()
                ext = path.suffix.lower()
                kind = 'Texture' if ext in IMAGE_EXTS else 'Model' if ext in MODEL_EXTS else 'Project'
                records.append(AssetRecord(str(path.resolve()), path.stem, ext, kind, stat.st_size, datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(timespec='seconds'), str(library_root)))
            except OSError:
                continue
        records.sort(key=lambda item: (item.name.casefold(), item.path.casefold()))
        return records
