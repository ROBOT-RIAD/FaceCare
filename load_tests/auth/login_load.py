import os


def login(self, credentials=None):
	if credentials is None:
		credentials = {
			"email": os.getenv("LOCUST_LOGIN_EMAIL", "load-test@example.com"),
			"password": os.getenv("LOCUST_LOGIN_PASSWORD", "strong-password-123"),
		}

	payload = {
		"email": credentials["email"],
		"password": credentials["password"],
	}

	with self.client.post(
		"/api/v1/login/",
		data=payload,
		name="POST /api/v1/login/",
		catch_response=True,
	) as response:
		if response.status_code == 200:
			response.success()
			return response.json().get("data", {}).get("access_token")
		elif response.status_code == 429:
			response.failure("Login rate limit reached")
		else:
			error_message = (
				f"Expected 200, received {response.status_code}: "
				f"{response.text[:500]}"
			)
			print(error_message)
			response.failure(error_message)

	return None
