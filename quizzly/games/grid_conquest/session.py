"""Compatibility imports for Grid Conquest's original durable-session API."""

from quizzly.games.board_session import assign_joiner, checkpoint, command, is_board, restore

__all__ = ["assign_joiner", "checkpoint", "command", "is_board", "restore"]
