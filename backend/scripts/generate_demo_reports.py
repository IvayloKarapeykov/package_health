"""Regenerates the example reports shown on the landing page.

Run from backend/ with an OpenRouter key in .env, so the reports include Jev's verdicts and the
LLM's explanations:

    .venv/bin/python -m scripts.generate_demo_reports
"""

import asyncio
import json
import sys
from pathlib import Path

from app.container import RunnerFactory
from app.core.config import get_settings
from app.core.http import create_http_client
from app.domain.credentials import Credentials
from app.domain.requests import ManifestRequest, PackageRequest

OUTPUT_DIR = Path(__file__).resolve().parents[2] / "frontend" / "src" / "demo"

PACKAGE_JSON = """{
  "name": "storefront",
  "dependencies": {
    "express": "^4.19.2",
    "lodash": "^4.17.21",
    "moment": "^2.29.4",
    "request": "^2.88.2"
  },
  "devDependencies": {
    "tslint": "^6.1.3"
  }
}
"""

REQUIREMENTS_TXT = """requests==2.31.0
flask>=3.0
nose==1.3.7
pycrypto==2.6.1
"""

DEMOS: dict[str, PackageRequest | ManifestRequest] = {
    "package-json": ManifestRequest(content=PACKAGE_JSON, filename="package.json"),
    "requirements-txt": ManifestRequest(content=REQUIREMENTS_TXT, filename="requirements.txt"),
    "log4j": PackageRequest(package="org.apache.logging.log4j:log4j-core:2.14.1", ecosystem="maven"),
}


async def main() -> None:
    settings = get_settings()
    if settings.openrouter_api_key is None:
        sys.exit("Set OPENROUTER_API_KEY in .env: the demos should show AI verdicts and explanations.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    async with create_http_client(settings.http_timeout_seconds) as http:
        runner = RunnerFactory(settings, http)(Credentials())
        for name, request in DEMOS.items():
            report = await runner.run(request)
            demo = {"request": request.model_dump(mode="json"), "report": report.model_dump(mode="json")}
            (OUTPUT_DIR / f"{name}.json").write_text(json.dumps(demo, indent=2, ensure_ascii=False) + "\n")
            print(f"{name}: {report.overall_verdict.value}, {len(report.assessments)} packages")


if __name__ == "__main__":
    asyncio.run(main())
