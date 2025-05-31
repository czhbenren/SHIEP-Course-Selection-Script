import sys
import asyncio

from main_select_courses import main_select_courses
from inquire_course_info import inquire_course_info
from verify_cookie_validity import verify_cookie_validity
from check_course import check_course


def display_help():
    """
    Show Commands
    """
    print("Usage: python main.py <command>")
    print("Commands:")
    print("  --start    : Select courses for all users")
    print("  --inquire  : Inquire course info")
    print("  --validate : Batch validate cookie validity")
    print("  --check    : Verify course availability")


async def main():
    if len(sys.argv) < 2:
        display_help()
        return

    match sys.argv[1].lower():  # Only use the first argument
        case "--start":
            await main_select_courses()
        case "--inquire":
            await inquire_course_info()
        case "--validate":
            await verify_cookie_validity()
        case "--check":
            await check_course()
        case _:
            print("Error: Unknown command.")
            display_help()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        print("Exiting application.")
