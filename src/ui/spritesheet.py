import pygame


class SpriteSheet:
    def __init__(self, filename):
        try:
            self.sheet = pygame.image.load(filename).convert_alpha()
        except pygame.error:
            self.sheet = pygame.Surface((16, 16))
            self.sheet.fill((255, 0, 255))

    def get_image_by_grid(self, col, row, scale):
        w, h, m = 16, 16, 1
        x = col * (w + m)
        y = row * (h + m)
        image = pygame.Surface((w, h), pygame.SRCALPHA)
        image.blit(self.sheet, (0, 0), (x, y, w, h))
        return pygame.transform.scale(image, (w * scale, h * scale))

    def get_equipped_image_by_grid(self, layers, scale):
        w, h, m = 16, 16, 1
        composite = pygame.Surface((w, h), pygame.SRCALPHA)
        for grid in layers:
            if grid is not None:
                x, y = grid[0] * (w + m), grid[1] * (h + m)
                composite.blit(self.sheet.subsurface((x, y, w, h)), (0, 0))
        return pygame.transform.scale(composite, (w * scale, h * scale))
