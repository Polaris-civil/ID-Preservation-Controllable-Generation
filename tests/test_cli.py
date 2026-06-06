import unittest
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from id_preservation_cg.cli import main


class CliTest(unittest.TestCase):
    def test_workflow_command_copies_packaged_template(self) -> None:
        with TemporaryDirectory() as tmp:
            target = Path(tmp) / "workflow.json"

            self.assertEqual(main(["workflow", "--output", str(target)]), 0)

            text = target.read_text(encoding="utf-8")
            self.assertIn("ID-Preservation Controllable Generation", text)

    def test_generate_config_preserves_output_path(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            output = tmp_path / "configured.svg"
            config = tmp_path / "request.json"
            config.write_text(
                json.dumps({"fan_refs": ["fan.jpg"], "output_path": str(output)}),
                encoding="utf-8",
            )

            self.assertEqual(main(["generate", "--config", str(config)]), 0)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
