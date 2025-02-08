import pygame

class EndGameHandler:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.font = game.font
        self.WIDTH = game.WIDTH
        self.HEIGHT = game.HEIGHT
        self.clock = game.clock

    def end_game(self):
        self.game.add_message("Вітаємо! Ви досягли 100-го рівня та завершили гру!")
        running = True
        while running:
            #self.screen.fill((0, 0, 0))
            end_text = self.font.render("Ви перемогли! Гра завершена.", True, (255, 255, 255))
            end_rect = end_text.get_rect(center=(self.WIDTH // 2, self.HEIGHT // 2))
            self.screen.blit(end_text, end_rect)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
        pygame.quit()
        exit()

    def game_over(self):
        self.game.add_message("Гра закінчена! Ви зазнали поразки.")
        self.game.add_message("Ваші характеристики скинуто до початкових значень.")
        self.wait(3000) 
        self.game.restart_game()
        self.game.game_state = 'exploration'

    def wait(self, duration):
        wait_start = pygame.time.get_ticks()
        while pygame.time.get_ticks() - wait_start < duration:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
            self.game.renderer.draw_room()
            pygame.display.flip()
            self.clock.tick(60)
