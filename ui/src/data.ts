import type { Asset, LocalFolder } from './types';

// Pexels image URLs gathered for each category
const sciFi = [
  'https://images.pexels.com/photos/18337612/pexels-photo-18337612.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/12843337/pexels-photo-12843337.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/18337624/pexels-photo-18337624.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/26545220/pexels-photo-26545220.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
];

const cyberpunk = [
  'https://images.pexels.com/photos/12187128/pexels-photo-12187128.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/18545010/pexels-photo-18545010.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/18545016/pexels-photo-18545016.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/18545011/pexels-photo-18545011.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
];

const fantasy = [
  'https://images.pexels.com/photos/1006107/pexels-photo-1006107.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/10722323/pexels-photo-10722323.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/31473120/pexels-photo-31473120.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/33425253/pexels-photo-33425253.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
];

const industrial = [
  'https://images.pexels.com/photos/40132857/pexels-photo-40132857.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/26969628/pexels-photo-26969628.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/7598915/pexels-photo-7598915.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/36736681/pexels-photo-36736681.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
];

const modern = [
  'https://images.pexels.com/photos/8657160/pexels-photo-8657160.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/12977017/pexels-photo-12977017.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/29791458/pexels-photo-29791458.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/28494626/pexels-photo-28494626.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
];

const textures = [
  'https://images.pexels.com/photos/11605087/pexels-photo-11605087.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/6066072/pexels-photo-6066072.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/34054451/pexels-photo-34054451.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
  'https://images.pexels.com/photos/6560286/pexels-photo-6560286.jpeg?auto=compress&cs=tinysrgb&h=650&w=940',
];

const catImages: Record<string, string[]> = {
  'Sci-Fi': sciFi,
  Cyberpunk: cyberpunk,
  Fantasy: fantasy,
  Industrial: industrial,
  Modern: modern,
};

const polycounts = ['Low', 'Mid', 'High'] as const;
const formats = ['.fbx', '.obj', '.blend', '.gltf', '.max'] as const;
const texRes = ['2K', '4K', '8K'] as const;
const fileSizes = [12.4, 45.8, 128.3, 8.2, 67.5, 234.1, 89.6, 15.3, 56.7, 312.8];

const kitNames = [
  'Neo Tokyo District',
  'Deep Space Station',
  'Medieval Kingdom',
  'Cyber Slums',
  'Factory Complex',
  'Modern Cityscape',
  'Orbital Platform',
  'Gothic Cathedral',
  'Industrial Pipeline',
  'Quantum Lab',
  'Ancient Ruins',
  'Mars Colony',
];

const assetNames = [
  'Tower Spire A',
  'Modular Wall Panel',
  'Console Terminal',
  'Street Light Array',
  'Catwalk Section',
  'Support Beam',
  'Door Frame Arch',
  'Antenna Mast',
  'Storage Crate',
  'Holographic Display',
  'Pipe Junction',
  'Generator Unit',
  'Window Module',
  'Rooftop Unit',
  'Bridge Segment',
  'Platform Grate',
  'Ventilation Shaft',
  'Staircase Module',
  'Landing Pad',
  'Reactor Core',
  'Stone Wall Block',
  'Castle Keep',
  'Gate House',
  'Watchtower',
  'Concrete Slab',
  'Glass Facade',
  'Marble Column',
  'Steel Girder',
  'Brick Texture Set',
  'Concrete PBR Pack',
  'Rusted Metal Set',
  'Marble Tile PBR',
];

const tagPool = [
  'modular', 'PBR', 'rigged', 'animated', 'destructible', 'interior',
  'exterior', 'hero prop', 'environment', 'vehicle', 'character', 'weapon',
  'low-poly', 'mid-poly', 'high-poly',
];

let idCounter = 0;

function pick<T>(arr: readonly T[], i: number): T {
  return arr[i % arr.length];
}

function makeAsset(
  name: string,
  category: Asset['category'],
  type: Asset['type'],
  imgIndex: number,
  kitIndex: number,
): Asset {
  idCounter++;
  const imgSource = type === 'Material' ? textures : catImages[category] || sciFi;
  const img = pick(imgSource, imgIndex);
  return {
    id: `asset-${idCounter}`,
    name,
    kitName: pick(kitNames, kitIndex),
    category,
    polycount: pick(polycounts, imgIndex + idCounter),
    type,
    fileFormat: type === 'Material' ? '.png' : pick(formats, idCounter),
    filePath: `${pick(['D:\\3D_Assets\\Kitbash', 'C:\\Models\\SciFi', 'E:\\Projects\\Assets', 'D:\\3D_Library\\Kits'], idCounter)}\\${name.replace(/\s+/g, '_').toLowerCase()}${type === 'Material' ? '.png' : pick(formats, idCounter)}`,
    textureRes: pick(texRes, idCounter + 3),
    vertices: pick([1200, 8400, 24500, 68000, 120000, 3500, 16000, 92000], idCounter),
    polygons: pick([2400, 16800, 49200, 136000, 240000, 7000, 32000, 184000], idCounter),
    colorSpace: pick(['sRGB', 'Linear'] as const, idCounter),
    associatedAssetsCount: pick([12, 28, 45, 67, 8, 33, 54, 19], idCounter),
    targetSoftwareVersion: pick(['Blender 4.2', 'UE 5.4', 'Maya 2025', 'Unity 2023 LTS', '3ds Max 2025'], idCounter),
    fileSizeMB: pick(fileSizes, idCounter),
    thumbnail: img,
    preview: img,
    favorite: idCounter % 7 === 0,
    imported: idCounter % 5 === 0,
    dateAdded: new Date(2024, (idCounter % 12), ((idCounter * 3) % 27) + 1).toISOString(),
    description: `High-quality ${type.toLowerCase()} asset from the ${pick(kitNames, kitIndex)} collection. Fully PBR-textured, game-ready, and optimized for real-time rendering across all major DCC tools.`,
    tags: [pick(tagPool, idCounter), pick(tagPool, idCounter + 3), pick(tagPool, idCounter + 7), `${pick(polycounts, imgIndex + idCounter).toLowerCase()}-poly`],
  };
}

export const assets: Asset[] = (() => {
  const list: Asset[] = [];
  let imgI = 0;
  let kitI = 0;

  for (const name of assetNames) {
    const categories: Asset['category'][] = ['Sci-Fi', 'Cyberpunk', 'Fantasy', 'Industrial', 'Modular', 'Modern'];
    const category = pick(categories, imgI);
    const type: Asset['type'] = imgI % 4 === 3 ? 'Material' : imgI % 3 === 0 ? 'Kit' : 'Model';
    list.push(makeAsset(name, category, type, imgI, kitI));
    imgI++;
    kitI = Math.floor(imgI / 3);
  }
  return list;
})();

export const localFolders: LocalFolder[] = [
  { id: 'f1', path: 'D:\\3D_Assets\\Kitbash', assetCount: 142, lastScanned: '2026-10-22' },
  { id: 'f2', path: 'C:\\Models\\SciFi', assetCount: 89, lastScanned: '2026-10-20' },
  { id: 'f3', path: 'E:\\Projects\\Texture_Library', assetCount: 34, lastScanned: null },
];

export const softwareVersions: Record<string, string[]> = {
  Blender: ['Blender 4.2', 'Blender 4.1', 'Blender 3.6'],
  'Unreal Engine': ['UE 5.4', 'UE 5.3', 'UE 5.2'],
  Unity: ['Unity 2023 LTS', 'Unity 2022 LTS'],
  '3ds Max': ['3ds Max 2025', '3ds Max 2024'],
  Maya: ['Maya 2025', 'Maya 2024'],
};
