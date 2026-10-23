"""Shared pieces of the login layer (kept free of Authlib so tests can use fakes)."""


class LoginError(RuntimeError):
    """The sign-in could not be completed. The message is safe to show."""
