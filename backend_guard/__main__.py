"""CLI entrypoint."""

from backend_guard.cli.app import app


def main() -> None:
    """Run the CLI."""
    app()


if __name__ == "__main__":
    main()
