# dataJAR-recipes

Elegant and powerful Apple services for education and business. https://www.datajar.co.uk

## Creating Recipes with GitHub Copilot

This repository includes a [GitHub Copilot skill](.github/skills/autopkg-recipes/SKILL.md) that provides structured guidance for creating AutoPkg recipes. When you ask Copilot to create a download, munki, or pkg recipe, it automatically follows dataJAR conventions and linting standards.

### Prerequisites

- **VS Code** with the GitHub Copilot extension
- **AutoPkg** installed and configured
- **pre-commit** installed (`brew install pre-commit` then `pre-commit install`)
- Basic understanding of AutoPkg recipe structure

### Usage

1. Open this repository in VS Code
2. Open GitHub Copilot Chat
3. Ask Copilot to create a recipe, for example:
   - *"Create a download and munki recipe for AppName"*
   - *"Create a download recipe for AppName that uses Sparkle"*
   - *"Create a pkg recipe for AppName"*
4. Copilot will use the skill to generate recipes following repository conventions
5. Test with `autopkg run -v RecipeName.download`
6. Verify with `pre-commit run --files <recipe files>`

### What the Skill Covers

- **Download recipes** — Direct URL, Sparkle, GitHub Releases, web scraping, architecture-specific downloads
- **Munki recipes** — Complete pkginfo, installs array generation, version detection, pkg unpacking
- **Pkg recipes** — PkgCopier, AppPkgCreator, PkgRootCreator patterns
- **Linting standards** — Formatting, key ordering, naming conventions
- **Processor reference** — Core processors with MinimumVersion requirements

### Skill Reference Files

| File | Contents |
|------|----------|
| [SKILL.md](.github/skills/autopkg-recipes/SKILL.md) | Main entry point and recipe creation workflow |
| [download-recipe.md](.github/skills/autopkg-recipes/references/download-recipe.md) | Download recipe templates and patterns |
| [munki-recipe.md](.github/skills/autopkg-recipes/references/munki-recipe.md) | Munki recipe approaches and pkginfo keys |
| [pkg-recipe.md](.github/skills/autopkg-recipes/references/pkg-recipe.md) | Pkg recipe patterns |
| [processors.md](.github/skills/autopkg-recipes/references/processors.md) | Processor reference with version requirements |
| [architecture.md](.github/skills/autopkg-recipes/references/architecture.md) | Architecture-specific download patterns |
| [linter-standards.md](.github/skills/autopkg-recipes/references/linter-standards.md) | Formatting and linting rules |

## Related Resources

### AutoPkg Documentation
- [AutoPkg GitHub](https://github.com/autopkg/autopkg)
- [AutoPkg Wiki](https://github.com/autopkg/autopkg/wiki)
- [Processor Documentation](https://github.com/autopkg/autopkg/wiki/Processor-Locations)

### dataJAR Repositories
- [dataJAR-recipes](https://github.com/autopkg/dataJAR-recipes)
- [Shared Processors](https://github.com/autopkg/dataJAR-recipes/tree/master/Shared%20Processors)

### Community Resources
- [AutoPkg Google Group](https://groups.google.com/forum/#!forum/autopkg-discuss)
- [MacAdmins Slack #autopkg](https://macadmins.slack.com)
- [Noteworthy Processors](https://github.com/autopkg/autopkg/wiki/Noteworthy-Processors)
