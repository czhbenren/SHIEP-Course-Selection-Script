import sys
import asyncio
from tqdm.asyncio import tqdm

from core import run_course_selection_loop_for_user
from inquire_course_info import inquire_course_info
from custom import USER_CONFIGS, INQUIRY_USER_DATA


async def main_select_courses():
    if not USER_CONFIGS:
        print("No user configurations found in custom.py. Exiting course selection.")
        return

    all_selection_tasks = []
    print("Preparing course selection tasks for all users...")

    for user_config in USER_CONFIGS:
        user_label = user_config.get("label", "Unknown_User")
        user_cookies = user_config.get("cookies")
        user_profile_id = user_config.get("profileId")
        user_course_ids = user_config.get("course_ids", [])

        if not user_cookies or not user_profile_id:
            user_cookies = INQUIRY_USER_DATA.get("cookies")
            user_profile_id = INQUIRY_USER_DATA.get("profileId")
            print(f"Warning: Using inquiry user data for user '{user_label}' due to missing cookies or profileId.")

        if not all([user_cookies, user_profile_id, user_course_ids]):
            print(f"Warning: Skipping user '{user_label}' due to missing cookies, profileId, or course_ids.")
            continue

        for course_id in user_course_ids:
            print(f"Queueing selection for User: {user_label}, Course ID: {course_id}")
            task = run_course_selection_loop_for_user(
                course_id_to_select=course_id,
                user_label=user_label,
                user_cookies=user_cookies,
                user_profile_id=user_profile_id,
            )
            all_selection_tasks.append(task)

    if not all_selection_tasks:
        print("No valid course selection tasks were created. Exiting.")
        return

    print(f"\nStarting selection for {len(all_selection_tasks)} course(s) across all users...\n")
    await tqdm.gather(*all_selection_tasks, desc="Overall Course Selection Progress")

    print("\nAll course selection tasks have been processed.")
    await asyncio.sleep(0.1)  # Add a small delay to ensure all print statements from tasks are flushed


def display_help():
    """
    Show Commands
    """
    print("Usage: python main.py <command>")
    print("Commands:")
    print("  --start    : Select courses for all users")
    print("  --inquire  : Inquire course info")
    print("  --validate : Batch validate cookie validity")
    print("  --spots    : Verify course availability")


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
            pass
        case "--check":
            pass
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
