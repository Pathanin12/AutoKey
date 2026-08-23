import sys
from pathlib import Path


def bootstrap() -> None:
    project_root = Path(__file__).resolve().parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


def main() -> None:
    bootstrap()
    from ui.main_window import MainWindow

    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
