import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from id_preservation_cg import ControllableGenerationPipeline, GenerationRequest
from id_preservation_cg.config import ModelConfig


class BackendTest(unittest.TestCase):
    def test_comfyui_backend_writes_payload_without_submission(self) -> None:
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.png"
            request = GenerationRequest(
                fan_refs=["fan.jpg"],
                celebrity_refs=["star.jpg"],
                output_path=str(output),
                model=ModelConfig(backend="comfyui", submit_comfyui_job=False),
            )

            result = ControllableGenerationPipeline().generate(request)
            payload_path = output.with_suffix(".comfyui_payload.json")

            self.assertTrue(Path(result["manifest"]).exists())
            self.assertTrue(payload_path.exists())
            payload = json.loads(payload_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["prompt"]["fan_refs"], ["fan.jpg"])
            self.assertEqual(payload["prompt"]["seed"], 42)


if __name__ == "__main__":
    unittest.main()
