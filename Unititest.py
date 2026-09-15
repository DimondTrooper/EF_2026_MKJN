import tkinter as tk
import unittest
 
from game import ANGLE_STEPS, DIRECTION_TO_ANGLE, clamp, next_step_towards
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
 
 
class TestNextStepTowards(unittest.TestCase):
    def test_same_angle_returns_same(self):
        self.assertEqual(next_step_towards(90, 90), 90)
 
    def test_one_step_forward(self):
        self.assertEqual(next_step_towards(0, 45), 45)
 
    def test_one_step_backward(self):
        self.assertEqual(next_step_towards(45, 0), 0)
 
    def test_takes_shortest_path_forward(self):
        # von 0 nach 90: vorwaerts 2 Schritte, rueckwaerts 6 -> vorwaerts
        self.assertEqual(next_step_towards(0, 90), 45)
 
    def test_takes_shortest_path_backward_wraps_around(self):
        # von 0 nach 315: vorwaerts 7 Schritte, rueckwaerts 1 -> rueckwaerts (wrap)
        self.assertEqual(next_step_towards(0, 315), 315)
 
    def test_full_rotation_reaches_target_eventually(self):
        # simulate: von 0 immer weiter Richtung 180 drehen, bis erreicht
        angle = 0
        steps = 0
        while angle != 180:
            angle = next_step_towards(angle, 180)
            steps += 1
            self.assertLessEqual(steps, len(ANGLE_STEPS))  # darf nie haengen bleiben
        self.assertEqual(angle, 180)
 
 
class TestDirectionToAngle(unittest.TestCase):
    def test_all_eight_directions_defined(self):
        self.assertEqual(len(DIRECTION_TO_ANGLE), 8)
 
    def test_up_only(self):
        self.assertEqual(DIRECTION_TO_ANGLE[(True, False, False, False)], 0)
 
    def test_down_only(self):
        self.assertEqual(DIRECTION_TO_ANGLE[(False, True, False, False)], 180)
 
    def test_up_right_diagonal(self):
        self.assertEqual(DIRECTION_TO_ANGLE[(True, False, False, True)], 315)
 
    def test_all_mapped_angles_are_valid_steps(self):
        for angle in DIRECTION_TO_ANGLE.values():
            self.assertIn(angle, ANGLE_STEPS)
 
 
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