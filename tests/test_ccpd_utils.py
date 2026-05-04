import unittest
from pathlib import Path

from train.ccpd_utils import parse_ccpd_filename


class CCPDUtilsTestCase(unittest.TestCase):
    def test_parse_standard_ccpd_filename(self):
        sample = Path("025-95_113-154&383_386&473-386&473_177&454_154&383_363&402-0_0_22_27_27_33_16-37-15.jpg")

        annotation = parse_ccpd_filename(sample)

        self.assertEqual(annotation.area_ratio_raw, "025")
        self.assertAlmostEqual(annotation.area_ratio, 0.025)
        self.assertEqual(annotation.tilt_degrees, (95, 113))
        self.assertEqual(annotation.bbox, (154, 383, 386, 473))
        self.assertEqual(
            annotation.vertices,
            ((386, 473), (177, 454), (154, 383), (363, 402)),
        )
        self.assertEqual(annotation.plate_indices, (0, 0, 22, 27, 27, 33, 16))
        self.assertEqual(annotation.plate_text, "皖AY339S")
        self.assertEqual(annotation.brightness, 37)
        self.assertEqual(annotation.blurriness, 15)

    def test_invalid_filename_raises_clear_error(self):
        with self.assertRaisesRegex(ValueError, "Expected 7 '-' separated fields"):
            parse_ccpd_filename("bad_filename.jpg")


if __name__ == "__main__":
    unittest.main()
