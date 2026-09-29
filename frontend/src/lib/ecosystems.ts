import type { Ecosystem, EcosystemChoice } from "@/types/analysis"

/** An entry in the single-package ecosystem picker: a registry, or "Auto-detect". */
export interface EcosystemChoiceMeta {
  id: EcosystemChoice
  /** The registry, e.g. "PyPI". Mirrors the backend's app/domain/ecosystems.py. */
  label: string
  language: string
  /** Placeholder for the single-package input, in the registry's own spec syntax. */
  placeholder: string
  examples: string[]
}

export interface EcosystemMeta extends EcosystemChoiceMeta {
  id: Ecosystem
}

export const ECOSYSTEMS: EcosystemMeta[] = [
  {
    id: "npm",
    label: "npm",
    language: "JavaScript / TypeScript",
    placeholder: "express, @tanstack/react-query, moment@2.29.1",
    examples: ["express", "moment", "request", "zod"],
  },
  {
    id: "pypi",
    label: "PyPI",
    language: "Python",
    placeholder: "requests, django>=4.2, pycrypto",
    examples: ["requests", "django", "nose", "pycrypto"],
  },
  {
    id: "maven",
    label: "Maven Central",
    language: "Java / Kotlin",
    placeholder: "com.google.guava:guava, junit:junit:4.13.2",
    examples: ["com.google.guava:guava", "junit:junit", "org.slf4j:slf4j-api"],
  },
  {
    id: "nuget",
    label: "NuGet",
    language: "C# / .NET",
    placeholder: "Newtonsoft.Json, Serilog@3.1.1",
    examples: ["Newtonsoft.Json", "Serilog", "AutoMapper"],
  },
  {
    id: "go",
    label: "Go modules",
    language: "Go",
    placeholder: "github.com/gin-gonic/gin, github.com/pkg/errors",
    examples: ["github.com/gin-gonic/gin", "github.com/pkg/errors", "github.com/spf13/cobra"],
  },
  {
    id: "cargo",
    label: "crates.io",
    language: "Rust",
    placeholder: "serde, tokio@1.36",
    examples: ["serde", "tokio", "time"],
  },
  {
    id: "rubygems",
    label: "RubyGems",
    language: "Ruby",
    placeholder: "rails, devise, paperclip",
    examples: ["rails", "devise", "paperclip"],
  },
  {
    id: "packagist",
    label: "Packagist",
    language: "PHP",
    placeholder: "laravel/framework, guzzlehttp/guzzle",
    examples: ["laravel/framework", "guzzlehttp/guzzle", "fzaninotto/faker"],
  },
]

/** The "auto" choice: the backend detects the registry from the name's syntax and adoption. */
export const AUTO_ECOSYSTEM: EcosystemChoiceMeta = {
  id: "auto",
  label: "Auto-detect",
  language: "Any registry",
  placeholder: "express, requests, serde, org.slf4j:slf4j-api, laravel/framework",
  examples: ["requests", "serde", "rails", "Newtonsoft.Json", "github.com/gin-gonic/gin"],
}

export const ECOSYSTEM_BY_ID = Object.fromEntries(ECOSYSTEMS.map((meta) => [meta.id, meta])) as Record<
  Ecosystem,
  EcosystemMeta
>

/** The picker's options: auto-detect first, then every registry. */
export const ECOSYSTEM_CHOICES: EcosystemChoiceMeta[] = [AUTO_ECOSYSTEM, ...ECOSYSTEMS]

export const ECOSYSTEM_CHOICE_BY_ID = Object.fromEntries(ECOSYSTEM_CHOICES.map((meta) => [meta.id, meta])) as Record<
  EcosystemChoice,
  EcosystemChoiceMeta
>

/** One realistic dependency file per supported format, for the "Load example" menu. */
export const MANIFEST_EXAMPLES: { format: string; ecosystem: Ecosystem; content: string }[] = [
  {
    format: "package.json",
    ecosystem: "npm",
    content: JSON.stringify(
      {
        name: "legacy-api",
        dependencies: {
          express: "^4.17.1",
          request: "^2.88.2",
          moment: "^2.29.1",
          lodash: "^4.17.15",
          axios: "^0.21.1",
          zod: "^3.23.8",
        },
        devDependencies: { "node-sass": "^4.14.1", tslint: "^6.1.3", typescript: "^5.4.0" },
      },
      null,
      2,
    ),
  },
  {
    format: "requirements.txt",
    ecosystem: "pypi",
    content: "# web app\nDjango>=4.2,<5\nrequests==2.19.0\ncelery>=5.3\nnose>=1.3  # legacy test runner\npycrypto==2.6.1\n",
  },
  {
    format: "pyproject.toml",
    ecosystem: "pypi",
    content:
      '[project]\nname = "service"\ndependencies = [\n  "fastapi>=0.110",\n  "httpx>=0.27",\n  "pydantic==2.6.0",\n]\n\n[dependency-groups]\ndev = ["pytest>=8", "ruff"]\n',
  },
  {
    format: "pom.xml",
    ecosystem: "maven",
    content: `<project xmlns="http://maven.apache.org/POM/4.0.0">
  <properties>
    <jackson.version>2.9.8</jackson.version>
  </properties>
  <dependencies>
    <dependency>
      <groupId>com.fasterxml.jackson.core</groupId>
      <artifactId>jackson-databind</artifactId>
      <version>\${jackson.version}</version>
    </dependency>
    <dependency>
      <groupId>com.google.guava</groupId>
      <artifactId>guava</artifactId>
      <version>33.0.0-jre</version>
    </dependency>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.12</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>`,
  },
  {
    format: "build.gradle",
    ecosystem: "maven",
    content:
      "dependencies {\n    implementation 'org.springframework.boot:spring-boot-starter-web:3.2.0'\n    implementation 'com.squareup.okhttp3:okhttp:4.12.0'\n    testImplementation 'org.junit.jupiter:junit-jupiter:5.10.0'\n}\n",
  },
  {
    format: ".csproj",
    ecosystem: "nuget",
    content: `<Project Sdk="Microsoft.NET.Sdk">
  <ItemGroup>
    <PackageReference Include="Newtonsoft.Json" Version="12.0.1" />
    <PackageReference Include="Serilog" Version="3.1.1" />
    <PackageReference Include="AutoMapper" Version="13.0.1" />
  </ItemGroup>
</Project>`,
  },
  {
    format: "go.mod",
    ecosystem: "go",
    content:
      "module example.com/api\n\ngo 1.22\n\nrequire (\n\tgithub.com/gin-gonic/gin v1.6.0\n\tgithub.com/pkg/errors v0.9.1\n\tgithub.com/spf13/cobra v1.8.0\n\tgolang.org/x/net v0.20.0 // indirect\n)\n",
  },
  {
    format: "Cargo.toml",
    ecosystem: "cargo",
    content:
      '[package]\nname = "app"\nversion = "0.1.0"\n\n[dependencies]\nserde = { version = "1.0", features = ["derive"] }\ntokio = { version = "1.36", features = ["full"] }\ntime = "0.1.40"\n\n[dev-dependencies]\ncriterion = "0.5"\n',
  },
  {
    format: "Gemfile",
    ecosystem: "rubygems",
    content:
      'source "https://rubygems.org"\n\ngem "rails", "~> 7.1"\ngem "devise"\ngem "paperclip"\n\ngroup :development, :test do\n  gem "rspec-rails"\nend\n',
  },
  {
    format: "composer.json",
    ecosystem: "packagist",
    content: JSON.stringify(
      {
        require: { php: ">=8.1", "laravel/framework": "^10.0", "guzzlehttp/guzzle": "^7.8", "fzaninotto/faker": "^1.9" },
        "require-dev": { "phpunit/phpunit": "^10.5" },
      },
      null,
      2,
    ),
  },
]
