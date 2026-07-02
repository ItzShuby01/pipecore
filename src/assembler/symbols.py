from __future__ import annotations


class SymbolTable:
    def __init__(self) -> None:
        self.symbols: dict[str, int] = {}

    def define(self, name: str, address: int) -> None:
        """Binds a text label to a specific word address in memory."""
        self.symbols[name] = address

    def resolve(self, name: str) -> int:
        """Returns the word address of a label. Raises error if missing."""
        if name not in self.symbols:
            raise KeyError(
                f"Compilation Error: Unresolved label symbol '{name}'")
        return self.symbols[name]

    def exists(self, name: str) -> bool:
        return name in self.symbols
