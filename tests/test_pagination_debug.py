import httpx
import json
from canvas_course_tools.utils import get_canvas
from canvas_course_tools.datatypes import Course
from pydantic import ValidationError

# --- SCRIPT CONFIGURATION ---
SERVER_ALIAS = "vu"
COURSES_PARAMS = {"per_page": 2, "include[]": "term"}


def validate_courses(response_name, courses_json):
    """Loops through a list of course data and validates each one."""
    print(f"\n--- Validating Courses for {response_name} ---")
    all_ok = True
    for i, course_data in enumerate(courses_json):
        try:
            course = Course.model_validate(course_data)
            print(f"  - Course {i + 1}: OK | Name: '{course.name}', Term: '{course.term}'")
        except ValidationError as e:
            all_ok = False
            print(f"  - Course {i + 1}: VALIDATION FAILED")
            print("    --- Failing Course Data ---")
            # Pretty print the specific failing object
            print(f"    {json.dumps(course_data, indent=4)}")
            print("    --- Pydantic Error ---")
            print(f"    {e}\n")
    if all_ok:
        print("  - All courses validated successfully.")


def main():
    """
    Diagnostic script to debug Canvas API pagination and Pydantic validation.
    """
    print(f"--- Getting credentials for server: '{SERVER_ALIAS}' ---")
    try:
        canvas_tasks = get_canvas(SERVER_ALIAS)
        url = canvas_tasks._url
        headers = canvas_tasks._headers
    except Exception as e:
        print(f"Error getting credentials: {e}")
        print("Please ensure your config file is set up correctly.")
        return

    # --- 1. FIRST REQUEST ---
    first_request_url = f"{url}/api/v1/courses"
    print(f"\n--- 1. Making FIRST request to: {first_request_url} with params: {COURSES_PARAMS} ---")

    try:
        response1 = httpx.get(first_request_url, headers=headers, params=COURSES_PARAMS)
        response1.raise_for_status()
    except httpx.HTTPError as e:
        print(f"HTTP error on first request: {e}")
        return

    response1_json = response1.json()
    validate_courses("FIRST RESPONSE", response1_json)

    # --- 2. EXTRACT NEXT URL AND PREPARE FOR SECOND REQUEST ---
    next_url = response1.links.get("next", {}).get("url")

    if not next_url:
        print("\n--- No 'next' link found. Cannot make second request. ---")
        return

    print(f"\n--- 2. Extracted NEXT request URL from Link header: {next_url} ---")
    print("--- Making SECOND request to this opaque URL with NO additional params ---")

    try:
        response2 = httpx.get(next_url, headers=headers)
        response2.raise_for_status()
    except httpx.HTTPError as e:
        print(f"HTTP error on second request: {e}")
        return

    response2_json = response2.json()
    validate_courses("SECOND RESPONSE", response2_json)

    print("\n--- Script finished. ---")


if __name__ == "__main__":
    main()
