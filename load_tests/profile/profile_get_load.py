
def profile(self):
	with self.client.get(
		"/api/v1/profile/",
		headers=self.auth_headers(),
		name="GET /api/v1/profile/",
		catch_response=True,
	) as response:
		if response.status_code == 200:
			response.success()
		elif response.status_code == 401:
			response.failure("Profile access requires a valid access token")
		elif response.status_code == 429:
			response.failure("Profile access rate limit reached")
		else:
			error_message = (
				f"Expected 200, received {response.status_code}: "
				f"{response.text[:500]}"
			)
			print(error_message)
			response.failure(error_message)
