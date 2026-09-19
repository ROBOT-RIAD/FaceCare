
import os
import uuid


def register(self):
    email = f"load-{uuid.uuid4().hex}@example.com"
    payload = {
        "email": email,
        "password": os.getenv("LOCUST_TEST_PASSWORD", "strong-password-123"),
        "full_name": "Load Test User",
        "gender": "Male",
        "contact_number": "+8801700000000",
        "skin_type": "Oily",
        "date_of_birth": "2000-01-15",
    }

    with self.client.post(
        "/api/v1/register/",
        data=payload,
        name="POST /api/v1/register/",
        catch_response=True,
    ) as response:
        if response.status_code == 201:
            response.success()
        elif response.status_code == 429:
            response.failure("Register rate limit reached")
        else:
            error_message = (
                f"Expected 201, received {response.status_code}: "
                f"{response.text[:500]}"
            )
            print(error_message)
            response.failure(error_message)