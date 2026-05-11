# Tetris Test Suite

Comprehensive test suite for the Tetris implementation with 61 tests covering core game logic, piece mechanics, board management, and edge cases.

## Test Coverage

**Overall Coverage: 56%** (304 statements, 171 covered)

The test suite focuses on core game logic while excluding pygame-specific rendering code. Core game mechanics have near-complete coverage.

## Running Tests

### Install Dependencies

```bash
pip install pytest pytest-cov pygame
```

### Run All Tests

```bash
pytest test_tetris.py -v
```

### Run Tests with Coverage

```bash
pytest test_tetris.py --cov=main --cov-report=term-missing
```

### Run Specific Test Class

```bash
# Test only Board functionality
pytest test_tetris.py::TestBoard -v

# Test only game logic
pytest test_tetris.py::TestTetrisGameLogic -v

# Test integration scenarios
pytest test_tetris.py::TestTetrisIntegration -v

# Test edge cases
pytest test_tetris.py::TestEdgeCases -v
```

## Test Organization

### 1. Board Tests (11 tests)
Tests for the game board grid management:
- ✓ Board initialization and empty grid creation
- ✓ Cell validity checking (bounds and collisions)
- ✓ Piece locking onto the board
- ✓ Line clearing (single, multiple, non-consecutive)
- ✓ Handling negative rows (spawn area)

**Coverage:** Complete coverage of Board class methods

### 2. Piece Tests (7 tests)
Tests for tetromino piece representation:
- ✓ Piece initialization with correct defaults
- ✓ All 7 piece types (I, O, T, S, Z, J, L)
- ✓ Cell coordinate calculations
- ✓ Custom positions and rotations
- ✓ Correct rotation counts per piece type
- ✓ Piece shape definitions

**Coverage:** Complete coverage of Piece class methods

### 3. Game Logic Tests (29 tests)
Tests for core Tetris game mechanics:

**Movement & Positioning:**
- ✓ Valid and invalid piece movement
- ✓ Movement boundary checking
- ✓ Lock timer reset on downward movement

**Rotation:**
- ✓ Simple rotation without obstacles
- ✓ Wall-kick rotation system (SRS)
- ✓ Rotation blocking by obstacles
- ✓ Lock timer reset on rotation

**Dropping:**
- ✓ Hard drop mechanics and scoring
- ✓ Ghost piece landing position calculation

**Piece Management:**
- ✓ 7-bag randomization system
- ✓ Bag refill mechanics
- ✓ Piece spawning from bag

**Hold Mechanic:**
- ✓ First-time hold (swap with next piece)
- ✓ Piece swapping
- ✓ Hold disabled after use until next lock

**Scoring & Progression:**
- ✓ Line clear scoring (single, double, triple, tetris)
- ✓ Level-based score multipliers
- ✓ Level advancement (10 lines per level)
- ✓ Fall speed calculation per level
- ✓ Fall speed minimum cap

**Game State:**
- ✓ Game initialization
- ✓ Game over detection on spawn collision
- ✓ Pause/resume functionality
- ✓ Gravity and fall timer mechanics
- ✓ Lock delay timer (500ms before locking)

**Coverage:** ~85% of game logic methods (excludes rendering)

### 4. Integration Tests (5 tests)
Tests for complete game sequences:
- ✓ Full piece lifecycle (spawn → move → rotate → lock)
- ✓ Line clearing with score updates
- ✓ Hold mechanic workflow
- ✓ Level progression through line clears
- ✓ Multiple simultaneous line clears (Tetris)

### 5. Edge Case Tests (9 tests)
Tests for boundary conditions and special cases:
- ✓ O-piece single rotation state
- ✓ I-piece special wall-kick table
- ✓ Spawn position conflicts causing game over
- ✓ 7-bag randomization ensuring all pieces
- ✓ Hard drop from spawn position
- ✓ Rotation at board edges
- ✓ Lock delay reset behavior
- ✓ Maximum level scoring
- ✓ Soft drop scoring

## What's Tested

### Core Game Logic (Fully Tested)
- ✅ Board collision detection
- ✅ Line clearing algorithm
- ✅ Piece movement and rotation
- ✅ SRS wall-kick system
- ✅ 7-bag randomization
- ✅ Scoring calculations
- ✅ Level progression
- ✅ Hold mechanic
- ✅ Lock delay
- ✅ Game over conditions
- ✅ Ghost piece calculation

### Not Tested (Pygame-Dependent)
- ❌ Rendering/drawing functions
- ❌ Pygame event handling loop
- ❌ Keyboard input processing
- ❌ Display and graphics
- ❌ Font rendering
- ❌ Surface blitting

These rendering functions constitute the missing 44% of coverage and would require pygame mock setup or integration testing that's beyond unit test scope.

## Test Strategy

### Mocking Approach
Tests use Python's `unittest.mock` to:
- Mock pygame initialization
- Isolate game logic from rendering
- Mock piece generation for deterministic tests
- Control randomization for predictable outcomes

### Fixtures
Pytest fixtures provide:
- `mock_tetris`: Clean Tetris instance with mocked pygame
- `game`: Fully initialized game state for integration tests

### Test Patterns
1. **Arrange**: Set up game state and test conditions
2. **Act**: Execute the method under test
3. **Assert**: Verify expected outcomes

## Key Testing Insights

### Spawn Position
- Pieces spawn at row -1 (above visible board)
- T piece has cells at both row -1 and row 0 at spawn
- I piece spawns entirely at row -1
- Negative rows are valid but don't check collisions

### Lock Timer Behavior
- Lock timer starts when piece lands
- Resets to None when piece moves down
- Resets to None when piece rotates
- Does NOT reset on horizontal movement
- Locks piece after 500ms

### Rotation System
- Uses SRS (Super Rotation System)
- Different wall-kick tables for I vs other pieces
- O piece has only 1 rotation state
- Other pieces have 4 rotation states

### 7-Bag System
- Ensures all 7 pieces appear before repeating
- Bag refills when fewer than 7 pieces remain
- Provides fair randomization

## Running the Game

To verify the actual game still works:

```bash
python3 main.py
```

## Test Maintenance

When modifying game logic:
1. Run tests to ensure no regressions
2. Update tests if behavior intentionally changes
3. Add new tests for new features
4. Maintain ~85%+ coverage of game logic

## Future Enhancements

Potential additions to test suite:
- [ ] Performance benchmarks
- [ ] Pygame integration tests with headless display
- [ ] Input handling tests with pygame events
- [ ] Visual regression tests for rendering
- [ ] Property-based testing with hypothesis
- [ ] Stress testing (long game sessions)
- [ ] Multiplayer/concurrent game tests (if added)

## Dependencies

- Python >= 3.12
- pygame >= 2.6.1
- pytest >= 8.0.0
- pytest-cov >= 4.1.0

## License

Tests follow the same license as the main codebase.
