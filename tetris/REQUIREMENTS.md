# Tetris Requirements

This document captures the current behavior of the `tetris` implementation so it can be used as the baseline for future spec-driven development.

## Scope

- The application is a single-player Tetris game implemented in Python with `pygame`.
- The game runs in a fixed-size window with a playfield and a sidebar.

## Gameplay Requirements

### Board and Pieces

- The playfield must be 10 columns by 20 rows.
- The game must support the 7 standard tetromino types: I, O, T, S, Z, J, and L.
- Each tetromino must use its defined color.
- New pieces must spawn near the top-center of the board.
- Piece generation must use a shuffled 7-bag system.

### Movement and Rotation

- Players must be able to move the active piece left and right.
- Players must be able to soft drop and hard drop the active piece.
- Players must be able to rotate pieces clockwise and counter-clockwise.
- Rotation must use the existing wall-kick behavior:
  - I pieces use the dedicated I-piece kick table.
  - J, L, S, T, and Z pieces use the shared kick table.
- O pieces must not require multi-state rotation behavior beyond their single defined state.

### Hold and Preview

- Players must be able to hold the current piece.
- Hold may only be used once per active piece until that piece locks.
- The sidebar must show the next queued piece.
- The sidebar must show the held piece when one exists.

### Gravity, Locking, and Progression

- Active pieces must fall automatically over time.
- Fall speed must increase as the level increases.
- A landed piece must lock after the current lock delay if it is not moved or rotated away from the landing position.
- Completed lines must be cleared immediately after a piece locks.
- Level progression must increase by 1 every 10 cleared lines.
- The game must end when a new piece cannot spawn in a valid position.

## Scoring Requirements

- Soft drop must award 1 point per successful downward move.
- Hard drop must award 2 points per successful downward move during the drop.
- Line clears must award points multiplied by the current level using this table:
  - 1 line: 100
  - 2 lines: 300
  - 3 lines: 500
  - 4 lines: 800

## Controls Requirements

- Left Arrow: move left
- Right Arrow: move right
- Down Arrow: soft drop
- Up Arrow or X: rotate clockwise
- Z: rotate counter-clockwise
- Space: hard drop
- C: hold piece
- P: pause or resume
- R: restart after game over

## Rendering Requirements

- The window must include:
  - the main playfield
  - a sidebar for score, lines, level, next piece, hold piece, and controls
- The game must render a ghost piece indicating the landing position of the active piece.
- The game must show a paused overlay when paused.
- The game must show a game-over overlay when the player loses.

## Session Requirements

- Starting a new game must reset the board, score, lines, level, hold state, timers, and game-over state.
- Restarting after game over must start a fresh game session.
