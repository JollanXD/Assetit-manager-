import tempfile
import unittest
from pathlib import Path
from assetit_core import LibraryService, SettingsStore

class CoreTests(unittest.TestCase):
    def test_settings_are_persisted_and_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            store = SettingsStore(Path(temp) / 'settings.json')
            value = store.load()
            value['libraries'] = ['C:/Assets', 7, None]
            value['thumbnail_size'] = 9999
            store.save(value)
            loaded = store.load()
            self.assertEqual(loaded['libraries'], ['C:/Assets', '7'])
            self.assertEqual(loaded['thumbnail_size'], 512)

    def test_scan_finds_supported_files_and_leaves_them_untouched(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            model = root / 'rock.FBX'
            model.write_bytes(b'asset')
            (root / 'readme.txt').write_text('ignore', encoding='utf-8')
            records = LibraryService().scan(root)
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].asset_type, 'Model')
            self.assertEqual(model.read_bytes(), b'asset')

if __name__ == '__main__':
    unittest.main()
