import pygame
import sys

# Inicializar Pygame
pygame.init()

# Configuración de la pantalla
screen_width = 400
screen_height = 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Juego de Damas 4x4")

# Colores
WHITE = (255, 255, 255) # Colores del tablero
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)
SELECT_COLOR = (150, 150, 255)  # Color para remarcar la opcion en el menu
VINO_PIECE = (128, 0, 32)  # Color vinotinto para las piezas de la IA
WHITE_PIECE = (255, 255, 255)  # Color blanco para las piezas del jugador
MOVEMENT_COUNTER = (0, 128, 255)  # Color para el contador de turnos

# Tamaño del tablero
board_size = 4
square_size = screen_width // board_size

# EPosicion de las piezas
pieces = {
    (0, 0): VINO_PIECE,
    (0, 2): VINO_PIECE,
    (3, 1): WHITE_PIECE,
    (3, 3): WHITE_PIECE,
}

# Algunas otras configuraciones
selected_piece = None
turn = 'vino'  # Turno inicial. 'vino' piezas vinotinto y 'white' piezas blancas
turn_counter = 0  # Contador de turnos

# Función para dibujar el tablero con las casillas intercambiadas
def draw_board():
    for row in range(board_size):
        for col in range(board_size):
            if (row + col) % 2 == 0:
                pygame.draw.rect(screen, BLACK, (col * square_size, row * square_size, square_size, square_size))  # Casilla negra
            else:
                pygame.draw.rect(screen, WHITE, (col * square_size, row * square_size, square_size, square_size))  # Casilla blanca

            # Si hay una pieza seleccionada, dibujar los puntos negros en las casillas válidas
            if selected_piece:
                selected_row, selected_col = selected_piece
                if (abs(selected_row - row) == 1 and abs(selected_col - col) == 1) and (row + col) % 2 == 0:
                    pygame.draw.circle(screen, WHITE, (col * square_size + square_size // 2, row * square_size + square_size // 2), 5)

# Función para dibujar las piezas
def draw_pieces():
    for (row, col), color in pieces.items():
        pygame.draw.circle(screen, color, (col * square_size + square_size // 2, row * square_size + square_size // 2), square_size // 3)

# Función para mostrar el contador de turnos
def show_movement_counter():
    font = pygame.font.Font(None, 36)
    turn_text = f"Turnos: {turn_counter}" # Muestra el mensaje
    text_surface = font.render(turn_text, True, MOVEMENT_COUNTER)
    screen.blit(text_surface, (10, 10))  # Posiciona el mensaje arriba a la izquierda

# Función para mostrar el menú
def show_menu():
    options = ["Jugar", "Salir"]
    selected_index = 0

    while True:
        screen.fill(GRAY)
        font = pygame.font.Font(None, 48)  
        title_text = font.render("Juego de Damas", True, BLACK)
        
        # Se ajusta el margen para centrar el título
        title_margin_top = 80
        screen.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, title_margin_top))

        font_medium = pygame.font.Font(None, 36)

        for i, option in enumerate(options):
            option_text = font_medium.render(option, True, BLACK)
            option_rect = option_text.get_rect(center=(screen_width // 2, 150 + i * 100))

            # Se dibuja el cuadro para remarcar la opcion en el menu
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
                elif selected_index == 1:  # Salir del juego
                    pygame.quit()
                    sys.exit()

# Función para manejar el movimiento de las piezas del jugador a traves del mouse
def handle_mouse_click(pos):
    global selected_piece, turn, turn_counter
    col = pos[0] // square_size
    row = pos[1] // square_size

    if selected_piece is None:
        # Selecciona una pieza
        if (row, col) in pieces and ((pieces[(row, col)] == VINO_PIECE and turn == 'vino') or (pieces[(row, col)] == WHITE_PIECE and turn == 'white')):
            selected_piece = (row, col)
    else:
        # Mueve la pieza
        if (row, col) not in pieces and (row + col) % 2 == 0:  # Solo se mueve a casillas negras
            # Verifica si el movimiento es válido (una casilla adyacente)
            selected_row, selected_col = selected_piece
            if (abs(selected_row - row) == 1 and abs(selected_col - col) == 1):
                pieces[(row, col)] = pieces[selected_piece]  # Mueve la pieza
                del pieces[selected_piece]  # Elimina la pieza de la posición anterior
                turn = 'white' if turn == 'vino' else 'vino'  # Cambia el turno
                turn_counter += 1  # Incrementa el contador de turnos
            selected_piece = None  # Deselecciona la pieza
        else:
            # Comprueba si se puede comer una pieza vinotinto
            if (row, col) in pieces and ((pieces[(row, col)] == VINO_PIECE and turn == 'white')):
                if pieces[(row, col)] != pieces[selected_piece]:
                    # Verifica si hay una casilla vacía detrás de la pieza a comer
                    behind_row = row + (row - selected_piece[0])  
                    behind_col = col + (col - selected_piece[1])  
                    if (behind_row, behind_col) not in pieces and 0 <= behind_row < board_size and 0 <= behind_col < board_size:  # La casilla detrás está vacía y dentro del tablero
                        del pieces[(row, col)]  # Elimina la pieza comida
                        pieces[(behind_row, behind_col)] = pieces[selected_piece]  # Mueve la pieza a la posición detrás
                        del pieces[selected_piece]  # Elimina la pieza de la posición anterior
                        turn = 'white' if turn == 'vino' else 'vino'  # Cambia el turno
                        turn_counter += 1  # Incrementa el contador de turnos
            selected_piece = None  # Deselecciona si no se puede mover

    check_winner()  # Verifica si hay un ganador después de cada movimiento

# Función para verificar si hay ganador
def check_winner():
    vino_count = sum(1 for color in pieces.values() if color == VINO_PIECE)
    white_count = sum(1 for color in pieces.values() if color == WHITE_PIECE)

    check_draw()

    if vino_count == 0:
        show_winner_message("Gano el jugador|blanco")
    elif white_count == 0:
        show_winner_message("Gano el jugador|vinotinto")

# Función para verificar si hay empate
def check_draw():
    global turn_counter
    if turn_counter >= 64:
        show_winner_message("¡Empate!|Número máximo|de turnos alcanzado.")

# Función para mostrar el mensaje final
def show_winner_message(winner):
    screen.fill(GRAY) 
    font = pygame.font.Font(None, 48)
    
    lines = winner.split("|")

    y_offset = screen_height // 2 - len(lines) * 24  # Se ajusta la posición vertical para centrar el texto

    for line in lines:
        text_surface = font.render(line, True, BLACK)
        text_rect = text_surface.get_rect(center=(screen_width // 2, y_offset))
        screen.blit(text_surface, text_rect)
        y_offset += 50  

    pygame.display.flip()
    pygame.time.wait(3000)  # Pausa de 3 segundos
    pygame.quit()
    sys.exit()

# Función para aplicar la jugada de la IA
def apply_ai_move():
    global turn, turn_counter
    best_move = minimax(pieces, 3, True, float('-inf'), float('inf')) 
    if best_move:
        pieces.clear()
        pieces.update(best_move)
        turn = 'white'  # Cambia el turno después de la jugada de la IA
        turn_counter += 1  # Incrementa el contador de turnos
    check_winner()

# Función de evaluación del tablero
def evaluate_board(board):
    VINO_PIECES = sum(1 for color in board.values() if color == VINO_PIECE)
    WHITE_PIECES = sum(1 for color in board.values() if color == WHITE_PIECE)
    return VINO_PIECES - WHITE_PIECES

# Función para generar movimientos válidos
def generate_moves(board, color):
    moves = []
    capture_moves = []  

    for (row, col), piece_color in board.items():
        if piece_color == color:
            for d_row, d_col in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                new_row, new_col = row + d_row, col + d_col
                if (new_row, new_col) not in board and 0 <= new_row < board_size and 0 <= new_col < board_size:
                    new_board = board.copy()
                    del new_board[(row, col)]
                    new_board[(new_row, new_col)] = piece_color
                    moves.append(new_board)

                # Verifica si hay una pieza enemiga que pueda ser comida
                enemy_row, enemy_col = row + d_row, col + d_col
                behind_row = new_row + d_row 
                behind_col = new_col + d_col  

                if 0 <= enemy_row < board_size and 0 <= enemy_col < board_size and (enemy_row, enemy_col) in board:
                    if board[(enemy_row, enemy_col)] != color:  # Hay una pieza enemiga
                        if (behind_row, behind_col) not in board and 0 <= behind_row < board_size and 0 <= behind_col < board_size:
                            # La casilla detrás está vacía
                            capture_board = board.copy()
                            del capture_board[(row, col)]  
                            del capture_board[(enemy_row, enemy_col)] 
                            capture_board[(behind_row, behind_col)] = piece_color 
                            capture_moves.append(capture_board)  

    # Da prioridad a los movimientos de captura, si hay movimientos de captura se retorna
    # Sino hay movimientos de captura, se retornan los movimientos normales
    if capture_moves:
        return capture_moves 
    return moves  

# Función minimax con poda alfa-beta
def minimax(board, depth, maximizing_player, alpha, beta):
    if depth == 0:
        return evaluate_board(board)

    if maximizing_player:
        max_eval = float('-inf')
        best_move = None
        for move in generate_moves(board, VINO_PIECE):
            eval = minimax(move, depth - 1, False, alpha, beta)
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return best_move if depth == 3 else max_eval
    else:
        min_eval = float('inf')
        best_move = None
        for move in generate_moves(board, WHITE_PIECE):
            eval = minimax(move, depth - 1, True, alpha, beta)
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
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
            if event.type == pygame.MOUSEBUTTONDOWN and turn == 'white':  
                handle_mouse_click(event.pos)
            if turn == 'vino': 
                apply_ai_move()

if __name__ == "__main__":
    main()
