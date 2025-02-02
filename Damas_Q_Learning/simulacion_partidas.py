import pygame
import sys
import random
import json
import os
import copy

pygame.init()

#Ventana del juego
screen_width = 400
screen_height = 400
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Simulación de Damas 4x4 (10k partidas)")

# Colores
BOARD_BLACK = (0, 0, 0)               # Casillas negras
BOARD_WHITE = (255, 255, 255)         # Casillas blancas
GRAY = (200, 200, 200)                # Fondo de la pantalla
SELECT_COLOR = (150, 150, 255)        # Resalte (no se usa en simulación)
VINO_PIECE = (128, 0, 32)             # Piezas de la IA (vinotinto)
PLAYER_PIECE = (100, 100, 100)        # Piezas de la otra IA (grises)
MOVEMENT_COUNTER = (0, 128, 255)      # Color del contador de turnos

# Tamaño del tablero
board_size = 4
square_size = screen_width // board_size

# Estado inicial del tablero: cada pieza se representa como (color, is_king)
initial_board = {
    (0, 0): (VINO_PIECE, False),
    (0, 2): (VINO_PIECE, False),
    (3, 1): (PLAYER_PIECE, False),
    (3, 3): (PLAYER_PIECE, False),
}

# Variables globales para el juego simulado
pieces = {}  # Se inicializa en reset_game()
turn = None  # 'player' o 'vino'
turn_counter = 0

# Contadores de victorias
gray_wins = 0
vino_wins = 0

# Parámetros de Q-Learning
alpha = 0.5         # Tasa de aprendizaje
gamma = 0.9         # Factor de descuento
epsilon = 0.8       # Probabilidad de exploración (se podría decaer con el tiempo)
q_table_file = "Damas_Q_Learning\qtable.json"
q_table = {}  # Se carga desde el archivo JSON

# Cargar los datos de partidas anteriores a q_table
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

# Guardar datos en Q_table
def save_q_table():
    # Carga el contenido existente y fusiona con la tabla actual sin sobreescribir datos ya almacenados
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

# Representa el estado del tablero como una cadena única (ordenada)
def get_state_representation(board):
    items = sorted([(str(k), board[k]) for k in board.keys()])
    return str(items)

# Actualiza Q_table
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

# Cargar la Q-Table al inicio
load_q_table()

# ------------------------------
# Funciones de Dibujo (para ver el progreso en la ventana)
# ------------------------------

# Dibuja el tablero
def draw_board():
    for row in range(board_size):
        for col in range(board_size):
            if ((row + col) % 2 )== 0:
                pygame.draw.rect(screen, BOARD_BLACK, (col * square_size, row * square_size, square_size, square_size))
            else:
                pygame.draw.rect(screen, BOARD_WHITE, (col * square_size, row * square_size, square_size, square_size))

# Dibuja las piezas
def draw_pieces():
    for (row, col), piece in pieces.items():
        color, is_king = piece
        pygame.draw.circle(screen, color, (col * square_size + square_size // 2, row * square_size + square_size // 2), square_size // 3)
        if is_king:
            pygame.draw.circle(screen, BOARD_BLACK, (col * square_size + square_size // 2, row * square_size + square_size // 2), square_size // 8)

#Muestra el contador de movimientos
def show_movement_counter():
    font = pygame.font.Font(None, 36)
    turn_text = f"Turnos: {turn_counter}"
    text_surface = font.render(turn_text, True, MOVEMENT_COUNTER)
    screen.blit(text_surface, (10, 10))

# Muestra el progreso en la simulacion
def show_simulation_progress(simulated, total):
    font = pygame.font.Font(None, 36)
    progress_text = f"Simuladas: {simulated} / {total} partidas"
    text_surface = font.render(progress_text, True, MOVEMENT_COUNTER)
    screen.blit(text_surface, (10, screen_height - 40))

# ------------------------------
# Funciones para recompensas
# ------------------------------

# Cuenta las piezas
def count_pieces(board, team):
    return sum(1 for piece in board.values() if piece[0] == team)

# cuenta si se promovio una pieza
def count_promoted(board, team):
    return sum(1 for piece in board.values() if piece[0] == team and piece[1] == True)

# Recompensa si la ficha tiene una ficha aliada cerca y tambien si se coloca en una poscion donde la ficha de atras impide que pueda ser comida
def support_reward(board, team):
    reward = 0
    for (row, col), piece in board.items():
        if piece[0] == team:
            for d_row, d_col in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                r = row + d_row
                c = col + d_col
                if (r, c) in board and board[(r, c)][0] == team:
                    reward += 0.2
                    break
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

# recompensa si hay una ficha en el medio
def central_control_reward(board, team):
    reward = 0
    central_cells = [(1,1), (1,2), (2,1), (2,2)]
    for (row, col), piece in board.items():
        if piece[0] == team and (row, col) in central_cells:
            reward += 0.1
    return reward

# recompensa si hay una ficha protegiendo
def protection_reward(board, team):
    reward = 0
    if team == VINO_PIECE:
        backward_dirs = [(-1, -1), (-1, 1)]
    else:
        backward_dirs = [(1, -1), (1, 1)]
    for (row, col), piece in board.items():
        if piece[0] == team:
            for d_row, d_col in backward_dirs:
                r = row + d_row
                c = col + d_col
                if 0 <= r < board_size and 0 <= c < board_size:
                    if (r, c) in board and board[(r, c)][0] == team:
                        reward += 0.5
                        break
    return reward

# Diferentes recompensas y castigos si mueve una ficha, captura una ficha, promueve a dama y suma todo y lo retorna
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
        reward += 1 * (prom_after - prom_before)

    if (enemy_after == enemy_before) and (prom_after == prom_before):
        reward -= 0.05

    reward += support_reward(after, team)
    reward += central_control_reward(after, team)
    reward += protection_reward(after, team)

    return reward

# ------------------------------
# Lógica del Juego y Q-Learning (Simulación de partidas AI vs AI)
# ------------------------------

# Resetea el juego
def reset_game():
    global pieces, turn, turn_counter
    pieces = copy.deepcopy(initial_board)
    turn = 'player'
    turn_counter = 0

# Promueve fichas
def promote_piece(row, piece):
    color, is_king = piece
    if not is_king:
        if color == PLAYER_PIECE and row == 0:
            return (color, True)
        if color == VINO_PIECE and row == board_size - 1:
            return (color, True)
    return piece

# Genera movimientos posibles para la IA
def generate_moves(board, color):
    moves = []
    capture_moves = []
    for (row, col), piece in board.items():
        if piece[0] == color:
            if piece[1]:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            else:
                if color == PLAYER_PIECE:
                    directions = [(-1, -1), (-1, 1)]
                else:
                    directions = [(1, -1), (1, 1)]
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

# Evalua si termina el juego
def game_over(board):
    vino_count = sum(1 for piece in board.values() if piece[0] == VINO_PIECE)
    player_count = sum(1 for piece in board.values() if piece[0] == PLAYER_PIECE)
    if vino_count == 0 or player_count == 0:
        return True
    return False

# Retorna si gano, perdio o empato
def get_winner(board):
    vino_count = sum(1 for piece in board.values() if piece[0] == VINO_PIECE)
    player_count = sum(1 for piece in board.values() if piece[0] == PLAYER_PIECE)
    if vino_count == 0:
        return "player"
    elif player_count == 0:
        return "vino"
    else:
        return "draw"

# Mueve las fichas de la IA
def ai_move(color):
    global pieces, turn, turn_counter
    state = get_state_representation(pieces)
    actions = []
    moves = generate_moves(pieces, color)
    if not moves:
        update_q_table(state, "none", -1, None)
        return None, state
    prev_board = copy.deepcopy(pieces)
    for move in moves:
        action_rep = get_state_representation(move)
        actions.append((move, action_rep))
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
    pieces = selected_move.copy()
    new_state = get_state_representation(pieces)
    reward = compute_reward(prev_board, pieces, color)
    update_q_table(state, selected_action, reward, new_state)
    turn_counter += 1
    return selected_action, state

# Acciones de la simulacion
def simulate_game(record_moves=True):
    global pieces, turn, turn_counter, gray_wins, vino_wins
    reset_game()
    turn = 'player'
    turn_counter = 0
    moves_log = []
    max_turns = 100
    while not game_over(pieces) and turn_counter < max_turns:
        current_color = PLAYER_PIECE if turn == 'player' else VINO_PIECE
        action, state_before = ai_move(current_color)
        moves_log.append({
            "turn": turn,
            "state_before": state_before,
            "action": action,
            "turn_counter": turn_counter
        })
        turn = 'vino' if turn == 'player' else 'player'
    winner = get_winner(pieces)
    if winner == "draw":
        final_reward = 0
    else:
        final_reward = 20 if winner == ("player" if turn == "vino" else "vino") else -20
        if winner == "player":
            gray_wins += 1
        elif winner == "vino":
            vino_wins += 1
    last_state = get_state_representation(pieces)
    update_q_table(last_state, "terminal", final_reward, None)
    return {"winner": winner, "turns": turn_counter, "moves": moves_log}

# Simula el juego entre las dos IA
def simulate_games(n):
    games = []
    for i in range(n):
        game_record = simulate_game(record_moves=True)
        games.append(game_record)
        if (i+1) % 100 == 0:
            print(f"Simuladas {i+1} partidas...")
            screen.fill(GRAY)
            draw_board()
            show_simulation_progress(i+1, n)
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    save_q_table()
                    pygame.quit()
                    sys.exit()
    save_q_table()

# Funcion principal
def main():
    total_games = 7000
    simulate_games(total_games)
    running = True
    font = pygame.font.Font(None, 36)
    while running:
        screen.fill(GRAY)
        text = font.render("Simulación completa: 10,000 partidas guardadas", True, BOARD_BLACK)
        screen.blit(text, (20, screen_height//2 - 20))
        text2 = font.render("Cierre la ventana para terminar", True, BOARD_BLACK)
        screen.blit(text2, (20, screen_height//2 + 20))
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
    print(f"Victorias grises: {gray_wins} | Victorias Vinotinto: {vino_wins}")
    save_q_table()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()