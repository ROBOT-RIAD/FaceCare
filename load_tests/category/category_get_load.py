
def get_all_category(self):
    with self.client.get(
        "/api/v1/category/",
        name="GET /api/v1/category/",
        catch_response=True,
    ) as response:
        if response.status_code == 200:
            response.success()
        elif response.status_code == 429:
            response.failure("Category list rate limit reached")
        else:
            error_message = (
                f"Expected 200, received {response.status_code}: "
                f"{response.text[:500]}"
            )
            print(error_message)
            response.failure(error_message)
