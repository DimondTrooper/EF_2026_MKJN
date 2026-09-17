### Claude code für Unit-Tests (die ganze Datei ist von Claude)
import tkinter as tk
import unittest

from game import ANGLE_STEPS, clamp
from build_tank_images import get_tank_images

import math
import os
import sys
import time
from unittest import mock

from PIL import Image

import game
import scoreboard
import utils
from build_tank_images import (
    HULL_PX,
    MUZZLE_FLASH_FRAME_COUNT,
    TANK_BASE_PATHS,
    _forward_vector,
    _hull_metrics,
    _load_scaled,
    get_destroyed_tank_images,
    get_muzzle_flash_frames,
)

#Alle Tests teilen sich EIN Tk-Fenster: PhotoImages gehoeren immer zu genau
#einem Tk-Interpreter (siehe menu.py), mehrere Fenster wuerden sich stoeren.
shared_root = None


def setUpModule():
    """
    Macht: Erstellt ein unsichtbares Tk-Fenster fuer alle Tests.
    Input: keine
    Output: kein Rueckgabewert
    """
    global shared_root
    shared_root = tk.Tk()
    shared_root.withdraw()


def tearDownModule():
    """
    Macht: Schliesst das gemeinsame Tk-Fenster nach allen Tests.
    Input: keine
    Output: kein Rueckgabewert
    """
    shared_root.destroy()


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
    # ImageTk.PhotoImage braucht ein existierendes Tk-Fenster -> shared_root aus setUpModule

    def test_returns_all_eight_angles(self):
        images = get_tank_images()
        self.assertEqual(set(images.keys()), set(ANGLE_STEPS))

    def test_images_have_size(self):
        images = get_tank_images()
        for angle, img in images.items():
            self.assertGreater(img.width(), 0, f"angle {angle}")
            self.assertGreater(img.height(), 0, f"angle {angle}")


# ============================================================================
# Hilfsfunktionen fuer die Tests
# ============================================================================

def make_world(width=800, height=600):
    """
    Macht: Baut ein kleines Test-Spielfeld ohne Zufall (keine Baeume/Minen),
           mit einfachen Platzhalter-Bildern statt der echten Assets.
    Input: width, height (Spielfeldgroesse)
    Output: world (Dict wie aus game.build_world)
    """
    canvas = tk.Canvas(shared_root, width=width, height=height)
    placeholder = tk.PhotoImage(master=shared_root, width=10, height=10)
    return {
        "canvas": canvas,
        "width": width,
        "height": height,
        "tree_photos": [placeholder],
        "trunk_photo": placeholder,
        "mine_photo": placeholder,
        "explosion_frames": [placeholder] * game.EXPLOSION_FRAME_COUNT,
        "wreck_images": {angle: placeholder for angle in ANGLE_STEPS},
        "trees": [],
        "mines": [],
        "wrecks": [],
    }


def make_player(world, start, name="Tester", number=1):
    """
    Macht: Erstellt einen Test-Spieler mit Platzhalter-Panzerbildern.
    Input: world (Test-Spielfeld), start ((x, y)), name, number (Spielernummer 1-3)
    Output: player (Dict wie aus game.create_player)
    """
    tank_image = tk.PhotoImage(master=shared_root, width=HULL_PX, height=HULL_PX)
    tank_images = {angle: tank_image for angle in ANGLE_STEPS}
    flash_frames = {angle: [tank_image] * MUZZLE_FLASH_FRAME_COUNT for angle in ANGLE_STEPS}
    return game.create_player(
        shared_root, world["canvas"], name, game.PLAYER_KEYS[number],
        tank_images, flash_frames, start,
    )


def add_circle(objects, cx, cy, radius=20):
    """
    Macht: Fuegt ein rundes Hindernis (Baum, Mine, Wrack) ohne Bild hinzu.
    Input: objects (Liste), cx, cy, radius
    Output: das neue Objekt-Dict
    """
    obj = {"id": None, "cx": cx, "cy": cy, "radius": radius}
    objects.append(obj)
    return obj


# ============================================================================
# game.py -- Kollisionen und Mathematik
# ============================================================================

class TestRectsOverlap(unittest.TestCase):
    def test_overlapping(self):
        self.assertTrue(game.rects_overlap((0, 0, 10, 10), (5, 5, 15, 15)))

    def test_separate(self):
        self.assertFalse(game.rects_overlap((0, 0, 10, 10), (20, 20, 30, 30)))

    def test_touching_edges_count_as_overlap(self):
        self.assertTrue(game.rects_overlap((0, 0, 10, 10), (10, 0, 20, 10)))

    def test_one_inside_other(self):
        self.assertTrue(game.rects_overlap((0, 0, 100, 100), (40, 40, 50, 50)))


class TestCircleRectOverlap(unittest.TestCase):
    def test_circle_inside_rect(self):
        self.assertTrue(game.circle_rect_overlap(5, 5, 1, (0, 0, 10, 10)))

    def test_circle_near_edge(self):
        self.assertTrue(game.circle_rect_overlap(15, 5, 5, (0, 0, 10, 10)))

    def test_circle_far_away(self):
        self.assertFalse(game.circle_rect_overlap(50, 50, 5, (0, 0, 10, 10)))

    def test_corner_uses_real_distance(self):
        # Abstand zur Ecke (10,10) ist sqrt(32) ~ 5.66 > 5 -> keine Beruehrung
        self.assertFalse(game.circle_rect_overlap(14, 14, 5, (0, 0, 10, 10)))


class TestCirclesOverlap(unittest.TestCase):
    def test_overlapping(self):
        self.assertTrue(game.circles_overlap(0, 0, 5, 8, 0, 5))

    def test_exactly_touching(self):
        self.assertTrue(game.circles_overlap(0, 0, 5, 10, 0, 5))

    def test_separate(self):
        self.assertFalse(game.circles_overlap(0, 0, 5, 11, 0, 5))

    def test_diagonal_distance(self):
        self.assertFalse(game.circles_overlap(0, 0, 5, 8, 8, 5))


class TestCircleHelpers(unittest.TestCase):
    def test_circle_bounding_box(self):
        self.assertEqual(game.circle_bounding_box({"cx": 50, "cy": 40, "radius": 10}), (40, 30, 60, 50))

    def test_first_circle_hit_returns_first_match(self):
        objects = []
        add_circle(objects, 500, 500)
        first = add_circle(objects, 10, 0)
        add_circle(objects, 12, 0)
        self.assertIs(game.first_circle_hit(0, 0, 5, objects), first)

    def test_first_circle_hit_none(self):
        objects = []
        add_circle(objects, 500, 500)
        self.assertIsNone(game.first_circle_hit(0, 0, 5, objects))

    def test_first_rect_hit(self):
        objects = []
        add_circle(objects, 500, 500)
        target = add_circle(objects, 30, 30, radius=10)
        self.assertIs(game.first_rect_hit((15, 15, 25, 25), objects), target)
        self.assertIsNone(game.first_rect_hit((0, 0, 5, 5), objects))


class TestAngleToVector(unittest.TestCase):
    def test_every_angle_has_a_vector(self):
        self.assertEqual(set(game.ANGLE_TO_VECTOR), set(ANGLE_STEPS))

    def test_vectors_have_length_one(self):
        for angle, (dx, dy) in game.ANGLE_TO_VECTOR.items():
            self.assertAlmostEqual(math.hypot(dx, dy), 1.0, places=6, msg=f"angle {angle}")

    def test_zero_degrees_points_up(self):
        self.assertEqual(game.ANGLE_TO_VECTOR[0], (0, -1))

    def test_matches_build_tank_images_convention(self):
        for angle, (dx, dy) in game.ANGLE_TO_VECTOR.items():
            fx, fy = _forward_vector(angle)
            self.assertAlmostEqual(dx, fx, places=6, msg=f"angle {angle}")
            self.assertAlmostEqual(dy, fy, places=6, msg=f"angle {angle}")


class TestPlayerConfig(unittest.TestCase):
    def test_modes_have_right_player_count(self):
        self.assertEqual(len(game.PLAYER_NUMBERS_BY_MODE["1 vs 1"]), 2)
        self.assertEqual(len(game.PLAYER_NUMBERS_BY_MODE["1 vs 1 vs 1"]), 3)

    def test_every_player_has_keys_and_color(self):
        for number in game.PLAYER_NUMBERS_BY_MODE["1 vs 1 vs 1"]:
            self.assertEqual(set(game.PLAYER_KEYS[number]), {"up", "down", "left", "right", "shoot"})
            self.assertIn(number, game.PLAYER_COLORS)

    def test_no_key_used_twice(self):
        all_keys = [key for keys in game.PLAYER_KEYS.values() for key in keys.values()]
        self.assertEqual(len(all_keys), len(set(all_keys)))


class TestReadMovementKeys(unittest.TestCase):
    def test_nothing_pressed(self):
        self.assertEqual(game.read_movement_keys(game.PLAYER_KEYS[1], set()), (False, False, False, False))

    def test_forward_and_left(self):
        self.assertEqual(game.read_movement_keys(game.PLAYER_KEYS[1], {"w", "a"}), (True, False, True, False))

    def test_keys_of_other_player_ignored(self):
        self.assertEqual(game.read_movement_keys(game.PLAYER_KEYS[2], {"w", "s"}), (False, False, False, False))


class TestSpawnPositions(unittest.TestCase):
    def test_position_inside_margin(self):
        for _ in range(100):
            x, y = game.random_spawn_position(800, 600)
            self.assertTrue(game.SPAWN_MARGIN <= x <= 800 - game.SPAWN_MARGIN)
            self.assertTrue(game.SPAWN_MARGIN <= y <= 600 - game.SPAWN_MARGIN)

    def test_avoids_boxes(self):
        # linke Haelfte ist blockiert -> Position muss rechts liegen
        blocked = [(0, 0, 400, 600)]
        for _ in range(50):
            x, _ = game.random_spawn_position(800, 600, blocked, 10, 10)
            self.assertGreater(x - 10, 400)

    def test_pick_tank_spawns_count(self):
        self.assertEqual(len(game.pick_tank_spawns(3, 1600, 900, [], 25)), 3)

    def test_pick_tank_spawns_keep_distance(self):
        for _ in range(20):
            spawns = game.pick_tank_spawns(3, 1600, 900, [], 25)
            for i, (x1, y1) in enumerate(spawns):
                for x2, y2 in spawns[i + 1:]:
                    self.assertGreaterEqual(math.hypot(x1 - x2, y1 - y2), game.MIN_PLAYER_SPAWN_DISTANCE)


# ============================================================================
# game.py -- Bildhelfer
# ============================================================================

class TestImageHelpers(unittest.TestCase):
    def test_scale_image(self):
        img = Image.new("RGBA", (100, 50))
        self.assertEqual(game.scale_image(img, 0.5).size, (50, 25))

    def test_scale_image_never_zero(self):
        img = Image.new("RGBA", (10, 10))
        self.assertEqual(game.scale_image(img, 0.001).size, (1, 1))

    def test_longest_side_factor(self):
        self.assertEqual(game.longest_side_factor(Image.new("RGBA", (200, 100)), 50), 0.25)
        self.assertEqual(game.longest_side_factor(Image.new("RGBA", (100, 400)), 100), 0.25)

    def test_center_on_square(self):
        img = Image.new("RGBA", (10, 20), (255, 0, 0, 255))
        square = game.center_on_square(img, 40)
        self.assertEqual(square.size, (40, 40))
        self.assertEqual(square.getpixel((20, 20)), (255, 0, 0, 255))  # Mitte ist rot
        self.assertEqual(square.getpixel((0, 0))[3], 0)  # Ecke ist transparent
        self.assertEqual(square.getbbox(), (15, 10, 25, 30))


# ============================================================================
# game.py -- Spieler und Spielablauf (mit Canvas)
# ============================================================================

class TestCreatePlayer(unittest.TestCase):
    def test_initial_state(self):
        world = make_world()
        player = make_player(world, (100, 200))
        self.assertTrue(player["alive"])
        self.assertEqual(player["state"]["angle"], 0)
        self.assertEqual(player["projectiles"], [])
        self.assertEqual(world["canvas"].coords(player["tank"]), [100.0, 200.0])

    def test_name_tag_above_tank(self):
        world = make_world()
        player = make_player(world, (100, 200), name="Noah")
        canvas = world["canvas"]
        self.assertEqual(canvas.itemcget(player["name_tag"], "text"), "Noah")
        self.assertLess(canvas.coords(player["name_tag"])[1], 200)

    def test_reload_ring_hidden_at_start(self):
        world = make_world()
        player = make_player(world, (100, 200))
        self.assertEqual(world["canvas"].itemcget(player["reload_ring"], "state"), "hidden")

    def test_reload_ring_right_of_name(self):
        world = make_world()
        player = make_player(world, (100, 200))
        canvas = world["canvas"]
        ring_left = game.reload_ring_box(canvas, player["name_tag"])[0]
        self.assertGreater(ring_left, canvas.bbox(player["name_tag"])[2])


class TestUpdateRotation(unittest.TestCase):
    def setUp(self):
        self.world = make_world()
        self.player = make_player(self.world, (400, 300))
        self.canvas = self.world["canvas"]

    def test_turn_left_adds_45(self):
        game.update_rotation(self.canvas, self.player, True, False)
        self.assertEqual(self.player["state"]["angle"], 45)

    def test_turn_right_wraps_to_315(self):
        game.update_rotation(self.canvas, self.player, False, True)
        self.assertEqual(self.player["state"]["angle"], 315)

    def test_both_or_no_keys_do_nothing(self):
        game.update_rotation(self.canvas, self.player, True, True)
        game.update_rotation(self.canvas, self.player, False, False)
        self.assertEqual(self.player["state"]["angle"], 0)

    def test_cooldown_blocks_second_step(self):
        game.update_rotation(self.canvas, self.player, True, False)
        game.update_rotation(self.canvas, self.player, True, False)
        self.assertEqual(self.player["state"]["angle"], 45)

    def test_after_cooldown_turns_again(self):
        game.update_rotation(self.canvas, self.player, True, False)
        self.player["state"]["last_rotate_time"] = 0  # Cooldown abgelaufen
        game.update_rotation(self.canvas, self.player, True, False)
        self.assertEqual(self.player["state"]["angle"], 90)


class TestMoveTank(unittest.TestCase):
    def setUp(self):
        self.world = make_world()
        self.player = make_player(self.world, (400, 300))
        self.canvas = self.world["canvas"]

    def test_forward_moves_up(self):
        self.assertEqual(game.move_tank(self.world, self.player, True, False, []), (400, 300 - game.SPEED))
        self.assertTrue(self.player["moving"])

    def test_backward_moves_down(self):
        self.assertEqual(game.move_tank(self.world, self.player, False, True, []), (400, 300 + game.SPEED))

    def test_follows_angle(self):
        self.player["state"]["angle"] = 270  # nach rechts
        self.assertEqual(game.move_tank(self.world, self.player, True, False, []), (400 + game.SPEED, 300))

    def test_name_tag_moves_along(self):
        before = self.canvas.coords(self.player["name_tag"])
        game.move_tank(self.world, self.player, True, False, [])
        after = self.canvas.coords(self.player["name_tag"])
        self.assertEqual(after[1], before[1] - game.SPEED)

    def test_no_or_both_keys(self):
        self.assertIsNone(game.move_tank(self.world, self.player, False, False, []))
        self.assertIsNone(game.move_tank(self.world, self.player, True, True, []))
        self.assertFalse(self.player["moving"])

    def test_stays_inside_field(self):
        player = make_player(self.world, (400, game.TANK_HITBOX_RADIUS))
        game.move_tank(self.world, player, True, False, [])
        self.assertGreaterEqual(self.canvas.coords(player["tank"])[1], game.TANK_HITBOX_RADIUS)

    def test_can_drive_close_to_edge(self):
        # keine unsichtbare Wand: der Panzer kommt bis auf die Hitbox an den Rand
        player = make_player(self.world, (400, game.TANK_HITBOX_RADIUS + 3))
        for _ in range(10):
            game.move_tank(self.world, player, True, False, [])
        self.assertAlmostEqual(self.canvas.coords(player["tank"])[1], game.TANK_HITBOX_RADIUS, places=3)

    def test_blocked_by_tree(self):
        add_circle(self.world["trees"], 400, 300 - game.TANK_HITBOX_RADIUS - 10)
        self.assertIsNone(game.move_tank(self.world, self.player, True, False, []))
        self.assertEqual(self.canvas.coords(self.player["tank"]), [400.0, 300.0])

    def test_blocked_by_wreck(self):
        add_circle(self.world["wrecks"], 400, 300 - game.TANK_HITBOX_RADIUS - 10)
        self.assertIsNone(game.move_tank(self.world, self.player, True, False, []))

    def test_blocked_by_living_tank_only(self):
        other = make_player(self.world, (400, 300 - 2 * game.TANK_HITBOX_RADIUS))
        self.assertIsNone(game.move_tank(self.world, self.player, True, False, [other]))
        other["alive"] = False
        self.assertIsNotNone(game.move_tank(self.world, self.player, True, False, [other]))


class TestMinesAndDestroy(unittest.TestCase):
    def setUp(self):
        self.world = make_world()
        self.player = make_player(self.world, (400, 300))

    def test_mine_destroys_tank(self):
        mine = add_circle(self.world["mines"], 400, 300, radius=10)
        mine["id"] = self.world["canvas"].create_oval(390, 290, 410, 310)
        game.trigger_mine(self.world, self.player, (400, 300))
        self.assertFalse(self.player["alive"])
        self.assertEqual(self.world["mines"], [])
        self.assertIsNotNone(self.player["explosion"])

    def test_far_mine_does_nothing(self):
        add_circle(self.world["mines"], 700, 500, radius=10)
        game.trigger_mine(self.world, self.player, (400, 300))
        self.assertTrue(self.player["alive"])
        self.assertEqual(len(self.world["mines"]), 1)

    def test_destroy_removes_canvas_items(self):
        canvas = self.world["canvas"]
        game.destroy_player(self.world, self.player)
        for item in ("tank", "name_tag", "reload_ring"):
            self.assertEqual(canvas.find_withtag(self.player[item]), ())

    def test_destroy_twice_is_safe(self):
        game.destroy_player(self.world, self.player)
        explosion = self.player["explosion"]
        game.destroy_player(self.world, self.player)
        self.assertIs(self.player["explosion"], explosion)

    def test_explosion_ends_in_wreck(self):
        self.player["state"]["angle"] = 90
        game.destroy_player(self.world, self.player)
        for _ in range(game.EXPLOSION_FRAME_COUNT):
            self.player["explosion"]["next_frame_time"] = 0
            game.update_explosion(self.world, self.player)
        self.assertIsNone(self.player["explosion"])
        self.assertEqual(len(self.world["wrecks"]), 1)
        wreck = self.world["wrecks"][0]
        self.assertEqual((wreck["cx"], wreck["cy"]), (400, 300))
        self.assertEqual(wreck["radius"], game.TANK_HITBOX_RADIUS)

    def test_explosion_waits_for_frame_time(self):
        game.destroy_player(self.world, self.player)
        game.update_explosion(self.world, self.player)  # Zeit noch nicht erreicht
        self.assertEqual(self.player["explosion"]["frame"], 0)


class TestShooting(unittest.TestCase):
    def setUp(self):
        self.world = make_world()
        self.player = make_player(self.world, (400, 300))
        self.canvas = self.world["canvas"]

    def test_fire_creates_projectile_at_barrel(self):
        game.fire_bullet(self.canvas, self.player)
        self.assertEqual(len(self.player["projectiles"]), 1)
        x1, y1, x2, y2 = self.canvas.coords(self.player["projectiles"][0]["id"])
        self.assertEqual(((x1 + x2) / 2, (y1 + y2) / 2), (400, 300 - game.BARREL_OFFSET))
        self.assertIsNotNone(self.player["shoot_animation"])

    def test_cooldown_blocks_second_shot(self):
        game.fire_bullet(self.canvas, self.player)
        game.fire_bullet(self.canvas, self.player)
        self.assertEqual(len(self.player["projectiles"]), 1)

    def test_dead_player_cannot_shoot(self):
        self.player["alive"] = False
        game.fire_bullet(self.canvas, self.player)
        self.assertEqual(self.player["projectiles"], [])

    def test_projectile_moves_in_direction(self):
        game.fire_bullet(self.canvas, self.player)
        game.update_projectiles(self.world, self.player)
        x1, y1, x2, y2 = self.canvas.coords(self.player["projectiles"][0]["id"])
        self.assertEqual((y1 + y2) / 2, 300 - game.BARREL_OFFSET - game.PROJECTILE_SPEED)

    def test_projectile_breaks_tree(self):
        tree = add_circle(self.world["trees"], 400, 300 - game.BARREL_OFFSET - game.PROJECTILE_SPEED)
        tree["id"] = self.canvas.create_image(tree["cx"], tree["cy"], image=self.world["tree_photos"][0])
        game.fire_bullet(self.canvas, self.player)
        game.update_projectiles(self.world, self.player)
        self.assertEqual(self.world["trees"], [])
        self.assertEqual(self.player["projectiles"], [])

    def test_wreck_stops_projectile(self):
        add_circle(self.world["wrecks"], 400, 300 - game.BARREL_OFFSET - game.PROJECTILE_SPEED)
        game.fire_bullet(self.canvas, self.player)
        game.update_projectiles(self.world, self.player)
        self.assertEqual(self.player["projectiles"], [])
        self.assertEqual(len(self.world["wrecks"]), 1)  # Wrack bleibt als Deckung

    def test_projectile_removed_outside_field(self):
        game.fire_bullet(self.canvas, self.player)
        for _ in range(100):
            game.update_projectiles(self.world, self.player)
        self.assertEqual(self.player["projectiles"], [])

    def test_hit_destroys_other_tank(self):
        target = make_player(self.world, (400, 150), number=2)
        game.fire_bullet(self.canvas, self.player)
        for _ in range(30):
            game.update_projectiles(self.world, self.player)
            game.check_hits(self.world, [self.player, target])
        self.assertFalse(target["alive"])
        self.assertTrue(self.player["alive"])
        self.assertEqual(self.player["projectiles"], [])

    def test_own_projectile_does_not_hit_shooter(self):
        game.fire_bullet(self.canvas, self.player)
        game.check_hits(self.world, [self.player])
        self.assertTrue(self.player["alive"])
        self.assertEqual(len(self.player["projectiles"]), 1)

    def test_shoot_animation_finishes(self):
        game.fire_bullet(self.canvas, self.player)
        for _ in range(MUZZLE_FLASH_FRAME_COUNT):
            self.player["shoot_animation"]["next_frame_time"] = 0
            game.update_shoot_animation(self.canvas, self.player)
        self.assertIsNone(self.player["shoot_animation"])

    def test_reload_ring_visible_while_reloading(self):
        game.fire_bullet(self.canvas, self.player)
        game.update_reload_indicator(self.canvas, self.player)
        self.assertEqual(self.canvas.itemcget(self.player["reload_ring"], "state"), "normal")

    def test_reload_ring_hidden_when_ready(self):
        self.player["state"]["last_shot_time"] = time.time() - game.SHOOT_COOLDOWN
        game.update_reload_indicator(self.canvas, self.player)
        self.assertEqual(self.canvas.itemcget(self.player["reload_ring"], "state"), "hidden")


class TestSounds(unittest.TestCase):
    def test_move_sound_starts_and_stops(self):
        sounds = {"move": None, "idle": None, "ambient": []}
        with mock.patch.object(game, "MOVE_SOUND") as move_sound:
            game.update_move_sound(sounds, [{"moving": True}])
            self.assertIsNotNone(sounds["move"])
            move_sound.play.assert_called_once()
            game.update_move_sound(sounds, [{"moving": False}])
            self.assertIsNone(sounds["move"])

    def test_ambient_sounds_are_rescheduled(self):
        sounds = {"ambient": [], "next_explosion_time": 0, "next_plane_time": 0}
        with mock.patch.object(game, "DISTANT_EXPLOSION_SOUND"), mock.patch.object(game, "PLANE_SOUND"):
            game.update_ambient_sounds(sounds)
        self.assertEqual(len(sounds["ambient"]), 2)
        self.assertGreater(sounds["next_explosion_time"], time.time())
        self.assertGreater(sounds["next_plane_time"], time.time())


class TestEndMatch(unittest.TestCase):
    def setUp(self):
        scoreboard.session_wins.clear()
        self.match = {
            "root": shared_root,
            "sounds": {"move": None, "idle": None, "ambient": []},
            "active": True,
        }

    def test_winner_gets_a_point(self):
        with mock.patch.object(shared_root, "after") as after:
            game.end_match(self.match, [{"name": "Noah"}])
        self.assertEqual(scoreboard.session_wins["Noah"], 1)
        self.assertEqual(after.call_args[0][3], "Noah wins!")

    def test_draw_without_survivors(self):
        with mock.patch.object(shared_root, "after") as after:
            game.end_match(self.match, [])
        self.assertEqual(scoreboard.session_wins, {})
        self.assertEqual(after.call_args[0][3], "Draw!")

    def test_key_bindings_removed(self):
        game.bind_key_tracking(shared_root, set())
        with mock.patch.object(shared_root, "after"):
            game.end_match(self.match, [])
        self.assertEqual(shared_root.bind("<KeyPress>"), "")

    def test_result_screen_skipped_after_leave(self):
        self.match["active"] = False
        with mock.patch.object(game, "show_winner_screen") as show:
            game.show_result_screen(self.match, "egal")
        show.assert_not_called()


class TestUniqueNames(unittest.TestCase):
    def test_different_names_unchanged(self):
        self.assertEqual(game.make_unique_names(["Noah", "Jun"]), ["Noah", "Jun"])

    def test_duplicate_gets_number(self):
        self.assertEqual(game.make_unique_names(["Noah", "Noah", "Noah"]), ["Noah", "Noah 2", "Noah 3"])

    def test_ignores_upper_lower_case(self):
        self.assertEqual(game.make_unique_names(["Noah", "noah"]), ["Noah", "noah 2"])

    def test_number_already_taken(self):
        self.assertEqual(game.make_unique_names(["Noah 2", "Noah", "Noah"]), ["Noah 2", "Noah", "Noah 3"])


class TestShootKeys(unittest.TestCase):
    def test_letter_binds_lower_and_upper(self):
        self.assertEqual(game.shoot_key_sequences("e"), ["<KeyPress-e>", "<KeyPress-E>"])

    def test_special_key_binds_once(self):
        self.assertEqual(game.shoot_key_sequences("Control_R"), ["<KeyPress-Control_R>"])

    def test_caps_lock_binding_exists_and_is_removed(self):
        world = make_world()
        make_player(world, (400, 300))
        self.assertNotEqual(shared_root.bind("<KeyPress-E>"), "")
        match = {"root": shared_root, "sounds": {"move": None, "idle": None, "ambient": []}}
        game.stop_match(match)
        self.assertEqual(shared_root.bind("<KeyPress-e>"), "")
        self.assertEqual(shared_root.bind("<KeyPress-E>"), "")


class TestKeyTracking(unittest.TestCase):
    def test_press_and_release(self):
        keys_pressed = set()
        handlers = {}
        fake_root = mock.Mock()
        fake_root.bind.side_effect = lambda sequence, handler: handlers.__setitem__(sequence, handler)
        game.bind_key_tracking(fake_root, keys_pressed)

        handlers["<KeyPress>"](mock.Mock(keysym="W"))
        handlers["<KeyPress>"](mock.Mock(keysym="Up"))
        self.assertEqual(keys_pressed, {"w", "up"})  # klein geschrieben wie in PLAYER_KEYS
        handlers["<KeyRelease>"](mock.Mock(keysym="W"))
        self.assertEqual(keys_pressed, {"up"})

    def test_focus_loss_releases_all_keys(self):
        keys_pressed = set()
        handlers = {}
        fake_root = mock.Mock()
        fake_root.bind.side_effect = lambda sequence, handler: handlers.__setitem__(sequence, handler)
        game.bind_key_tracking(fake_root, keys_pressed)

        handlers["<KeyPress>"](mock.Mock(keysym="w"))
        handlers["<FocusOut>"](mock.Mock())  # Alt+Tab
        self.assertEqual(keys_pressed, set())

    def test_focus_binding_removed_at_match_end(self):
        game.bind_key_tracking(shared_root, set())
        game.stop_match({"root": shared_root, "sounds": {"move": None, "idle": None, "ambient": []}})
        self.assertEqual(shared_root.bind("<FocusOut>"), "")


class TestNoAudio(unittest.TestCase):
    def test_init_audio_fails_gracefully(self):
        with mock.patch.object(game.pygame.mixer, "init", side_effect=game.pygame.error("no audio device")):
            self.assertFalse(game.init_audio())

    def test_silent_sound_without_audio(self):
        with mock.patch.object(game, "AUDIO_AVAILABLE", False):
            sound = game.load_sound(game.SHOOT_SOUND_PATH, 0.5)
        self.assertIsInstance(sound, game.SilentSound)
        self.assertIsNone(sound.play(loops=-1))

    def test_match_sounds_work_silently(self):
        silent = game.SilentSound()
        names = ["IDLE_TANK_SOUND", "BREEZE_SOUND", "MOVE_SOUND", "DISTANT_EXPLOSION_SOUND", "PLANE_SOUND"]
        with mock.patch.multiple(game, **{name: silent for name in names}):
            sounds = game.start_match_sounds()
            sounds["next_explosion_time"] = sounds["next_plane_time"] = 0
            game.update_ambient_sounds(sounds)
            game.update_move_sound(sounds, [{"moving": True}])
            game.update_move_sound(sounds, [{"moving": False}])
            game.stop_match_sounds(sounds)  # darf keinen Fehler werfen

    def test_shooting_works_silently(self):
        world = make_world()
        player = make_player(world, (400, 300))
        with mock.patch.object(game, "SHOOT_SOUND", game.SilentSound()):
            game.fire_bullet(world["canvas"], player)
        self.assertEqual(len(player["projectiles"]), 1)


# ============================================================================
# scoreboard.py
# ============================================================================

class TestScoreboard(unittest.TestCase):
    def setUp(self):
        scoreboard.session_wins.clear()

    def test_register_players_start_at_zero(self):
        scoreboard.register_players(["A", "B"])
        self.assertEqual(scoreboard.session_wins, {"A": 0, "B": 0})

    def test_register_keeps_existing_wins(self):
        scoreboard.record_win("A")
        scoreboard.register_players(["A"])
        self.assertEqual(scoreboard.session_wins["A"], 1)

    def test_record_win_counts_up(self):
        scoreboard.record_win("A")
        scoreboard.record_win("A")
        self.assertEqual(scoreboard.session_wins["A"], 2)

    def test_record_win_for_unknown_player(self):
        scoreboard.record_win("Neu")
        self.assertEqual(scoreboard.session_wins["Neu"], 1)

    def test_leaderboard_sorted_by_wins_then_name(self):
        scoreboard.register_players(["charlie", "Bravo", "alpha"])
        scoreboard.record_win("charlie")
        self.assertEqual(scoreboard.get_leaderboard(), [("charlie", 1), ("alpha", 0), ("Bravo", 0)])

    def test_empty_leaderboard(self):
        self.assertEqual(scoreboard.get_leaderboard(), [])


# ============================================================================
# build_tank_images.py und utils.py
# ============================================================================

class TestBuildTankImages(unittest.TestCase):
    def test_all_colors_same_hull_width(self):
        # Die Bildflaeche darf je nach Rohr/Farbe verschieden gross sein -- der Rumpf nicht.
        # Nach dem Skalieren misst man wegen weicher Kanten ein paar Pixel mehr als
        # HULL_PX, darum wird nur geprueft, dass alle Rumpfe fast gleich breit sind.
        widths = {}
        for color in game.PLAYER_COLORS.values():
            straight_path, diagonal_path = TANK_BASE_PATHS[color]
            for path, rotated_45 in ((straight_path, False), (diagonal_path, True)):
                widths[(color, rotated_45)] = _hull_metrics(_load_scaled(path, rotated_45), rotated_45)[2]
        self.assertLessEqual(max(widths.values()) - min(widths.values()), 4, widths)
        self.assertAlmostEqual(min(widths.values()), HULL_PX, delta=HULL_PX * 0.2)

    def test_tank_images_are_square(self):
        for angle, img in get_tank_images("red").items():
            self.assertEqual(img.width(), img.height(), f"angle {angle}")

    def test_muzzle_flash_frames(self):
        for color in game.PLAYER_COLORS.values():
            frames = get_muzzle_flash_frames(color)
            self.assertEqual(set(frames), set(ANGLE_STEPS), color)
            for angle, frame_list in frames.items():
                self.assertEqual(len(frame_list), MUZZLE_FLASH_FRAME_COUNT, f"{color} {angle}")

    def test_muzzle_flash_frames_are_square(self):
        # quadratisch -> das Drehzentrum bleibt beim Drehen in der Bildmitte
        for angle, frame_list in get_muzzle_flash_frames("blue").items():
            for frame in frame_list:
                self.assertEqual(frame.width(), frame.height(), f"angle {angle}")

    def test_destroyed_images_all_angles(self):
        wrecks = get_destroyed_tank_images()
        self.assertEqual(set(wrecks), set(ANGLE_STEPS))
        for angle, img in wrecks.items():
            self.assertGreater(img.width(), 0, f"angle {angle}")

    def test_forward_vector_zero_points_up(self):
        fx, fy = _forward_vector(0)
        self.assertAlmostEqual(fx, 0)
        self.assertAlmostEqual(fy, -1)


class TestResourcePath(unittest.TestCase):
    def test_normal_script_uses_project_folder(self):
        project_dir = os.path.dirname(os.path.abspath(utils.__file__))
        self.assertEqual(utils.resource_path("Assets/Mine.png"), os.path.join(project_dir, "Assets/Mine.png"))

    def test_assets_exist(self):
        self.assertTrue(os.path.exists(utils.resource_path("Assets/Mine.png")))
        self.assertTrue(os.path.exists(utils.resource_path("Sounds/Shoot.wav")))

    def test_exe_uses_meipass(self):
        with mock.patch.object(sys, "_MEIPASS", "C:/temp_exe", create=True):
            self.assertEqual(utils.resource_path("Sounds/Shoot.wav"), os.path.join("C:/temp_exe", "Sounds/Shoot.wav"))


class TestBlurredBackground(unittest.TestCase):
    def test_size_matches_window(self):
        self.assertEqual(utils.blurred_city_image(320, 180).size, (320, 180))

    def test_darker_than_original(self):
        blurred = utils.blurred_city_image(160, 90)
        original = Image.open(utils.CITY_BACKGROUND_PATH).convert("L").resize((160, 90))
        mean = lambda img: sum(img.convert("L").getdata()) / (img.width * img.height)
        self.assertLess(mean(blurred), mean(original))

    def test_result_is_cached(self):
        self.assertIs(utils.blurred_city_image(200, 100), utils.blurred_city_image(200, 100))

    def test_background_is_lowest_canvas_item(self):
        canvas = tk.Canvas(shared_root)
        utils.add_blurred_background(canvas, 200, 100)
        first = canvas.find_all()[0]
        self.assertEqual(canvas.type(first), "image")
        self.assertEqual(canvas.itemcget(first, "image"), str(canvas.background_img))

    def test_winner_screen_has_background(self):
        from winner_screen import show_winner_screen
        with mock.patch.object(shared_root, "winfo_width", return_value=400), \
                mock.patch.object(shared_root, "winfo_height", return_value=300):
            show_winner_screen(shared_root, "Noah wins!", [("Noah", 1)], lambda: None, lambda: None)
        canvas = [w for w in shared_root.winfo_children() if isinstance(w, tk.Canvas)][-1]
        self.assertEqual(canvas.type(canvas.find_all()[0]), "image")  # Hintergrund liegt ganz unten
        texts = [canvas.itemcget(i, "text") for i in canvas.find_all() if canvas.type(i) == "text"]
        self.assertIn("Noah wins!", texts)


if __name__ == "__main__":
    unittest.main()
### Claude code für Unit-Tests (die ganze Datei ist von Claude)
