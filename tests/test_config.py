import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from id_preservation_cg.config import load_generation_request


class ConfigTest(unittest.TestCase):
    def test_load_generation_request_json(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            config = tmp_path / "request.json"
            config.write_text(
                json.dumps(
                    {
                        "fan_refs": ["fan.jpg"],
                        "celebrity_refs": ["star.jpg"],
                        "output_path": str(tmp_path / "out.svg"),
                        "controls": {"use_style_lora": True},
                        "model": {"backend": "mock", "seed": 7},
                    }
                ),
                encoding="utf-8",
            )

            request = load_generation_request(config)

            self.assertEqual(request.fan_refs, ["fan.jpg"])
            self.assertTrue(request.controls.use_style_lora)
            self.assertEqual(request.model.seed, 7)


if __name__ == "__main__":
    unittest.main()
