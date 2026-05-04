import importlib.util
import shutil
import unittest
from pathlib import Path


HAS_NUMPY = importlib.util.find_spec("numpy") is not None

if HAS_NUMPY:
    from train.crnn_dataset import CRNNCharset, build_charset_from_manifests


TMP_ROOT = Path("tests") / "_tmp_crnn_charset"


@unittest.skipUnless(HAS_NUMPY, "numpy is required for CRNN charset tests")
class CRNNCharsetTestCase(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        charset = CRNNCharset()
        text = "皖A12345"
        encoded = charset.encode(text)
        decoded = charset.decode_encoded_text(encoded)
        self.assertEqual(decoded, text)
        self.assertTrue(all(index > 0 for index in encoded))

    def test_greedy_decode_removes_blank_and_repeated_tokens(self):
        charset = CRNNCharset(["皖", "A", "1", "2", "3", "4", "5"])
        blank = charset.blank_index
        indices = [
            charset.char_to_index["皖"],
            charset.char_to_index["皖"],
            blank,
            charset.char_to_index["A"],
            blank,
            charset.char_to_index["1"],
            charset.char_to_index["1"],
            charset.char_to_index["2"],
            charset.char_to_index["3"],
            blank,
            charset.char_to_index["4"],
            charset.char_to_index["5"],
        ]
        decoded = charset.decode_indices(indices)
        self.assertEqual(decoded, "皖A12345")

    def test_build_charset_from_manifests_covers_all_seen_characters(self):
        temp_dir = TMP_ROOT / "build_charset"
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)

            manifest = temp_dir / "train.txt"
            manifest.write_text(
                "images/train/a.jpg\t皖A12345\nimages/train/b.jpg\t苏B9Z888\n",
                encoding="utf-8",
            )

            charset = build_charset_from_manifests(
                data_root=temp_dir,
                manifest_paths=["train.txt"],
            )
            mapping = charset.to_json_dict()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIn("皖", charset.characters)
        self.assertIn("苏", charset.characters)
        self.assertIn("Z", charset.characters)
        self.assertEqual(mapping["blank_index"], 0)
        self.assertEqual(mapping["char_to_index"]["皖"], charset.char_to_index["皖"])
