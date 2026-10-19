"""Prevent accidental Nano fallback after the production engine change."""
import json
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from studio.voice import load_model, MODEL_REVISIONS


class TurboTests(unittest.TestCase):
    def test_default_loads_turbo_and_rejects_nano_only_directory(self):
        backend=MagicMock()
        module=types.ModuleType('chatterbox.tts_turbo');module.ChatterboxTurboTTS=backend
        with tempfile.TemporaryDirectory() as directory, patch.dict('sys.modules',{
                'torch':MagicMock(),'chatterbox':types.ModuleType('chatterbox'),
                'chatterbox.tts_turbo':module}):
            root=Path(directory);(root/'t3_nano_v1.safetensors').touch()
            with self.assertRaisesRegex(ValueError,'no fallback model'):
                load_model(model_dir=root)
            backend.from_local.assert_not_called()
            (root/'t3_turbo_v1.safetensors').touch()
            load_model(model_dir=root)
            backend.from_local.assert_called_once_with(root,device='cpu',nano=False)
            backend.from_pretrained.assert_not_called()

    def test_production_profiles_use_turbo_with_conditioning_provenance(self):
        root=Path(__file__).resolve().parents[1]/'voices'
        for relative in json.loads((root/'cast-profiles.json').read_text()).values():
            metadata=json.loads((root/relative/'profile.json').read_text())
            self.assertEqual(metadata['variant'],'turbo')
            self.assertEqual(metadata['model_revision'],MODEL_REVISIONS['turbo'])
            self.assertEqual(metadata['conditioning_origin_variant'],'nano')
