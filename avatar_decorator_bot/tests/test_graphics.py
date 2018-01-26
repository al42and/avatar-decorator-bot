import unittest
import os.path
from PIL import Image, ImageChops, ImageStat

from avatar_decorator_bot import graphics


class TestGraphics(unittest.TestCase):
    _FILE_NAME_PREFIX = 'avatar_decorator_bot/tests/data'

    def test_get_color(self):
        with self.assertRaises(ValueError):
            graphics.get_color([''])
        with self.assertRaises(ValueError):
            graphics.get_color(['reeeeed'])
        self.assertEqual(graphics.get_color(['red']), (255, 0, 0))
        self.assertEqual(graphics.get_color(['lightskyblue']), (0x87, 0xce, 0xfa))
        self.assertEqual(graphics.get_color(['#1234ef']), (0x12, 0x34, 0xef))
        self.assertEqual(graphics.get_color(['#1234efff']), (0x12, 0x34, 0xef))
        self.assertEqual(graphics.get_color(['rgb(12,34,99)']), (12, 34, 99))
        self.assertEqual(graphics.get_color(['rgb(12,', '34', ',', '99)']), (12, 34, 99))

    def test_create_empty_avatar(self):
        result_bytes = graphics.create_empty_avatar((255, 0, 0))
        self._compare_bytes_to_file(result_bytes, 'red.png')

    def test_add_color_to_avatar(self):
        # We don't test the rim between avatar and color mask, because who cares about details of antialiasing?
        with open(os.path.join(self._FILE_NAME_PREFIX, 'face.png'), 'rb') as img:
            result_bytes = graphics.add_color_to_avatar(img, (255, 0, 0))
            self._compare_bytes_to_file(result_bytes, 'face_red.png')

    def _compare_bytes_to_file(self, img_bytes: bytes, filename: str) -> None:
        image = Image.open(img_bytes)
        image_ref = Image.open(os.path.join(self._FILE_NAME_PREFIX, filename))
        self.assertEqual(image.size, image_ref.size)  # First, compare sizes
        image_ref_alpha = image_ref.split()[-1]  # Extract alpha channel from reference image
        mask = image_ref_alpha.convert("L")  # We don't compare values where reference image is transparent
        image_ref = image_ref.convert('RGB')
        # Calculate sum of absolute differences between two images
        diff_sum = ImageStat.Stat(ImageChops.difference(image, image_ref), mask=mask).sum
        self.assertEqual(max(diff_sum), 0)


if __name__ == '__main__':
    unittest.main()
