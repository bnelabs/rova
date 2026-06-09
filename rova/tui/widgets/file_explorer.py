"""File explorer widget — tree view of the workspace directory."""

from __future__ import annotations

from pathlib import Path

from textual.widgets import Tree
from textual.message import Message


class FileExplorer(Tree[Path]):
    """A directory tree widget showing the workspace file structure.

    Click a file to preview it. Directories are expandable.
    """

    class FileSelected(Message):
        """Posted when a file is selected (clicked)."""

        def __init__(self, path: Path) -> None:
            super().__init__()
            self.path = path

    def __init__(self, workspace_dir: Path, **kwargs) -> None:
        super().__init__("Workspace", **kwargs)
        self.workspace_dir = workspace_dir
        self.show_root = True

    def on_mount(self) -> None:
        self._populate()

    def _populate(self) -> None:
        """Build the tree from the workspace directory."""
        self.root.remove_children()
        if not self.workspace_dir.exists():
            return
        self._add_directory(self.root, self.workspace_dir)

    def _add_directory(self, parent, path: Path) -> None:
        """Recursively add directory contents to the tree."""
        try:
            entries = sorted(
                [p for p in path.iterdir() if p.name != ".gitkeep"],
                key=lambda p: (not p.is_dir(), p.name.lower()),
            )
        except PermissionError:
            return

        for entry in entries:
            if entry.is_dir():
                branch = parent.add(entry.name, entry)
                self._add_directory(branch, entry)
            else:
                parent.add_leaf(entry.name, entry)

    def refresh_tree(self) -> None:
        """Rebuild the tree (e.g., after a file is created)."""
        self._populate()

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Post a message when a file node is selected."""
        node = event.node
        if node.data is not None and isinstance(node.data, Path) and node.data.is_file():
            self.post_message(self.FileSelected(node.data))
