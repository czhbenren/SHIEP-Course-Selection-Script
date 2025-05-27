import asyncio
from tqdm.asyncio import tqdm

from core import run_course_selection_loop_for_user
from inquire_course_info import inquire_course_info_async
from custom import USER_CONFIGS


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


async def main():
    task_choice = input("What do you want to do?\n[1] Select courses for all users\n[2] Inquire course info\nChoice: ").strip()
    if task_choice == "1":
        await main_select_courses()
    elif task_choice == "2":
        print("Running course info inquiry...")
        await inquire_course_info_async()
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user.")
    finally:
        print("Exiting application.")
