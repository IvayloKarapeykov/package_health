"""Manifest parsers and format detection, one realistic file per format."""

import json

import pytest

from app.domain.errors import InvalidInputError
from app.manifests.registry import find_parser

PACKAGE_JSON = json.dumps(
    {
        "dependencies": {"react": "^18.2.0", "local": "file:../local", "fork": "user/repo", "sw": "npm:string-width@^4"},
        "devDependencies": {"vitest": "^1.0.0", "react": "^18.2.0"},
        "peerDependencies": {"react-dom": "^18"},
    }
)
PACKAGE_LOCK = json.dumps(
    {
        "lockfileVersion": 3,
        "packages": {
            "": {"dependencies": {"express": "^4.17.1"}, "devDependencies": {"jest": "^29"}},
            "node_modules/express": {"version": "4.18.2"},
            "node_modules/jest": {"version": "29.7.0"},
        },
    }
)
PNPM_LOCK = """lockfileVersion: '9.0'
importers:
  .:
    dependencies:
      react:
        specifier: ^18.2.0
        version: 18.2.0
      react-dom:
        specifier: ^18.2.0
        version: 18.2.0(react@18.2.0)
    devDependencies:
      typescript:
        specifier: ^5.4.0
        version: 5.4.5
"""
REQUIREMENTS = """# app deps
requests==2.31.0
Django>=4.2,<5  # web
uvicorn[standard]>=0.23 ; python_version >= "3.8"
-r dev.txt
git+https://github.com/acme/lib.git
pkg @ https://example.com/pkg.whl
"""
PYPROJECT = """
[project]
name = "app"
dependencies = ["httpx>=0.27", "pydantic[email]==2.6.0"]
[project.optional-dependencies]
dev = ["pytest>=8"]
postgres = ["psycopg>=3"]
[tool.poetry.dependencies]
python = "^3.11"
rich = "^13"
mylib = { path = "../mylib" }
"""
PIPFILE = """
[[source]]
url = "https://pypi.org/simple"
[packages]
flask = "*"
sqlalchemy = { version = ">=2.0" }
[dev-packages]
black = "==24.1.0"
"""
CARGO = """
[package]
name = "app"
version = "0.1.0"
[dependencies]
serde = { version = "1.0", features = ["derive"] }
tokio = "1.36"
json = { package = "serde_json", version = "1" }
local = { path = "../local" }
[dev-dependencies]
criterion = "0.5"
"""
GO_MOD = """module example.com/app

go 1.22

require github.com/pkg/errors v0.9.1

require (
\tgithub.com/gin-gonic/gin v1.9.1
\tgolang.org/x/net v0.20.0 // indirect
)
"""
POM = """<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <version>1.0.0</version>
  <properties><jackson.version>2.17.0</jackson.version></properties>
  <dependencies>
    <dependency><groupId>com.fasterxml.jackson.core</groupId><artifactId>jackson-databind</artifactId><version>${jackson.version}</version></dependency>
    <dependency><groupId>junit</groupId><artifactId>junit</artifactId><version>4.13.2</version><scope>test</scope></dependency>
  </dependencies>
  <build><plugins><plugin><artifactId>maven-compiler-plugin</artifactId></plugin></plugins></build>
</project>"""
GRADLE = """
plugins { id 'java' }
dependencies {
    implementation 'com.google.guava:guava:33.0.0-jre'
    implementation("org.slf4j:slf4j-api:2.0.9")
    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'
}
"""
GEMFILE = """source "https://rubygems.org"
ruby "3.3.0"
gem "rails", "~> 7.1.0"
gem "pg", ">= 1.1"
gem "mylib", path: "../mylib"
gem "rubocop", require: false, group: :development
group :development, :test do
  gem "rspec-rails"
end
"""
COMPOSER = json.dumps(
    {"require": {"php": ">=8.1", "ext-json": "*", "laravel/framework": "^10.0"}, "require-dev": {"phpunit/phpunit": "^10"}}
)
CSPROJ = """<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="13.0.3" />
    <PackageReference Include="Serilog"><Version>3.1.1</Version></PackageReference>
    <PackageReference Include="Microsoft.CodeAnalysis.NetAnalyzers" Version="8.0.0" PrivateAssets="all" />
    <PackageReference Update="Serilog" Version="3.1.2" />
  </ItemGroup>
</Project>"""


def entries(text: str, filename: str | None = None, include_dev: bool = True) -> tuple[str, str, list, list]:
    parser = find_parser(text, filename)
    parsed = parser.parse(text, include_dev=include_dev)
    return (
        parser.format,
        parser.ecosystem,
        [(d.name, d.requested, d.kind) for d in parsed.dependencies],
        [s.name for s in parsed.skipped],
    )


@pytest.mark.parametrize(
    ("text", "format", "ecosystem", "dependencies", "skipped"),
    [
        (
            PACKAGE_JSON,
            "package.json",
            "npm",
            [("react", "^18.2.0", "prod"), ("string-width", "^4", "prod"), ("react-dom", "^18", "peer"),
             ("vitest", "^1.0.0", "dev"), ("react", "^18.2.0", "dev")],
            ["local", "fork"],
        ),
        (PACKAGE_LOCK, "package-lock.json", "npm", [("express", "4.18.2", "prod"), ("jest", "29.7.0", "dev")], []),
        (
            PNPM_LOCK,
            "pnpm-lock.yaml",
            "npm",
            [("react", "18.2.0", "prod"), ("react-dom", "18.2.0", "prod"), ("typescript", "5.4.5", "dev")],
            [],
        ),
        (
            REQUIREMENTS,
            "requirements.txt",
            "pypi",
            [("requests", "==2.31.0", "prod"), ("Django", ">=4.2,<5", "prod"), ("uvicorn", ">=0.23", "prod")],
            ["git+https://github.com/acme/lib.git", "pkg"],
        ),
        (
            PYPROJECT,
            "pyproject.toml",
            "pypi",
            [("httpx", ">=0.27", "prod"), ("pydantic", "==2.6.0", "prod"), ("pytest", ">=8", "dev"),
             ("psycopg", ">=3", "optional"), ("rich", "^13", "prod")],
            ["mylib"],
        ),
        (PIPFILE, "Pipfile", "pypi", [("flask", None, "prod"), ("sqlalchemy", ">=2.0", "prod"), ("black", "==24.1.0", "dev")], []),
        (
            CARGO,
            "Cargo.toml",
            "cargo",
            [("serde", "1.0", "prod"), ("tokio", "1.36", "prod"), ("serde_json", "1", "prod"), ("criterion", "0.5", "dev")],
            ["local"],
        ),
        (GO_MOD, "go.mod", "go", [("github.com/pkg/errors", "v0.9.1", "prod"), ("github.com/gin-gonic/gin", "v1.9.1", "prod")], []),
        (
            POM,
            "pom.xml",
            "maven",
            [("com.fasterxml.jackson.core:jackson-databind", "2.17.0", "prod"), ("junit:junit", "4.13.2", "dev")],
            [],
        ),
        (
            GRADLE,
            "build.gradle",
            "maven",
            [("com.google.guava:guava", "33.0.0-jre", "prod"), ("org.slf4j:slf4j-api", "2.0.9", "prod"),
             ("org.junit.jupiter:junit-jupiter", "5.10.0", "dev")],
            [],
        ),
        (
            GEMFILE,
            "Gemfile",
            "rubygems",
            [("rails", "~> 7.1.0", "prod"), ("pg", ">= 1.1", "prod"), ("rubocop", None, "dev"), ("rspec-rails", None, "dev")],
            ["mylib"],
        ),
        (COMPOSER, "composer.json", "packagist", [("laravel/framework", "^10.0", "prod"), ("phpunit/phpunit", "^10", "dev")], []),
        (
            CSPROJ,
            ".csproj",
            "nuget",
            [("Newtonsoft.Json", "13.0.3", "prod"), ("Serilog", "3.1.1", "prod"),
             ("Microsoft.CodeAnalysis.NetAnalyzers", "8.0.0", "dev")],
            [],
        ),
    ],
)
def test_format_is_detected_from_content_and_parsed(text, format, ecosystem, dependencies, skipped) -> None:
    assert entries(text) == (format, ecosystem, dependencies, skipped)


def test_dev_dependencies_can_be_excluded() -> None:
    _, _, dependencies, _ = entries(GEMFILE, include_dev=False)
    assert [name for name, _, _ in dependencies] == ["rails", "pg"]


@pytest.mark.parametrize(
    ("filename", "format"),
    [("backend/requirements-dev.txt", "requirements.txt"), ("App.csproj", ".csproj"), ("build.gradle.kts", "build.gradle")],
)
def test_file_name_picks_the_parser(filename: str, format: str) -> None:
    assert find_parser("", filename).format == format


@pytest.mark.parametrize(
    ("text", "filename"),
    [("just some prose, not a manifest!", None), ("{}", "notes.md"), ("{oops", "package.json")],
)
def test_unusable_input_is_rejected(text: str, filename: str | None) -> None:
    with pytest.raises(InvalidInputError):
        find_parser(text, filename).parse(text, include_dev=True)
