import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from id_preservation_cg.config import LoraConfig
from id_preservation_cg.lora import LoraTrainer


class LoraTrainerTest(unittest.TestCase):
    def test_lora_trainer_writes_manifest(self) -> None:
        with TemporaryDirectory() as tmp:
            manifest = LoraTrainer(LoraConfig(output_dir=str(Path(tmp) / "lora"))).train(["a.jpg", "b.jpg"])
            self.assertTrue(manifest.exists())
            self.assertIn("training_manifest.json", str(manifest))


if __name__ == "__main__":
    unittest.main()
