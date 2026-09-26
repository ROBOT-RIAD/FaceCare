import os
from locust import HttpUser, between, task

from load_tests.auth.login_load import login as login_load
from load_tests.auth.register_load import register as register_load
from load_tests.profile.profile_get_load import profile as profile_load




class PublicApiUser(HttpUser):
    """Load tests for APIs available without authentication."""

    wait_time = between(1, 3)

    @task
    def register(self):
        register_load(self)

    # @task
    # def login(self):
    #     login_load(self)



class UserApiUser(HttpUser):
    """Load tests for authenticated user endpoints."""

    wait_time = between(1, 3)
    # def on_start(self):
    #     self.access_token = login_load(self)

    # @task
    # def profile(self):
    #     profile_load(self)

    def auth_headers(self):
        if not self.access_token:
            return {}
        return {"Authorization": f"Bearer {self.access_token}"}


class AdminApiUser(HttpUser):
    """Add authenticated admin API tasks here when those endpoints exist."""
    wait_time = between(1, 3)

    # def on_start(self):
    #         self.access_token = login_load(self)

    def auth_headers(self):
            if not self.access_token:
                return {}
            return {"Authorization": f"Bearer {self.access_token}"}