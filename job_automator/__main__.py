"""Entry point for `python -m job_automator` and the `job` CLI command."""

from job_automator.cli import app


def main():
    app()


if __name__ == "__main__":
    main()
