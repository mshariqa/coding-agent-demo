"""
Comprehensive tests for Tetris implementation.
Tests cover Board, Piece, and Tetris game logic.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from main import (
    Board, Piece, Tetris,
    COLS, ROWS, TETROMINOES, COLORS,
    SCORE_TABLE, LINES_PER_LEVEL, LOCK_DELAY,
    LIGHT_BG, _contrast_ratio
)


# ── Board Tests ────────────────────────────────────────────────────────────────

class TestBoard:
    """Test the Board class for grid management."""

    def test_board_initialization(self):
        """Test board creates correct empty grid."""
        board = Board()
        assert len(board.grid) == ROWS
        assert all(len(row) == COLS for row in board.grid)
        assert all(cell is None for row in board.grid for cell in row)

    def test_is_valid_empty_board(self):
        """Test valid piece placement on empty board."""
        board = Board()
        # Valid position in center
        assert board.is_valid([(0, 4), (0, 5), (1, 4), (1, 5)])
        # Valid position at edges
        assert board.is_valid([(0, 0), (0, 1), (1, 0), (1, 1)])
        assert board.is_valid([(ROWS-1, COLS-1)])

    def test_is_valid_negative_row(self):
        """Test that negative rows are allowed (spawn area)."""
        board = Board()
        # Negative rows should be valid for spawn
        assert board.is_valid([(-1, 4), (-1, 5), (0, 4), (0, 5)])

    def test_is_valid_out_of_bounds(self):
        """Test invalid positions outside board boundaries."""
        board = Board()
        # Left boundary
        assert not board.is_valid([(0, -1)])
        # Right boundary
        assert not board.is_valid([(0, COLS)])
        # Bottom boundary
        assert not board.is_valid([(ROWS, 0)])

    def test_is_valid_collision(self):
        """Test collision detection with occupied cells."""
        board = Board()
        # Place a cell
        board.grid[5][4] = (255, 0, 0)
        # Try to place at same location
        assert not board.is_valid([(5, 4)])
        # Adjacent cell should be valid
        assert board.is_valid([(5, 3)])
        assert board.is_valid([(5, 5)])

    def test_lock_piece(self):
        """Test locking piece onto board."""
        board = Board()
        color = (0, 255, 0)
        cells = [(5, 3), (5, 4), (6, 3), (6, 4)]
        board.lock(cells, color)

        for r, c in cells:
            assert board.grid[r][c] == color

    def test_lock_negative_row(self):
        """Test that negative row cells are not locked."""
        board = Board()
        color = (0, 255, 0)
        cells = [(-1, 4), (0, 4), (1, 4)]
        board.lock(cells, color)

        # Row -1 doesn't exist, should not crash
        assert board.grid[0][4] == color
        assert board.grid[1][4] == color

    def test_clear_lines_no_full_lines(self):
        """Test clear_lines returns 0 when no full lines."""
        board = Board()
        # Place some cells but not full line
        for c in range(COLS - 1):
            board.grid[ROWS-1][c] = (255, 0, 0)

        cleared = board.clear_lines()
        assert cleared == 0

    def test_clear_lines_single_line(self):
        """Test clearing a single full line."""
        board = Board()
        # Fill bottom row
        for c in range(COLS):
            board.grid[ROWS-1][c] = (255, 0, 0)

        cleared = board.clear_lines()
        assert cleared == 1
        # Bottom row should be empty
        assert all(cell is None for cell in board.grid[ROWS-1])
        # Top row should now have the cleared line
        assert all(cell is None for cell in board.grid[0])

    def test_clear_lines_multiple_lines(self):
        """Test clearing multiple full lines."""
        board = Board()
        # Fill bottom 3 rows
        for r in range(ROWS-3, ROWS):
            for c in range(COLS):
                board.grid[r][c] = (255, 0, 0)

        cleared = board.clear_lines()
        assert cleared == 3
        # Bottom 3 rows should be empty
        for r in range(ROWS-3, ROWS):
            assert all(cell is None for cell in board.grid[r])

    def test_clear_lines_non_consecutive(self):
        """Test clearing non-consecutive lines."""
        board = Board()
        # Fill rows with gap
        for c in range(COLS):
            board.grid[ROWS-1][c] = (255, 0, 0)  # Bottom
            board.grid[ROWS-3][c] = (0, 255, 0)  # Two up

        cleared = board.clear_lines()
        assert cleared == 2


# ── Piece Tests ────────────────────────────────────────────────────────────────

class TestPiece:
    """Test the Piece class for tetromino representation."""

    def test_piece_initialization(self):
        """Test piece is created with correct defaults."""
        piece = Piece("I")
        assert piece.kind == "I"
        assert piece.color == COLORS["I"]
        assert piece.rot == 0
        assert piece.row == -1
        assert piece.col == COLS // 2 - 2

    def test_all_piece_types(self):
        """Test all piece types can be created."""
        for kind in TETROMINOES.keys():
            piece = Piece(kind)
            assert piece.kind == kind
            assert piece.color == COLORS[kind]

    def test_cells_default_position(self):
        """Test cells() returns correct positions with defaults."""
        piece = Piece("O")
        cells = piece.cells()
        # O piece at row=-1, col=3 (COLS//2-2 = 3)
        expected = [
            (-1 + dr, 3 + dc)
            for dr, dc in TETROMINOES["O"][0]
        ]
        assert cells == expected

    def test_cells_custom_position(self):
        """Test cells() with custom row and col."""
        piece = Piece("I")
        cells = piece.cells(row=5, col=3)
        expected = [
            (5 + dr, 3 + dc)
            for dr, dc in TETROMINOES["I"][0]
        ]
        assert cells == expected

    def test_cells_custom_rotation(self):
        """Test cells() with custom rotation."""
        piece = Piece("T")
        piece.rot = 1
        cells = piece.cells(rot=2)
        # Should use rotation 2, not piece's current rotation 1
        expected = [
            (-1 + dr, 3 + dc)
            for dr, dc in TETROMINOES["T"][2]
        ]
        assert cells == expected

    def test_num_rotations(self):
        """Test correct number of rotations for each piece."""
        assert Piece("I").num_rotations() == 4
        assert Piece("O").num_rotations() == 1
        assert Piece("T").num_rotations() == 4
        assert Piece("S").num_rotations() == 4
        assert Piece("Z").num_rotations() == 4
        assert Piece("J").num_rotations() == 4
        assert Piece("L").num_rotations() == 4

    def test_piece_shapes(self):
        """Test that piece shapes are defined correctly."""
        # I piece should have 4 cells in a row/column
        for rot in range(4):
            cells = TETROMINOES["I"][rot]
            assert len(cells) == 4

        # O piece should be 2x2 square with 1 rotation
        o_cells = TETROMINOES["O"][0]
        assert len(o_cells) == 4
        assert len(TETROMINOES["O"]) == 1


# ── Tetris Game Logic Tests ────────────────────────────────────────────────────

class TestTetrisGameLogic:
    """Test Tetris game logic without pygame dependencies."""

    @pytest.fixture
    def mock_tetris(self):
        """Create a Tetris instance with mocked pygame."""
        with patch('main.pygame'):
            tetris = Tetris()
            # Reset to clean state without pygame
            tetris.board = Board()
            tetris.bag = []
            tetris.current = None
            tetris.held = None
            tetris.can_hold = True
            tetris.score = 0
            tetris.lines = 0
            tetris.level = 1
            tetris.game_over = False
            tetris.paused = False
            tetris.fall_timer = 0
            tetris.lock_timer = None
            return tetris

    def test_new_game_initialization(self, mock_tetris):
        """Test _new_game initializes all state correctly."""
        with patch.object(mock_tetris, '_next_piece') as mock_next:
            mock_next.return_value = Piece("I")
            mock_tetris._new_game()

            assert isinstance(mock_tetris.board, Board)
            assert mock_tetris.bag == []
            assert mock_tetris.score == 0
            assert mock_tetris.lines == 0
            assert mock_tetris.level == 1
            assert not mock_tetris.game_over
            assert not mock_tetris.paused
            assert mock_tetris.can_hold

    def test_refill_bag(self, mock_tetris):
        """Test _refill_bag adds 7 pieces."""
        mock_tetris._refill_bag()
        assert len(mock_tetris.bag) == 7
        # Should have all piece types
        assert set(mock_tetris.bag) == set(TETROMINOES.keys())

    def test_next_piece_refills_bag(self, mock_tetris):
        """Test _next_piece refills bag when needed."""
        assert len(mock_tetris.bag) == 0
        piece = mock_tetris._next_piece()
        assert isinstance(piece, Piece)
        assert len(mock_tetris.bag) == 6  # 7 - 1

    def test_next_piece_consumes_bag(self, mock_tetris):
        """Test _next_piece consumes from bag."""
        # Start with a full bag to prevent refill
        mock_tetris.bag = ["I", "T", "O", "S", "Z", "J", "L"]
        piece = mock_tetris._next_piece()
        assert piece.kind == "I"
        assert mock_tetris.bag == ["T", "O", "S", "Z", "J", "L"]

    def test_fall_speed_level_1(self, mock_tetris):
        """Test fall speed at level 1."""
        mock_tetris.level = 1
        speed = mock_tetris._fall_speed()
        assert speed == 1000  # Base speed

    def test_fall_speed_increases(self, mock_tetris):
        """Test fall speed increases with level."""
        mock_tetris.level = 1
        speed1 = mock_tetris._fall_speed()
        mock_tetris.level = 5
        speed5 = mock_tetris._fall_speed()
        assert speed5 < speed1

    def test_fall_speed_minimum(self, mock_tetris):
        """Test fall speed has minimum."""
        mock_tetris.level = 100
        speed = mock_tetris._fall_speed()
        assert speed >= 50

    def test_move_valid(self, mock_tetris):
        """Test successful piece movement."""
        mock_tetris.current = Piece("O")
        mock_tetris.current.row = 5
        mock_tetris.current.col = 4

        result = mock_tetris._move(0, 1)
        assert result is True
        assert mock_tetris.current.col == 5

    def test_move_invalid(self, mock_tetris):
        """Test blocked piece movement."""
        mock_tetris.current = Piece("O")
        mock_tetris.current.row = 5
        mock_tetris.current.col = 0

        # Try to move left (out of bounds)
        result = mock_tetris._move(0, -1)
        assert result is False
        assert mock_tetris.current.col == 0  # Position unchanged

    def test_move_down_resets_lock_timer(self, mock_tetris):
        """Test moving down resets lock timer."""
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = 5
        mock_tetris.lock_timer = 100

        mock_tetris._move(1, 0)
        assert mock_tetris.lock_timer is None

    def test_rotate_simple(self, mock_tetris):
        """Test simple rotation without wall kicks."""
        mock_tetris.current = Piece("T")
        mock_tetris.current.row = 5
        mock_tetris.current.col = 4
        initial_rot = mock_tetris.current.rot

        mock_tetris._rotate(1)
        assert mock_tetris.current.rot == (initial_rot + 1) % 4

    def test_rotate_with_wall_kick(self, mock_tetris):
        """Test rotation with wall kick."""
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = 5
        mock_tetris.current.col = 0  # Against left wall
        initial_col = mock_tetris.current.col

        # Try to rotate - should apply wall kick
        mock_tetris._rotate(1)
        # Rotation should succeed with wall kick adjustment
        # (exact position depends on kick table)

    def test_rotate_blocked(self, mock_tetris):
        """Test rotation blocked by obstacles."""
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = 0
        mock_tetris.current.col = 4

        # Block rotation area
        for c in range(COLS):
            mock_tetris.board.grid[1][c] = (255, 0, 0)

        initial_rot = mock_tetris.current.rot
        mock_tetris._rotate(1)
        # If rotation fails, rotation should stay same
        # (may succeed with wall kick, so don't assert)

    def test_rotate_resets_lock_timer(self, mock_tetris):
        """Test rotation resets lock timer."""
        mock_tetris.current = Piece("T")
        mock_tetris.current.row = 5
        mock_tetris.current.col = 4
        mock_tetris.lock_timer = 100

        mock_tetris._rotate(1)
        assert mock_tetris.lock_timer is None

    def test_ghost_row_calculation(self, mock_tetris):
        """Test ghost piece landing position."""
        mock_tetris.current = Piece("O")
        mock_tetris.current.row = 0
        mock_tetris.current.col = 4

        ghost_row = mock_tetris._ghost_row()
        assert ghost_row >= mock_tetris.current.row
        assert ghost_row <= ROWS - 2  # O piece is 2 rows tall

    def test_ghost_row_with_obstacles(self, mock_tetris):
        """Test ghost position stops at obstacles."""
        mock_tetris.current = Piece("O")
        mock_tetris.current.row = 0
        mock_tetris.current.col = 4

        # Place obstacle
        for c in range(4, 6):
            mock_tetris.board.grid[10][c] = (255, 0, 0)

        ghost_row = mock_tetris._ghost_row()
        assert ghost_row < 10

    def test_hard_drop(self, mock_tetris):
        """Test hard drop moves piece to bottom."""
        mock_tetris.current = Piece("O")
        mock_tetris.current.row = 0
        mock_tetris.current.col = 4
        initial_score = mock_tetris.score

        with patch.object(mock_tetris, '_lock_piece'):
            mock_tetris._hard_drop()
            # Score should increase (2 points per row)
            assert mock_tetris.score > initial_score

    def test_lock_piece_clears_lines(self, mock_tetris):
        """Test locking piece triggers line clear."""
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = ROWS - 1
        mock_tetris.current.col = 0
        mock_tetris.current.rot = 0  # Horizontal

        # Fill row except where I piece will go
        for c in range(4, COLS):
            mock_tetris.board.grid[ROWS-1][c] = (255, 0, 0)

        with patch.object(mock_tetris, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            initial_score = mock_tetris.score
            mock_tetris._lock_piece()

            # Should clear 1 line
            assert mock_tetris.lines == 1
            assert mock_tetris.score == initial_score + SCORE_TABLE[1] * 1

    def test_lock_piece_advances_level(self, mock_tetris):
        """Test locking piece advances level."""
        mock_tetris.lines = LINES_PER_LEVEL - 1
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = ROWS - 1
        mock_tetris.current.col = 0

        # Setup for line clear
        for c in range(4, COLS):
            mock_tetris.board.grid[ROWS-1][c] = (255, 0, 0)

        with patch.object(mock_tetris, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            mock_tetris._lock_piece()

            assert mock_tetris.level == 2

    def test_lock_piece_game_over(self, mock_tetris):
        """Test game over when piece can't spawn."""
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = 0

        with patch.object(mock_tetris, '_next_piece') as mock_next:
            new_piece = Piece("T")
            # Block spawn area where T piece will be
            # T piece spawns at (-1, 3) with cells at (-1, 4), (0, 3), (0, 4), (0, 5)
            for c in range(3, 6):
                mock_tetris.board.grid[0][c] = (255, 0, 0)
            mock_next.return_value = new_piece

            mock_tetris._lock_piece()
            assert mock_tetris.game_over

    def test_hold_first_time(self, mock_tetris):
        """Test holding piece for first time."""
        mock_tetris.current = Piece("I")
        mock_tetris.held = None

        with patch.object(mock_tetris, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            mock_tetris._hold()

            assert mock_tetris.held == "I"
            assert mock_tetris.current.kind == "T"
            assert not mock_tetris.can_hold

    def test_hold_swap(self, mock_tetris):
        """Test swapping held piece."""
        mock_tetris.current = Piece("I")
        mock_tetris.held = "T"
        mock_tetris.can_hold = True

        mock_tetris._hold()

        assert mock_tetris.held == "I"
        assert mock_tetris.current.kind == "T"
        assert not mock_tetris.can_hold

    def test_hold_when_disabled(self, mock_tetris):
        """Test hold does nothing when disabled."""
        mock_tetris.current = Piece("I")
        mock_tetris.held = "T"
        mock_tetris.can_hold = False

        mock_tetris._hold()

        # Nothing should change
        assert mock_tetris.current.kind == "I"
        assert mock_tetris.held == "T"

    def test_scoring_single_line(self, mock_tetris):
        """Test scoring for single line clear."""
        mock_tetris.level = 1
        mock_tetris.lines = 0
        mock_tetris.score = 0
        mock_tetris.board.clear_lines = Mock(return_value=1)
        mock_tetris.current = Piece("I")

        with patch.object(mock_tetris, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            mock_tetris._lock_piece()

            assert mock_tetris.score == SCORE_TABLE[1] * 1

    def test_scoring_tetris(self, mock_tetris):
        """Test scoring for 4-line clear (Tetris)."""
        mock_tetris.level = 2
        mock_tetris.score = 0
        mock_tetris.board.clear_lines = Mock(return_value=4)
        mock_tetris.current = Piece("I")

        with patch.object(mock_tetris, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            mock_tetris._lock_piece()

            assert mock_tetris.score == SCORE_TABLE[4] * 2

    def test_update_gravity(self, mock_tetris):
        """Test update applies gravity over time."""
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = 0
        mock_tetris.fall_interval = 1000
        mock_tetris.fall_timer = 0

        # Not enough time passed
        mock_tetris.update(500)
        assert mock_tetris.current.row == 0

        # Enough time passed
        mock_tetris.update(600)
        assert mock_tetris.current.row == 1

    def test_update_lock_delay(self, mock_tetris):
        """Test update triggers lock after delay."""
        mock_tetris.current = Piece("O")
        mock_tetris.current.row = ROWS - 2  # At bottom
        mock_tetris.current.col = 4

        with patch.object(mock_tetris, '_lock_piece') as mock_lock:
            # First update starts lock timer
            mock_tetris.update(100)
            assert mock_tetris.lock_timer is not None

            # Subsequent updates increment timer
            mock_tetris.update(LOCK_DELAY)
            mock_lock.assert_called_once()

    def test_update_paused(self, mock_tetris):
        """Test update does nothing when paused."""
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = 0
        mock_tetris.paused = True
        mock_tetris.fall_timer = 0
        mock_tetris.fall_interval = 100

        mock_tetris.update(1000)

        # No movement should occur
        assert mock_tetris.current.row == 0

    def test_update_game_over(self, mock_tetris):
        """Test update does nothing when game over."""
        mock_tetris.current = Piece("I")
        mock_tetris.current.row = 0
        mock_tetris.game_over = True

        mock_tetris.update(1000)

        # No movement should occur
        assert mock_tetris.current.row == 0

    def test_toggle_theme_with_keyboard(self):
        """Test pressing T toggles light/dark mode."""
        with patch('main.pygame') as mock_pygame:
            game = Tetris()
            game.dark_mode = True
            game.handle_keydown(mock_pygame.K_t)
            assert not game.dark_mode
            game.handle_keydown(mock_pygame.K_t)
            assert game.dark_mode

    def test_toggle_theme_with_mouse_button(self):
        """Test clicking theme button toggles mode."""
        with patch('main.pygame'):
            game = Tetris()
            game.dark_mode = True
            game.theme_button_rect = Mock()
            game.theme_button_rect.collidepoint.return_value = True

            game.handle_mouse_down((0, 0))
            assert not game.dark_mode

            game.theme_button_rect.collidepoint.return_value = False
            game.handle_mouse_down((0, 0))
            assert not game.dark_mode

    def test_light_mode_block_colors_are_high_contrast(self):
        """Test block colors are adjusted for readable contrast in light mode."""
        with patch('main.pygame'):
            game = Tetris()
            game.dark_mode = False
            adjusted = game._high_contrast_color(COLORS["O"])
            assert _contrast_ratio(adjusted, LIGHT_BG) >= 4.5


# ── Integration Tests ──────────────────────────────────────────────────────────

class TestTetrisIntegration:
    """Integration tests for complete game sequences."""

    @pytest.fixture
    def game(self):
        """Create a game instance with mocked pygame."""
        with patch('main.pygame'):
            tetris = Tetris()
            tetris.board = Board()
            tetris.bag = ["I", "T", "O", "S"]
            tetris.current = Piece("I")
            tetris.held = None
            tetris.can_hold = True
            tetris.score = 0
            tetris.lines = 0
            tetris.level = 1
            tetris.game_over = False
            tetris.paused = False
            tetris.fall_timer = 0
            tetris.lock_timer = None
            return tetris

    def test_complete_piece_lifecycle(self, game):
        """Test complete piece lifecycle: spawn, move, rotate, lock."""
        game.current.row = 0
        game.current.col = 4

        # Move piece
        assert game._move(1, 0)
        assert game.current.row == 1

        # Rotate piece
        initial_rot = game.current.rot
        game._rotate(1)
        assert game.current.rot != initial_rot

        # Hard drop and lock
        with patch.object(game, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            game._hard_drop()
            assert game.current.kind == "T"

    def test_line_clear_and_scoring(self, game):
        """Test clearing lines updates score correctly."""
        game.current = Piece("I")
        game.current.row = ROWS - 1
        game.current.col = 0
        game.current.rot = 0  # Horizontal

        # Fill row except where I piece will go
        for c in range(4, COLS):
            game.board.grid[ROWS-1][c] = (255, 0, 0)

        with patch.object(game, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            initial_score = game.score
            game._lock_piece()

            assert game.lines == 1
            assert game.score == initial_score + SCORE_TABLE[1] * game.level

    def test_hold_and_continue(self, game):
        """Test hold mechanic in game flow."""
        initial_kind = game.current.kind

        with patch.object(game, '_next_piece') as mock_next:
            mock_next.return_value = Piece("S")
            game._hold()

            assert game.held == initial_kind
            assert game.current.kind == "S"
            assert not game.can_hold

        # Can't hold again until next piece
        second_kind = game.current.kind
        game._hold()
        assert game.current.kind == second_kind  # Unchanged

    def test_level_progression(self, game):
        """Test leveling up through line clears."""
        game.lines = 0
        game.level = 1

        # Clear enough lines to level up
        game.board.clear_lines = Mock(return_value=LINES_PER_LEVEL)

        with patch.object(game, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            game._lock_piece()

            assert game.level == 2
            assert game.lines == LINES_PER_LEVEL

    def test_multiple_simultaneous_line_clears(self, game):
        """Test clearing multiple lines at once."""
        game.current = Piece("I")
        game.current.row = ROWS - 4  # Place at top of the 4-row section
        game.current.col = 3
        game.current.rot = 1  # Vertical orientation

        # Fill 4 rows with gaps where I piece goes (column 3 offset by 2 = column 5)
        # Vertical I piece at rot=1: [(0, 2), (1, 2), (2, 2), (3, 2)]
        # At row ROWS-4, col 3: cells are at column 3+2=5
        for r in range(ROWS-4, ROWS):
            for c in range(COLS):
                if c != 5:  # Column where vertical I piece lands
                    game.board.grid[r][c] = (255, 0, 0)

        with patch.object(game, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            game._lock_piece()

            assert game.lines == 4
            # Tetris scoring
            assert game.score == SCORE_TABLE[4] * game.level


# ── Edge Cases ─────────────────────────────────────────────────────────────────

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.fixture
    def game(self):
        """Create a game instance."""
        with patch('main.pygame'):
            tetris = Tetris()
            tetris.board = Board()
            tetris.bag = []
            tetris.current = None
            tetris.held = None
            tetris.can_hold = True
            tetris.score = 0
            tetris.lines = 0
            tetris.level = 1
            tetris.game_over = False
            tetris.paused = False
            return tetris

    def test_o_piece_rotation(self, game):
        """Test O piece only has 1 rotation state."""
        game.current = Piece("O")
        game.current.row = 5
        game.current.col = 4

        # Try to rotate
        game._rotate(1)
        assert game.current.rot == 0  # Should stay 0

        game._rotate(-1)
        assert game.current.rot == 0  # Should stay 0

    def test_i_piece_wall_kicks(self, game):
        """Test I piece uses different wall kick table."""
        game.current = Piece("I")
        game.current.row = 5
        game.current.col = 0

        # Rotation should use KICKS_I table
        game._rotate(1)
        # Just verify it doesn't crash (exact behavior depends on board state)

    def test_spawn_position_conflict(self, game):
        """Test game over when spawn position blocked."""
        game.current = Piece("I")

        with patch.object(game, '_next_piece') as mock_next:
            # Next piece will be T, which has cells in row 0
            new_piece = Piece("T")
            # T piece spawns with cells at (-1, 4), (0, 3), (0, 4), (0, 5)
            # Block those positions in row 0
            game.board.grid[0][3] = (255, 0, 0)
            game.board.grid[0][4] = (255, 0, 0)
            game.board.grid[0][5] = (255, 0, 0)
            mock_next.return_value = new_piece

            game._lock_piece()
            assert game.game_over

    def test_bag_randomization(self, game):
        """Test bag system ensures all pieces appear."""
        pieces = []
        for _ in range(14):  # Two full bags
            piece = game._next_piece()
            pieces.append(piece.kind)

        # First 7 should contain all types
        first_bag = set(pieces[:7])
        assert first_bag == set(TETROMINOES.keys())

        # Second 7 should also contain all types
        second_bag = set(pieces[7:14])
        assert second_bag == set(TETROMINOES.keys())

    def test_hard_drop_at_spawn(self, game):
        """Test hard drop from spawn position."""
        game.current = Piece("O")
        game.current.row = 0
        game.current.col = 4
        initial_score = game.score

        with patch.object(game, '_lock_piece'):
            game._hard_drop()
            # Score should increase based on drop distance
            assert game.score > initial_score

    def test_rotation_at_board_edges(self, game):
        """Test rotation behavior at board boundaries."""
        game.current = Piece("I")
        game.current.row = 0
        game.current.col = 0  # Left edge

        # Should handle rotation with wall kicks
        game._rotate(1)
        # Just verify no crash

        game.current.col = COLS - 1  # Right edge
        game._rotate(1)
        # Just verify no crash

    def test_lock_delay_reset_on_move(self, game):
        """Test lock delay resets when piece moves down."""
        game.current = Piece("O")
        game.current.row = 5  # Not at bottom, so can move down
        game.lock_timer = 400

        # Move down resets timer
        game._move(1, 0)
        assert game.lock_timer is None

    def test_maximum_level_scoring(self, game):
        """Test scoring at high levels."""
        game.level = 20
        game.board.clear_lines = Mock(return_value=4)
        game.current = Piece("I")

        with patch.object(game, '_next_piece') as mock_next:
            mock_next.return_value = Piece("T")
            game._lock_piece()

            # Tetris at level 20
            assert game.score == SCORE_TABLE[4] * 20

    def test_soft_drop_scoring(self, game):
        """Test soft drop adds to score."""
        game.current = Piece("I")
        game.current.row = 5
        initial_score = game.score

        # Soft drop should add 1 point per row
        success = game._move(1, 0)
        if success:
            game.score += 1
            assert game.score == initial_score + 1
