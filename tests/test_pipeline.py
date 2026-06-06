import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from id_preservation_cg import ControllableGenerationPipeline, GenerationRequest


class PipelineTest(unittest.TestCase):
    def test_pipeline_writes_svg_and_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            output = Path(tmp) / "result.svg"
            result = ControllableGenerationPipeline().generate(
                GenerationRequest(
                    fan_refs=["missing_fan_a.jpg", "missing_fan_b.jpg"],
                    celebrity_refs=["missing_star.jpg"],
                    pose_image="missing_pose.png",
                    output_path=str(output),
                )
            )

            self.assertTrue(output.exists())
            self.assertTrue(Path(result["manifest"]).exists())
            self.assertIn("fan identity", result["prompt"])


if __name__ == "__main__":
    unittest.main()
