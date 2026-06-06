import unittest

from id_preservation_cg import ControllableGenerationPipeline, GenerationRequest
from id_preservation_cg.config import LoraConfig
from id_preservation_cg.lora import LoraTrainer


class ValidationTest(unittest.TestCase):
    def test_generation_requires_fan_refs(self) -> None:
        with self.assertRaisesRegex(ValueError, "fan_refs"):
            ControllableGenerationPipeline().generate(GenerationRequest(fan_refs=[]))

    def test_lora_rank_must_be_positive(self) -> None:
        with self.assertRaisesRegex(ValueError, "rank"):
            LoraTrainer(LoraConfig(rank=0)).train(["a.jpg"])


if __name__ == "__main__":
    unittest.main()
