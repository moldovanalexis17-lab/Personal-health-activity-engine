"""Portfolio entry point for the Personal Health & Activity Engine."""

from test_sheets import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user.")
