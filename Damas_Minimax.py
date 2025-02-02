import pygame
import sys

pygame.init()

screen_width = 400
screen_height = 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Juego de Damas 4x4")

# Colores
BOARD_BLACK = (0, 0, 0)               # Casillas negras
BOARD_WHITE = (255, 255, 255)         # Casillas blancas
GRAY = (200, 200, 200)                # Fondo del menú
SELECT_COLOR = (150, 150, 255)        # Resalte en el menú
VINO_PIECE = (128, 0, 32)             # Piezas de la IA (vinotinto)
PLAYER_PIECE = (100, 100, 100)        # Piezas del jugador (grises)
MOVEMENT_COUNTER = (0, 128, 255)      # Color del contador de turnos

# Tamaño del tablero
board_size = 4
square_size = screen_width // board_size

# Representación de las piezas:
# Cada pieza se representa como una tupla: (color, is_king)
# Inicialmente, ninguna pieza es "dama" (False)
pieces = {
    (0, 0): (VINO_PIECE, False),
    (0, 2): (VINO_PIECE, False),
    (3, 1): (PLAYER_PIECE, False),
    (3, 3): (PLAYER_PIECE, False),
}

selected_piece = None
# Para evitar confusiones, usamos "player" para el jugador y "vino" para la IA.
turn = 'player'  
turn_counter = 0

def draw_board():
    for row in range(board_size):
        for col in range(board_size):
            if (row + col) % 2 == 0:
                pygame.draw.rect(screen, BOARD_BLACK, (col * square_size, row * square_size, square_size, square_size))
            else:
                pygame.draw.rect(screen, BOARD_WHITE, (col * square_size, row * square_size, square_size, square_size))
            # Dibuja una señal en las casillas adyacentes a la pieza seleccionada
            if selected_piece:
                selected_row, selected_col = selected_piece
                if (abs(selected_row - row) == 1 and abs(selected_col - col) == 1) and ((row + col) % 2 == 0):
                    pygame.draw.circle(screen, BOARD_WHITE, (col * square_size + square_size // 2, row * square_size + square_size // 2), 5)

def draw_pieces():
    for (row, col), piece in pieces.items():
        color, is_king = piece
        pygame.draw.circle(screen, color, (col * square_size + square_size // 2, row * square_size + square_size // 2), square_size // 3)
        # Si la pieza es dama, se dibuja un marcador (círculo pequeño negro)
        if is_king:
            pygame.draw.circle(screen, BOARD_BLACK, (col * square_size + square_size // 2, row * square_size + square_size // 2), square_size // 8)

def show_movement_counter():
    font = pygame.font.Font(None, 36)
    turn_text = f"Turnos: {turn_counter}"
    text_surface = font.render(turn_text, True, MOVEMENT_COUNTER)
    screen.blit(text_surface, (10, 10))

def show_menu():
    options = ["Jugar", "Salir"]
    selected_index = 0

    while True:
        screen.fill(GRAY)
        font = pygame.font.Font(None, 48)
        title_text = font.render("Juego de Damas", True, BOARD_BLACK)
        title_margin_top = 80
        screen.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, title_margin_top))

        font_medium = pygame.font.Font(None, 36)
        for i, option in enumerate(options):
            option_text = font_medium.render(option, True, BOARD_BLACK)
            option_rect = option_text.get_rect(center=(screen_width // 2, 150 + i * 100))
            if i == selected_index:
                pygame.draw.rect(screen, SELECT_COLOR, option_rect.inflate(20, 20))
            screen.blit(option_text, option_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected_index = (selected_index - 1) % len(options)
                elif event.key == pygame.K_DOWN:
                    selected_index = (selected_index + 1) % len(options)
                elif event.key == pygame.K_RETURN:
                    if selected_index == 0:
                        return
                    elif selected_index == 1:
                        pygame.quit()
                        sys.exit()

# Función que promueve a dama (rey) si la pieza llega a la fila contraria.
def promote_piece(row, piece):
    color, is_king = piece
    if not is_king:
        # Las piezas del jugador (grises) deben llegar a la fila 0 para promocionarse.
        if color == PLAYER_PIECE and row == 0:
            return (color, True)
        # Las piezas vinotinto deben llegar a la última fila (board_size - 1) para promocionarse.
        if color == VINO_PIECE and row == board_size - 1:
            return (color, True)
    return piece

# Función para manejar el movimiento mediante el mouse.
def handle_mouse_click(pos):
    global selected_piece, turn, turn_counter
    col = pos[0] // square_size
    row = pos[1] // square_size

    if selected_piece is None:
        # Seleccionar pieza si coincide con el turno.
        if (row, col) in pieces:
            p_color, _ = pieces[(row, col)]
            if (p_color == PLAYER_PIECE and turn == 'player') or (p_color == VINO_PIECE and turn == 'vino'):
                selected_piece = (row, col)
    else:
        selected_row, selected_col = selected_piece
        # Movimiento normal (una casilla en diagonal)
        if (abs(selected_row - row) == 1 and abs(selected_col - col) == 1):
            moving_piece = pieces[selected_piece]
            color, is_king = moving_piece
            # Para piezas NO promocionadas, se restringe el movimiento hacia adelante.
            if not is_king:
                if (color == PLAYER_PIECE and row >= selected_row) or (color == VINO_PIECE and row <= selected_row):
                    selected_piece = None
                    return
            # Mueve la pieza y aplica la promoción si corresponde.
            new_piece = promote_piece(row, moving_piece)
            pieces[(row, col)] = new_piece
            del pieces[selected_piece]
            turn = 'player' if turn == 'vino' else 'vino'
            turn_counter += 1
        else:
            # Intento de captura:
            if (row, col) in pieces and pieces[(row, col)][0] != pieces[selected_piece][0]:
                behind_row = row + (row - selected_row)
                behind_col = col + (col - selected_col)
                if 0 <= behind_row < board_size and 0 <= behind_col < board_size and (behind_row, behind_col) not in pieces:
                    moving_piece = pieces[selected_piece]
                    new_piece = promote_piece(behind_row, moving_piece)
                    del pieces[(row, col)]
                    pieces[(behind_row, behind_col)] = new_piece
                    del pieces[selected_piece]
                    turn = 'player' if turn == 'vino' else 'vino'
                    turn_counter += 1
        selected_piece = None
        check_winner()

def check_winner():
    vino_count = sum(1 for piece in pieces.values() if piece[0] == VINO_PIECE)
    player_count = sum(1 for piece in pieces.values() if piece[0] == PLAYER_PIECE)
    check_draw()
    if vino_count == 0:
        show_winner_message("Gano el jugador|vinotinto")
    elif player_count == 0:
        show_winner_message("Gano el jugador|grises")

def check_draw():
    global turn_counter
    if turn_counter >= 64:
        show_winner_message("¡Empate!|Número máximo|de turnos alcanzado.")

def show_winner_message(winner):
    screen.fill(GRAY)
    font = pygame.font.Font(None, 48)
    lines = winner.split("|")
    y_offset = screen_height // 2 - len(lines) * 24
    for line in lines:
        text_surface = font.render(line, True, BOARD_BLACK)
        text_rect = text_surface.get_rect(center=(screen_width // 2, y_offset))
        screen.blit(text_surface, text_rect)
        y_offset += 50
    pygame.display.flip()
    pygame.time.wait(3000)
    pygame.quit()
    sys.exit()

# La IA utiliza Minimax con poda alfa-beta.
def apply_ai_move():
    global turn, turn_counter
    best_move = minimax(pieces, 3, True, float('-inf'), float('inf'))
    if best_move:
        pieces.clear()
        pieces.update(best_move)
        turn = 'player'
        turn_counter += 1
    check_winner()

def evaluate_board(board):
    vino_count = sum(1 for piece in board.values() if piece[0] == VINO_PIECE)
    player_count = sum(1 for piece in board.values() if piece[0] == PLAYER_PIECE)
    return vino_count - player_count

def generate_moves(board, color):
    moves = []
    capture_moves = []
    for (row, col), piece in board.items():
        if piece[0] == color:
            color_piece, is_king = piece
            # Direcciones permitidas según si es dama o no.
            if is_king:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            else:
                if color == PLAYER_PIECE:
                    directions = [(-1, -1), (-1, 1)]  # Las piezas del jugador solo avanzan "hacia arriba" (fila menor)
                else:
                    directions = [(1, -1), (1, 1)]      # Las piezas vinotinto solo avanzan "hacia abajo" (fila mayor)
            for d_row, d_col in directions:
                new_row = row + d_row
                new_col = col + d_col
                if 0 <= new_row < board_size and 0 <= new_col < board_size:
                    if (new_row, new_col) not in board:
                        new_board = board.copy()
                        del new_board[(row, col)]
                        new_piece = promote_piece(new_row, piece)
                        new_board[(new_row, new_col)] = new_piece
                        moves.append(new_board)
                    # Verifica posibilidad de captura.
                    enemy_row = row + d_row
                    enemy_col = col + d_col
                    behind_row = enemy_row + d_row
                    behind_col = enemy_col + d_col
                    if (0 <= enemy_row < board_size and 0 <= enemy_col < board_size and
                        (enemy_row, enemy_col) in board and board[(enemy_row, enemy_col)][0] != color):
                        if 0 <= behind_row < board_size and 0 <= behind_col < board_size and (behind_row, behind_col) not in board:
                            capture_board = board.copy()
                            del capture_board[(row, col)]
                            del capture_board[(enemy_row, enemy_col)]
                            new_piece = promote_piece(behind_row, piece)
                            capture_board[(behind_row, behind_col)] = new_piece
                            capture_moves.append(capture_board)
    return capture_moves if capture_moves else moves

def minimax(board, depth, maximizing_player, alpha, beta):
    if depth == 0:
        return evaluate_board(board)
    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        for move in generate_moves(board, VINO_PIECE):
            eval_value = minimax(move, depth - 1, False, alpha, beta)
            if eval_value > max_eval:
                max_eval = eval_value
                best_move = move
            alpha = max(alpha, eval_value)
            if beta <= alpha:
                break
        return best_move if depth == 3 else max_eval
    else:
        min_eval = float('inf')
        best_move = None
        for move in generate_moves(board, PLAYER_PIECE):
            eval_value = minimax(move, depth - 1, True, alpha, beta)
            if eval_value < min_eval:
                min_eval = eval_value
                best_move = move
            beta = min(beta, eval_value)
            if beta <= alpha:
                break
        return best_move if depth == 3 else min_eval

def main():
    show_menu()
    while True:
        draw_board()
        draw_pieces()
        show_movement_counter()
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and turn == 'player':
                handle_mouse_click(event.pos)

        if turn == 'vino':
            apply_ai_move()

if __name__ == "__main__":
    main()
