import tkinter as tk
import unittest

from game import ANGLE_STEPS, clamp
from build_tank_images import get_tank_images


class TestClamp(unittest.TestCase):
    def test_value_within_range_unchanged(self):
        self.assertEqual(clamp(5, 0, 10), 5)

    def test_value_below_min_is_clamped(self):
        self.assertEqual(clamp(-5, 0, 10), 0)

    def test_value_above_max_is_clamped(self):
        self.assertEqual(clamp(50, 0, 10), 10)

    def test_value_equal_to_bound(self):
        self.assertEqual(clamp(0, 0, 10), 0)
        self.assertEqual(clamp(10, 0, 10), 10)


class TestAngleSteps(unittest.TestCase):
    def test_eight_angles_defined(self):
        self.assertEqual(len(ANGLE_STEPS), 8)

    def test_steps_are_45_degrees_apart(self):
        for i in range(len(ANGLE_STEPS)):
            current = ANGLE_STEPS[i]
            nxt = ANGLE_STEPS[(i + 1) % len(ANGLE_STEPS)]
            diff = (nxt - current) % 360
            self.assertEqual(diff, 45)


class TestGetTankImages(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ImageTk.PhotoImage braucht ein existierendes Tk-Fenster
        cls.root = tk.Tk()
 
    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()
 
    def test_returns_all_eight_angles(self):
        images = get_tank_images()
        self.assertEqual(set(images.keys()), set(ANGLE_STEPS))
 
    def test_images_have_size(self):
        images = get_tank_images()
        for angle, img in images.items():
            self.assertGreater(img.width(), 0, f"angle {angle}")
            self.assertGreater(img.height(), 0, f"angle {angle}")
 
 
if __name__ == "__main__":
    unittest.main()