import pygame
import sys
import random
import json
import os
import copy

pygame.init()

# Dimensiones de la ventana del juego
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
# Usamos "player" para el jugador y "vino" para la IA.
turn = 'player'
turn_counter = 0

# Parámetros de Q-Learning
alpha = 0.5         # Tasa de aprendizaje
gamma = 0.9         # Factor de descuento
epsilon = 0.2       # Probabilidad de exploración
q_table_file = "Damas_Q_Learning\qtable.json"
q_table = {}  # Se cargará desde el archivo JSON

# Carga los datos del archivo a q_table
def load_q_table():
    global q_table
    if os.path.exists(q_table_file):
        try:
            with open(q_table_file, "r") as f:
                q_table = json.load(f)
        except Exception as e:
            print("Error cargando qtable:", e)
            q_table = {}
    else:
        q_table = {}

# Guarda los datos en qtable
def save_q_table():
    # Carga la información existente y fusiona con la tabla actual
    existing = {}
    if os.path.exists(q_table_file):
        try:
            with open(q_table_file, "r") as f:
                existing = json.load(f)
        except Exception as e:
            print("Error leyendo qtable para fusionar:", e)
            existing = {}
    for state, actions in q_table.items():
        if state in existing:
            for action, value in actions.items():
                existing[state][action] = value
        else:
            existing[state] = actions
    with open(q_table_file, "w") as f:
        json.dump(existing, f)

# Convierte el estado del tablero a una cadena unica
def get_state_representation(board):
    # Se ordenan las piezas para tener una representación consistente.
    items = sorted([(str(k), board[k]) for k in board.keys()])
    return str(items)

# Actualiza qtable
def update_q_table(state, action, reward, next_state):
    global q_table
    if state not in q_table:
        q_table[state] = {}
    if action not in q_table[state]:
        q_table[state][action] = 0.0
    next_max = 0.0
    if next_state is not None and next_state in q_table and q_table[next_state]:
        next_max = max(q_table[next_state].values())
    q_table[state][action] = q_table[state][action] + alpha * (reward + gamma * next_max - q_table[state][action])

# Cargar la Q-Table desde el archivo JSON al iniciar
load_q_table()

# Dibuja el tablero
def draw_board():
    for row in range(board_size):
        for col in range(board_size):
            if (row + col) % 2 == 0:
                pygame.draw.rect(screen, BOARD_BLACK, (col * square_size, row * square_size, square_size, square_size))
            else:
                pygame.draw.rect(screen, BOARD_WHITE, (col * square_size, row * square_size, square_size, square_size))
            # Señal en casillas adyacentes a la pieza seleccionada
            if selected_piece:
                selected_row, selected_col = selected_piece
                if (abs(selected_row - row) == 1 and abs(selected_col - col) == 1) and ((row + col) % 2 == 0):
                    pygame.draw.circle(screen, BOARD_WHITE, (col * square_size + square_size // 2, row * square_size + square_size // 2), 5)

# Dibuja las piezas
def draw_pieces():
    for (row, col), piece in pieces.items():
        color, is_king = piece
        pygame.draw.circle(screen, color, (col * square_size + square_size // 2, row * square_size + square_size // 2), square_size // 3)
        # Si la pieza es dama, se dibuja un marcador (círculo pequeño negro)
        if is_king:
            pygame.draw.circle(screen, BOARD_BLACK, (col * square_size + square_size // 2, row * square_size + square_size // 2), square_size // 8)

# Muestra contador de turnos
def show_movement_counter():
    font = pygame.font.Font(None, 36)
    turn_text = f"Turnos: {turn_counter}"
    text_surface = font.render(turn_text, True, MOVEMENT_COUNTER)
    screen.blit(text_surface, (10, 10))

# Muestra el menu
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
                save_q_table()
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
                        save_q_table()
                        pygame.quit()
                        sys.exit()

# Función que promueve a dama (rey) si la pieza llega a la fila contraria.
def promote_piece(row, piece):
    color, is_king = piece
    if not is_king:
        if color == PLAYER_PIECE and row == 0:
            return (color, True)
        if color == VINO_PIECE and row == board_size - 1:
            return (color, True)
    return piece

# ------------------------------
# Funciones auxiliares para recompensas
# ------------------------------

# Cuenta las piezas
def count_pieces(board, team):
    return sum(1 for piece in board.values() if piece[0] == team)

# Cuenta las promociones
def count_promoted(board, team):
    return sum(1 for piece in board.values() if piece[0] == team and piece[1] == True)


# Recompensa por soporte: Suma +0.2 si una ficha tiene al menos un amigo en alguna casilla diagonal.
# Además, evalúa el posicionamiento protegido: si la ficha cuenta con una amiga en la dirección
# "trasera" (según la dirección de avance) que le impide ser capturada, se otorga +0.5.

def support_reward(board, team):
    
    reward = 0
    for (row, col), piece in board.items():
        if piece[0] == team:
            # Evaluar soporte en cualquier diagonal
            for d_row, d_col in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                r = row + d_row
                c = col + d_col
                if (r, c) in board and board[(r, c)][0] == team:
                    reward += 0.2
                    break
            # Evaluar posicionamiento protegido: definir "atrás" según el sentido de avance.
            if team == VINO_PIECE:
                backward_dirs = [(-1, -1), (-1, 1)]
            else:
                backward_dirs = [(1, -1), (1, 1)]
            for d_row, d_col in backward_dirs:
                r = row + d_row
                c = col + d_col
                if 0 <= r < board_size and 0 <= c < board_size:
                    if (r, c) in board and board[(r, c)][0] == team:
                        reward += 1.5
                        break
    return reward

# Recompensa por ocupar celdas centrales en un tablero 4x4
def central_control_reward(board, team):
    reward = 0
    central_cells = [(1, 1), (1, 2), (2, 1), (2, 2)]
    for (row, col), piece in board.items():
        if piece[0] == team and (row, col) in central_cells:
            reward += 0.1
    return reward


# Calcula la recompensa basada en:
#   - Pérdida o ganancia de piezas (–5 por cada propia perdida, +5 por cada enemiga capturada)
#   - Promoción a dama (+1 por cada ficha promovida)
#   - Penalización leve si el movimiento es "normal" sin captura ni promoción (–0.05)
#   - Recompensas adicionales por soporte (incluyendo posicionamiento protegido) y control central

def compute_reward(before, after, team):
   
    reward = 0
    enemy = PLAYER_PIECE if team == VINO_PIECE else VINO_PIECE

    own_before = count_pieces(before, team)
    own_after = count_pieces(after, team)
    enemy_before = count_pieces(before, enemy)
    enemy_after = count_pieces(after, enemy)

    if own_after < own_before:
        reward -= 5 * (own_before - own_after)
    if enemy_after < enemy_before:
        reward += 5 * (enemy_before - enemy_after)

    prom_before = count_promoted(before, team)
    prom_after = count_promoted(after, team)
    if prom_after > prom_before:
        reward += 3 * (prom_after - prom_before)

    if (enemy_after == enemy_before) and (prom_after == prom_before):
        reward -= 0.1

    reward += support_reward(after, team)
    reward += central_control_reward(after, team)

    return reward

# ------------------------------
# Lógica del Juego y Q-Learning (Human vs IA)
# ------------------------------

# Permite que el jugador mueva piezas
def handle_mouse_click(pos):
    global selected_piece, turn, turn_counter
    col = pos[0] // square_size
    row = pos[1] // square_size

    if selected_piece is None:
        if (row, col) in pieces:
            p_color, _ = pieces[(row, col)]
            if (p_color == PLAYER_PIECE and turn == 'player') or (p_color == VINO_PIECE and turn == 'vino'):
                selected_piece = (row, col)
    else:
        selected_row, selected_col = selected_piece
        # Primero se verifica si se intenta capturar (clic en pieza enemiga)
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
        # Movimiento normal a casilla adyacente
        elif (row, col) not in pieces and abs(selected_row - row) == 1 and abs(selected_col - col) == 1:
            moving_piece = pieces[selected_piece]
            color, is_king = moving_piece
            if not is_king:
                if (color == PLAYER_PIECE and row >= selected_row) or (color == VINO_PIECE and row <= selected_row):
                    selected_piece = None
                    return
            new_piece = promote_piece(row, moving_piece)
            pieces[(row, col)] = new_piece
            del pieces[selected_piece]
            turn = 'player' if turn == 'vino' else 'vino'
            turn_counter += 1
        selected_piece = None
        check_winner()

# Evalua si hay un ganador
def check_winner():
    vino_count = sum(1 for piece in pieces.values() if piece[0] == VINO_PIECE)
    player_count = sum(1 for piece in pieces.values() if piece[0] == PLAYER_PIECE)
    check_draw()
    if vino_count == 0:
        # IA pierde: actualizar Q-table con castigo fuerte (-20)
        terminal_state = get_state_representation(pieces)
        update_q_table(terminal_state, "terminal", -20, None)
        show_winner_message("Gano el jugador|grises")
    elif player_count == 0:
        # IA gana: actualizar Q-table con recompensa fuerte (+20)
        terminal_state = get_state_representation(pieces)
        update_q_table(terminal_state, "terminal", 20, None)
        show_winner_message("Gano el jugador|vinotinto")

# Evalua si hay empate
def check_draw():
    global turn_counter
    if turn_counter >= 64:
        show_winner_message("¡Empate!|Número máximo|de turnos alcanzado.")

# Muestra el ganador
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
    save_q_table()
    pygame.quit()
    sys.exit()

# Genera movimientos para la IA
def generate_moves(board, color):
    moves = []
    capture_moves = []
    for (row, col), piece in board.items():
        if piece[0] == color:
            color_piece, is_king = piece
            if is_king:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            else:
                if color == PLAYER_PIECE:
                    directions = [(-1, -1), (-1, 1)]  # El jugador (humano) avanza hacia arriba (fila menor)
                else:
                    directions = [(1, -1), (1, 1)]      # La IA avanza hacia abajo (fila mayor)
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
                    # Captura: verificar casilla detrás de la pieza enemiga.
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

# Función de la IA usando Q-Learning (para la jugada de la IA en Human vs IA)
def apply_ai_move():
    global turn, turn_counter, pieces
    state = get_state_representation(pieces)
    actions = []
    moves = generate_moves(pieces, VINO_PIECE)
    if not moves:
        update_q_table(state, "none", -1, None)
        turn = 'player'
        return
    # Guardar el estado previo completo para calcular recompensa
    prev_board = copy.deepcopy(pieces)
    for move in moves:
        action_rep = get_state_representation(move)
        actions.append((move, action_rep))
    # Política epsilon-greedy
    if random.random() < epsilon:
        selected_move, selected_action = random.choice(actions)
    else:
        q_values = q_table.get(state, {})
        best_value = -float('inf')
        selected_move, selected_action = None, None
        for move, action_rep in actions:
            value = q_values.get(action_rep, 0.0)
            if value > best_value:
                best_value = value
                selected_move, selected_action = move, action_rep
        if selected_move is None:
            selected_move, selected_action = random.choice(actions)
    prev_state = state
    pieces = selected_move.copy()
    new_state = get_state_representation(pieces)
    # Calcular recompensa basada en las mejoras definidas, incluyendo la recompensa por posicionamiento protegido
    reward = compute_reward(prev_board, pieces, VINO_PIECE)
    update_q_table(prev_state, selected_action, reward, new_state)
    turn = 'player'
    turn_counter += 1
    save_q_table()
    check_winner()

def main():
    show_menu()
    while True:
        draw_board()
        draw_pieces()
        show_movement_counter()
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                save_q_table()
                pygame.quit()
                sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN and turn == 'player':
                handle_mouse_click(event.pos)

        if turn == 'vino':
            apply_ai_move()

if __name__ == "__main__":
    main()
