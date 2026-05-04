import shutil
import unittest
from pathlib import Path

from train.prepare_ccpd import collect_parsed_samples, split_samples


VALID_NAME_1 = "025-95_113-154&383_386&473-386&473_177&454_154&383_363&402-0_0_22_27_27_33_16-37-15.jpg"
VALID_NAME_2 = "026-90_100-120&300_360&400-360&400_130&390_120&300_350&310-0_1_2_3_4_5_6-40-10.jpg"
INVALID_NAME = "not_a_ccpd_name.jpg"
TMP_ROOT = Path("tests") / "_tmp_prepare_ccpd"


class PrepareCCPDTestCase(unittest.TestCase):
    def test_collect_parsed_samples_skips_invalid_filenames(self):
        temp_dir = TMP_ROOT / "case_skip_invalid"
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir
            for name in (VALID_NAME_1, VALID_NAME_2, INVALID_NAME):
                (temp_path / name).write_bytes(b"placeholder")

            image_paths = sorted(temp_path.iterdir())
            samples, skipped = collect_parsed_samples(image_paths)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertEqual(len(samples), 2)
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0].image_path.name, INVALID_NAME)

    def test_split_samples_is_reproducible(self):
        temp_dir = TMP_ROOT / "case_split_reproducible"
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)
            temp_path = temp_dir
            image_paths = []
            for index in range(10):
                name = (
                    f"0{index}-95_113-154&383_386&473-386&473_177&454_154&383_363&402-"
                    f"0_0_22_27_27_33_16-37-{index}.jpg"
                )
                path = temp_path / name
                path.write_bytes(b"placeholder")
                image_paths.append(path)

            samples, skipped = collect_parsed_samples(image_paths)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertFalse(skipped)
        first_split = split_samples(samples, seed=42, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)
        second_split = split_samples(samples, seed=42, train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)

        self.assertEqual([sample.image_path.name for sample in first_split[0].samples], [sample.image_path.name for sample in second_split[0].samples])
        self.assertEqual([sample.image_path.name for sample in first_split[1].samples], [sample.image_path.name for sample in second_split[1].samples])
        self.assertEqual([sample.image_path.name for sample in first_split[2].samples], [sample.image_path.name for sample in second_split[2].samples])
        self.assertEqual(len(first_split[0].samples), 8)
        self.assertEqual(len(first_split[1].samples), 1)
        self.assertEqual(len(first_split[2].samples), 1)


if __name__ == "__main__":
    unittest.main()
