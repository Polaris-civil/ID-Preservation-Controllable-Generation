import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from id_preservation_cg.backends import ComfyUIBackend
from id_preservation_cg.config import GenerationRequest, ModelConfig


class ComfyUIClientPayloadTest(unittest.TestCase):
    def test_custom_api_workflow_placeholder_replacement(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            workflow = tmp_path / "workflow.json"
            workflow.write_text(
                json.dumps(
                    {
                        "1": {
                            "class_type": "SaveImage",
                            "inputs": {"filename_prefix": "{{filename_prefix}}"},
                        }
                    }
                ),
                encoding="utf-8",
            )
            request = GenerationRequest(
                fan_refs=["fan.jpg"],
                output_path=str(tmp_path / "my_output.png"),
                model=ModelConfig(backend="comfyui", comfyui_workflow=str(workflow)),
            )

            payload = ComfyUIBackend()._build_payload(request, "positive prompt", [])

            self.assertEqual(payload["prompt"]["1"]["inputs"]["filename_prefix"], "my_output")
            self.assertEqual(payload["extra_data"]["extra_pnginfo"]["idpcg"]["positive_prompt"], "positive prompt")
