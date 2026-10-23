export type Category = string;
export type Polycount = 'Low' | 'Mid' | 'High';
export type Software = 'Blender' | 'Unreal Engine' | 'Unity' | '3ds Max' | 'Maya';
export type AssetType = 'Model' | 'Material' | 'Kit';
export type FileFormat = '.fbx' | '.obj' | '.blend' | '.gltf' | '.usdc' | '.png' | '.exr' | '.max' | '.ma' | '.tga' | '.uproject' | '.jpg';
export type TextureRes = '2K' | '4K' | '8K';
export type ColorSpace = 'sRGB' | 'Linear';

export interface CategoryDef {
  name: string;
  iconName: string;
}

export interface Asset {
  id: string;
  name: string;
  kitName: string;
  category: Category;
  polycount: Polycount;
  type: AssetType;
  fileFormat: FileFormat;
  filePath: string;
  textureRes: TextureRes;
  vertices: number;
  polygons: number;
  colorSpace: ColorSpace;
  associatedAssetsCount: number;
  targetSoftwareVersion: string;
  fileSizeMB: number;
  thumbnail: string;
  preview: string;
  favorite: boolean;
  imported: boolean;
  dateAdded: string;
  description: string;
  tags: string[];
}

export type ViewMode = 'grid' | 'list';

export type NavSection =
  | 'all'
  | 'kits'
  | 'models'
  | 'materials'
  | 'favorites'
  | 'imported';

export interface LocalFolder {
  id: string;
  path: string;
  assetCount: number;
  lastScanned: string | null;
}
