from dataclasses import dataclass

from pydantic import SecretStr


@dataclass(frozen=True)
class Credentials:
    github_token: SecretStr | None = None
    openrouter_api_key: SecretStr | None = None

    @classmethod
    def from_raw(cls, github_token: str | None = None, openrouter_api_key: str | None = None) -> "Credentials":
        """Blank values count as absent."""
        return cls(github_token=_secret(github_token), openrouter_api_key=_secret(openrouter_api_key))

    @property
    def empty(self) -> bool:
        return self.github_token is None and self.openrouter_api_key is None

    def or_defaults(self, github_token: SecretStr | None, openrouter_api_key: SecretStr | None) -> "Credentials":
        """Falls back to the given server keys where absent."""
        return Credentials(
            github_token=self.github_token or github_token,
            openrouter_api_key=self.openrouter_api_key or openrouter_api_key,
        )


def _secret(value: str | None) -> SecretStr | None:
    value = (value or "").strip()
    return SecretStr(value) if value else None
