import importlib.util
import shutil
import unittest
from pathlib import Path


HAS_NUMPY = importlib.util.find_spec("numpy") is not None

if HAS_NUMPY:
    from train.crnn_dataset import (
        CRNNCharset,
        build_charset_from_manifests,
        build_prediction_rows,
        compute_accuracy_from_rows,
        compute_edit_distance,
    )


TMP_ROOT = Path("tests") / "_tmp_crnn_charset"


@unittest.skipUnless(HAS_NUMPY, "numpy is required for CRNN charset tests")
class CRNNCharsetTestCase(unittest.TestCase):
    def test_encode_decode_roundtrip(self):
        charset = CRNNCharset()
        text = "\u7696A12345"
        encoded = charset.encode(text)
        decoded = charset.decode_encoded_text(encoded)
        self.assertEqual(decoded, text)
        self.assertTrue(all(index > 0 for index in encoded))

    def test_greedy_decode_removes_blank_and_repeated_tokens(self):
        charset = CRNNCharset(["\u7696", "A", "1", "2", "3", "4", "5"])
        blank = charset.blank_index
        indices = [
            charset.char_to_index["\u7696"],
            charset.char_to_index["\u7696"],
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
        self.assertEqual(decoded, "\u7696A12345")

    def test_greedy_decode_keeps_repeated_tokens_when_blank_separates_them(self):
        charset = CRNNCharset(["\u7696", "A", "0", "B", "9"])
        blank = charset.blank_index
        indices = [
            charset.char_to_index["\u7696"],
            blank,
            charset.char_to_index["A"],
            blank,
            charset.char_to_index["A"],
            charset.char_to_index["A"],
            blank,
            charset.char_to_index["0"],
            charset.char_to_index["B"],
            blank,
            charset.char_to_index["0"],
            charset.char_to_index["9"],
        ]
        decoded = charset.decode_indices(indices)
        self.assertEqual(decoded, "\u7696AA0B09")

    def test_build_charset_from_manifests_covers_all_seen_characters(self):
        temp_dir = TMP_ROOT / "build_charset"
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
            temp_dir.mkdir(parents=True, exist_ok=True)

            manifest = temp_dir / "train.txt"
            manifest.write_text(
                "images/train/a.jpg\t\u7696A12345\nimages/train/b.jpg\t\u82cfB9Z888\n",
                encoding="utf-8",
            )

            charset = build_charset_from_manifests(
                data_root=temp_dir,
                manifest_paths=["train.txt"],
            )
            mapping = charset.to_json_dict()
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

        self.assertIn("\u7696", charset.characters)
        self.assertIn("\u82cf", charset.characters)
        self.assertIn("Z", charset.characters)
        self.assertEqual(mapping["blank_index"], 0)
        self.assertEqual(mapping["char_to_index"]["\u7696"], charset.char_to_index["\u7696"])

    def test_plate_accuracy_counts_exact_matches_from_prediction_rows(self):
        rows = build_prediction_rows(
            image_paths=["a.jpg", "b.jpg", "c.jpg"],
            predictions=["\u7696AY8451 ", "\u7696A2", " \u7696A397S8"],
            targets=[" \u7696AY8451", "\u7696AWP262", "\u7696A397S8\n"],
        )
        char_acc, plate_acc = compute_accuracy_from_rows(rows)
        self.assertEqual(sum(int(row["exact_match"]) for row in rows), 2)
        self.assertAlmostEqual(plate_acc, 2 / 3)
        self.assertGreater(char_acc, plate_acc)

    def test_edit_distance_handles_missing_middle_characters(self):
        self.assertEqual(compute_edit_distance("\u7696AA0B09", "\u7696AA09"), 2)
        self.assertEqual(compute_edit_distance("\u7696AY7T35", "\u7696AYT35"), 1)


if __name__ == "__main__":
    unittest.main()
