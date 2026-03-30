from __future__ import annotations

from dataclasses import dataclass

try:
    from pynput.mouse import Button, Controller
except Exception:  # pragma: no cover
    Button = None
    Controller = None


@dataclass(slots=True)
class MouseController:
    dry_run: bool = False

    def __post_init__(self) -> None:
        self._controller = None if self.dry_run or Controller is None else Controller()
        self._down = False

    def move(self, x: float, y: float) -> None:
        if self._controller is not None:
            self._controller.position = (int(x), int(y))

    def set_touch(self, active: bool) -> None:
        if self._controller is None or Button is None:
            return
        if active and not self._down:
            self._controller.press(Button.left)
            self._down = True
        elif not active and self._down:
            self._controller.release(Button.left)
            self._down = False
