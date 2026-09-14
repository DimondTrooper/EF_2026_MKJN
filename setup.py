import pygame

import settings

SWATCH_SIZE = 60
SWATCH_GAP = 20
ROW_GAP = 110
FIRST_ROW_Y = 220


def _swatch_rects(num_colors, center_x):
    total_width = num_colors * SWATCH_SIZE + (num_colors - 1) * SWATCH_GAP
    start_x = center_x - total_width // 2
    return [
        pygame.Rect(start_x + i * (SWATCH_SIZE + SWATCH_GAP), 0, SWATCH_SIZE, SWATCH_SIZE)
        for i in range(num_colors)
    ]


def run_setup(screen, num_players):
    """Farbauswahl-Screen. Jeder Spieler wählt per Mausklick eine eigene Farbe.
    Gibt eine Liste von RGB-Farben (eine pro Spieler) zurück, sobald alle
    gewählt haben und "Weiter" gedrückt wird. Gibt None zurück, wenn das
    Fenster geschlossen oder ESC gedrückt wird."""
    clock = pygame.time.Clock()
    font_title = pygame.font.SysFont(settings.FONT_NAME, settings.FONT_SIZE_TITLE, bold=True)
    font_normal = pygame.font.SysFont(settings.FONT_NAME, settings.FONT_SIZE_NORMAL)
    font_small = pygame.font.SysFont(settings.FONT_NAME, settings.FONT_SIZE_SMALL)

    center_x = screen.get_width() // 2
    swatch_rects = _swatch_rects(len(settings.PLAYER_COLORS), center_x)

    chosen = [None] * num_players  # Index in settings.PLAYER_COLORS pro Spieler

    button_rect = pygame.Rect(0, 0, 220, 60)
    button_rect.center = (center_x, FIRST_ROW_Y + (num_players - 1) * ROW_GAP + 140)

    while True:
        all_chosen = all(c is not None for c in chosen)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return None
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and all_chosen:
                return [settings.PLAYER_COLORS[i][1] for i in chosen]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for p in range(num_players):
                    row_y = FIRST_ROW_Y + p * ROW_GAP
                    for i, rect in enumerate(swatch_rects):
                        if not rect.move(0, row_y).collidepoint(mouse_pos):
                            continue
                        if i in chosen and chosen.index(i) != p:
                            continue  # Farbe schon von anderem Spieler gewählt
                        chosen[p] = None if chosen[p] == i else i
                if all(c is not None for c in chosen) and button_rect.collidepoint(mouse_pos):
                    return [settings.PLAYER_COLORS[i][1] for i in chosen]

        screen.fill(settings.BG_COLOR)

        title_surf = font_title.render("Wähle deine Farbe", True, settings.TEXT_COLOR)
        screen.blit(title_surf, title_surf.get_rect(center=(center_x, 100)))

        for p in range(num_players):
            row_y = FIRST_ROW_Y + p * ROW_GAP
            label = font_normal.render(f"Spieler {p + 1}", True, settings.TEXT_COLOR)
            screen.blit(label, label.get_rect(midbottom=(center_x, row_y - 15)))

            for i, (name, color) in enumerate(settings.PLAYER_COLORS):
                rect = swatch_rects[i].move(0, row_y)
                taken_by_other = i in chosen and chosen.index(i) != p

                pygame.draw.rect(screen, color, rect, border_radius=8)
                if taken_by_other:
                    overlay = pygame.Surface(rect.size, pygame.SRCALPHA)
                    overlay.fill((0, 0, 0, 160))
                    screen.blit(overlay, rect.topleft)
                if chosen[p] == i:
                    pygame.draw.rect(screen, settings.HIGHLIGHT_COLOR, rect, width=4, border_radius=8)

                name_surf = font_small.render(name, True, settings.MUTED_TEXT_COLOR)
                screen.blit(name_surf, name_surf.get_rect(midtop=(rect.centerx, rect.bottom + 6)))

        button_color = settings.BUTTON_ACTIVE_COLOR if all_chosen else settings.PANEL_COLOR
        button_text_color = settings.TEXT_COLOR if all_chosen else settings.MUTED_TEXT_COLOR
        pygame.draw.rect(screen, button_color, button_rect, border_radius=10)
        button_text = font_normal.render("Weiter", True, button_text_color)
        screen.blit(button_text, button_text.get_rect(center=button_rect.center))

        pygame.display.flip()
        clock.tick(settings.FPS)


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_caption(settings.TITLE)
    test_screen = pygame.display.set_mode((settings.WIDTH, settings.HEIGHT))
    result = run_setup(test_screen, num_players=2)
    print("Gewählte Farben:", result)
    pygame.quit()
