import pygame
import sys
import random
import time
from queue import Queue

# Constants
WIDTH, HEIGHT = 600, 700
ROWS, COLS = 9, 9
CELL_SIZE = WIDTH // COLS
WALL_THICKNESS = 8
TOP_BAR = 100
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BROWN = (139, 69, 19)
BLUE = (50, 50, 255)
RED = (255, 50, 50)
GRAY = (200, 200, 200)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Quoridor Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)

class Player:
    def _init_(self, row, col, goal_row):
        self.row = row
        self.col = col
        self.goal_row = goal_row
        self.walls = 10

    def move(self, row, col):
        self.row = row
        self.col = col

class Game:
    def _init_(self, ai_depth=3):
        self.board = [[0] * COLS for _ in range(ROWS)]
        self.p1 = Player(0, COLS // 2, ROWS - 1)
        self.p2 = Player(ROWS - 1, COLS // 2, 0)
        self.turn = 0
        self.walls = set()
        self.mode = None
        self.wall_orientation = 'h'
        self.mp_btn = None
        self.ai_btn = None
        self.ai_depth = ai_depth
        self.update_distances()

    def update_distances(self):
        """Update path distances for both players"""
        self.p1_distance = self.bfs(self.p1, self.p1.goal_row)
        self.p2_distance = self.bfs(self.p2, self.p2.goal_row)

    def draw_board(self):
        screen.fill(WHITE)

        # Draw grid
        for row in range(ROWS):
            for col in range(COLS):
                rect = pygame.Rect(col * CELL_SIZE, TOP_BAR + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                pygame.draw.rect(screen, BLACK, rect, 1)

        # Highlight valid moves
        current_player = self.p1 if self.turn == 0 else self.p2
        for r, c in self.valid_moves(current_player):
            highlight_rect = pygame.Rect(c * CELL_SIZE + 5, TOP_BAR + r * CELL_SIZE + 5, CELL_SIZE - 10, CELL_SIZE - 10)
            pygame.draw.rect(screen, GRAY, highlight_rect)

        # Draw walls
        for x, y, o in self.walls:
            if o == 'h':
                wall_rect = pygame.Rect(x * CELL_SIZE, TOP_BAR + y * CELL_SIZE + CELL_SIZE - WALL_THICKNESS // 2, CELL_SIZE * 2, WALL_THICKNESS)
            else:
                wall_rect = pygame.Rect(x * CELL_SIZE + CELL_SIZE - WALL_THICKNESS // 2, TOP_BAR + y * CELL_SIZE, WALL_THICKNESS, CELL_SIZE * 2)
            pygame.draw.rect(screen, BROWN, wall_rect)

        # Draw players
        p1_x = self.p1.col * CELL_SIZE + CELL_SIZE // 2
        p1_y = TOP_BAR + self.p1.row * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, BLUE, (p1_x, p1_y), CELL_SIZE // 3)

        p2_x = self.p2.col * CELL_SIZE + CELL_SIZE // 2
        p2_y = TOP_BAR + self.p2.row * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(screen, RED, (p2_x, p2_y), CELL_SIZE // 3)

        # Draw wall counters
        p1_text = font.render(f"P1 Walls: {self.p1.walls}", True, BLUE)
        p2_text = font.render(f"P2 Walls: {self.p2.walls}", True, RED)
        screen.blit(p1_text, (10, 10))
        screen.blit(p2_text, (WIDTH - 160, 10))

        # Draw buttons if mode is not selected
        if self.mode is None:
            self.mp_btn = pygame.Rect(WIDTH // 4 - 50, 30, 100, 40)
            self.ai_btn = pygame.Rect(3 * WIDTH // 4 - 50, 30, 100, 40)
            pygame.draw.rect(screen, BLUE, self.mp_btn)
            pygame.draw.rect(screen, RED, self.ai_btn)
            mp_text = font.render("Multiplayer", True, WHITE)
            ai_text = font.render("AI", True, WHITE)
            screen.blit(mp_text, (self.mp_btn.x + 5, self.mp_btn.y + 5))
            screen.blit(ai_text, (self.ai_btn.x + 25, self.ai_btn.y + 5))

    def valid_moves(self, player):
        opponent = self.p2 if player == self.p1 else self.p1
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        moves = []
        for dr, dc in directions:
            nr, nc = player.row + dr, player.col + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                if not self.blocked(player.row, player.col, nr, nc):
                    if (nr, nc) == (opponent.row, opponent.col):
                        jr, jc = nr + dr, nc + dc
                        if 0 <= jr < ROWS and 0 <= jc < COLS and not self.blocked(nr, nc, jr, jc):
                            moves.append((jr, jc))
                        else:
                            for ddr, ddc in [(-dc, -dr), (dc, dr)]:
                                diag_r, diag_c = nr + ddr, nc + ddc
                                if 0 <= diag_r < ROWS and 0 <= diag_c < COLS and not self.blocked(nr, nc, diag_r, diag_c):
                                    moves.append((diag_r, diag_c))
                    else:
                        moves.append((nr, nc))
        return moves

    def blocked(self, r1, c1, r2, c2):
        for x, y, o in self.walls:
            if o == 'h' and ((r1 == y and r2 == y + 1) or (r2 == y and r1 == y + 1)) and (x == c1 or x == c2):
                return True
            if o == 'v' and ((c1 == x and c2 == x + 1) or (c2 == x and c1 == x + 1)) and (y == r1 or y == r2):
                return True
        return False

    def valid_wall_placement(self, x, y, orientation):
        if x >= COLS - 1 or y >= ROWS - 1:
            return False
        if (x, y, orientation) in self.walls:
            return False

        self.walls.add((x, y, orientation))
        p1_path = self.bfs(self.p1, self.p1.goal_row)
        p2_path = self.bfs(self.p2, self.p2.goal_row)
        self.walls.remove((x, y, orientation))

        return p1_path != float('inf') and p2_path != float('inf')

    def place_wall(self, x, y):
        current_player = self.p1 if self.turn == 0 else self.p2
        if current_player.walls > 0 and self.valid_wall_placement(x, y, self.wall_orientation):
            self.walls.add((x, y, self.wall_orientation))
            current_player.walls -= 1
            self.update_distances()
            self.turn = 1 - self.turn

    def bfs(self, start, goal_row):
        q = Queue()
        q.put((start.row, start.col, 0))
        visited = set()
        while not q.empty():
            r, c, d = q.get()
            if r == goal_row:
                return d
            visited.add((r, c))
            for nr, nc in self.valid_moves(Player(r, c, goal_row)):
                if (nr, nc) not in visited:
                    q.put((nr, nc, d + 1))
        return float('inf')

    def evaluate_position(self):
        """Evaluate the current board position from AI's perspective"""
        p1_dist = self.bfs(self.p1, self.p1.goal_row)
        p2_dist = self.bfs(self.p2, self.p2.goal_row)
        
        # Favor positions where AI is closer to goal and player is farther
        score = (self.p2_distance - p2_dist) * 2 - (p1_dist - self.p1_distance)
        
        # Add small random factor to avoid identical evaluations
        score += random.uniform(-0.1, 0.1)
        
        return score

    def ai_turn(self):
        # 1. First check if AI can win immediately
        winning_moves = [move for move in self.valid_moves(self.p2) 
                        if move[0] == self.p2.goal_row]
        if winning_moves:
            self.p2.move(*winning_moves[0])
            self.update_distances()
            self.turn = 0
            return

        # 2. Try to find the best move
        best_score = -float('inf')
        best_move = None
        
        for move in self.valid_moves(self.p2):
            self.p2.move(*move)
            score = self.evaluate_position()
            self.p2.move(self.p2.row, self.p2.col)  # Revert move
            
            if score > best_score:
                best_score = score
                best_move = move

        if best_move:
            self.p2.move(*best_move)
            self.update_distances()
            self.turn = 0
            return

        # 3. If no good moves, try to place a wall
        if self.p2.walls > 0:
            best_wall_score = -float('inf')
            best_wall = None
            
            # Try both orientations
            for orientation in ['h', 'v']:
                for x in range(COLS - 1):
                    for y in range(ROWS - 1):
                        if self.valid_wall_placement(x, y, orientation):
                            self.walls.add((x, y, orientation))
                            score = self.evaluate_position()
                            self.walls.remove((x, y, orientation))
                            
                            if score > best_wall_score:
                                best_wall_score = score
                                best_wall = (x, y, orientation)
            
            # Only place wall if it's significantly beneficial
            if best_wall and best_wall_score > 1:
                self.place_wall(*best_wall)
                return

        # If no good moves or walls, just pass
        self.turn = 0

    def check_win(self):
        if self.p1.row == self.p1.goal_row:
            return 1
        if self.p2.row == self.p2.goal_row:
            return 2
        return 0

def display_winner(screen, winner):
    screen.fill(WHITE)
    text = font.render(f"Player {winner} wins! Press R to restart.", True, BLACK)
    text_rect = text.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(text, text_rect)
    pygame.display.flip()

def main():
    game = Game(ai_depth=3)
    running = True
    game_over = False

    while running:
        clock.tick(FPS)
        game.draw_board()
        pygame.display.flip()

        if game.mode == "AI" and game.turn == 1 and not game_over:
            game.ai_turn()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    main()
                    return
                elif event.key == pygame.K_TAB:
                    game.wall_orientation = 'v' if game.wall_orientation == 'h' else 'h'

            if game.mode is None and event.type == pygame.MOUSEBUTTONDOWN:
                if game.mp_btn.collidepoint(event.pos):
                    game.mode = "MP"
                elif game.ai_btn.collidepoint(event.pos):
                    game.mode = "AI"

            if event.type == pygame.MOUSEBUTTONDOWN and game.mode is not None and not game_over:
                x, y = event.pos
                row = (y - TOP_BAR) // CELL_SIZE
                col = x // CELL_SIZE

                if TOP_BAR <= y < HEIGHT:
                    current_player = game.p1 if game.turn == 0 else game.p2
                    if (row, col) in game.valid_moves(current_player):
                        current_player.move(row, col)
                        game.update_distances()
                        game.turn = 1 - game.turn
                    else:
                        grid_x, grid_y = col, row
                        if game.valid_wall_placement(grid_x, grid_y, game.wall_orientation):
                            game.place_wall(grid_x, grid_y)

        winner = game.check_win()
        if winner:
            display_winner(screen, winner)
            game_over = True

if _name_ == "_main_":
    main() 
    """ edit this code make ai don't go through walls also use walls to block me"""