"""Small manifests exercise execution independently of the production image gate."""
import hashlib
import json
from pathlib import Path

from PIL import Image

from baseline.protocol import get_prompt


def _write_manifest(path, ids):
    path = Path(path)
    image = path.parent / 'fixture.png'
    Image.new('RGB', (4, 4), 'white').save(image)
    items = [dict(taskId=task, family='matching', groupId='fixture', imageFilename=image.name,
                  imageSha256=hashlib.sha256(image.read_bytes()).hexdigest(),
                  groundTruth={'choice': 'A'}, prompt=get_prompt('matching'),
                  design={'axis': 'hue', 'difficulty': 'wide'}) for task in ids]
    path.write_text(json.dumps(items))
    return path


def _write_config(path):
    model = dict(id='mock-model', provider='openai', model='fixture-model', display_name='Fixture',
                 api_key_env='FIXTURE_API_KEY', source_url='https://example.com/models',
                 input_per_m=1.0, output_per_m=1.0, max_output_tokens=16)
    Path(path).write_text(json.dumps(dict(version=1, verified_at='2026-09-13', models=[model])))
    return path
