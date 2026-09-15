import os
import uuid
from pathlib import Path

from locust import HttpUser, between, task


class PublicApiUser(HttpUser):
    """Load tests for APIs available without authentication."""

    wait_time = between(1, 3)

    @task
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

    # @task
    # def register(self):
    #     email = f"load-{uuid.uuid4().hex}@example.com"

    #     payload = {
    #         "email": email,
    #         "password": os.getenv("LOCUST_TEST_PASSWORD", "strong-password-123"),
    #         "full_name": "Load Test User",
    #         "gender": "Male",
    #         "contact_number": "+8801700000000",
    #         "skin_type": "Oily",
    #         "date_of_birth": "2000-01-15",
    #     }

    #     image_dir = Path(__file__).resolve().parent
    #     image_candidates = [
    #         image_dir / "test_image.jpeg",
    #         image_dir / "test_iamge.jpeg",
    #         image_dir.parent / "test_image.jpeg",
    #         image_dir.parent / "test_iamge.jpeg",
    #     ]
    #     image_path = next((p for p in image_candidates if p.exists()), image_dir / "test_image.jpeg")

    #     with image_path.open("rb") as image:
    #         files = {
    #             "image": (
    #                 image_path.name,
    #                 image,
    #                 "image/jpeg",
    #             )
    #         }

    #         with self.client.post(
    #             "/api/v1/register/",
    #             data=payload,
    #             files=files,
    #             name="POST /api/v1/register/",
    #             catch_response=True,
    #         ) as response:

    #             if response.status_code == 201:
    #                 response.success()

    #             elif response.status_code == 429:
    #                 response.failure("Register rate limit reached")

    #             else:
    #                 response.failure(
    #                     f"Expected 201, received {response.status_code}: "
    #                     f"{response.text[:200]}"
    #                 )


    class UserApiUser(HttpUser):
        """Add authenticated user API tasks here when those endpoints exist."""

        abstract = True
        wait_time = between(1, 3)

        def auth_headers(self):
            access_token = os.getenv("LOCUST_USER_ACCESS_TOKEN")
            if not access_token:
                return {}
            return {"Authorization": f"Bearer {access_token}"}


class AdminApiUser(HttpUser):
    """Add authenticated admin API tasks here when those endpoints exist."""

    abstract = True
    wait_time = between(1, 3)

    def auth_headers(self):
        access_token = os.getenv("LOCUST_ADMIN_ACCESS_TOKEN")
        if not access_token:
            return {}
        return {"Authorization": f"Bearer {access_token}"}