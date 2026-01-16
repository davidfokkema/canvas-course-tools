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
        base_url = canvas_tasks._url
        headers = canvas_tasks._headers
    except Exception as e:
        print(f"Error getting credentials: {e}")
        print("Please ensure your config file is set up correctly.")
        return

    with httpx.Client(base_url=base_url, headers=headers) as client:
        # Initialize loop variables
        next_url = "/api/v1/courses"
        params = COURSES_PARAMS
        request_count = 0

        while next_url:
            request_count += 1
            print(f"\n--- Making request #{request_count} to: {next_url} ---")

            try:
                response = client.get(next_url, params=params)
                response.raise_for_status()
            except httpx.HTTPError as e:
                print(f"HTTP error on request #{request_count}: {e}")
                break  # Exit loop on error

            response_json = response.json()
            validate_courses(f"RESPONSE #{request_count}", response_json)

            # Get the URL for the next iteration
            next_url = response.links.get("next", {}).get("url")

            # Clear params after the first request, as the next_url is opaque
            if params:
                params = None

    print(f"\n--- Loop finished after {request_count} request(s). ---")


if __name__ == "__main__":
    main()
