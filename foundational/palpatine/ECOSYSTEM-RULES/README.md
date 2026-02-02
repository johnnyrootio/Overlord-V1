# Ecosystem-Specific Rules and Guidelines

This directory contains ecosystem-specific configuration, cursor rules, and best practices for different programming languages and tech stacks.

## Purpose

Different programming ecosystems (Python, Go, TypeScript/Node.js, Rust, etc.) have different:
- Project structures
- Testing frameworks
- Linting and formatting tools
- Best practices
- Cursor rules and conventions

The Overlord should select and apply the appropriate ecosystem rules based on the project's tech stack.

## Structure

```
ECOSYSTEM-RULES/
├── README.md                    # This file
├── python/
│   ├── cursor-rules.md         # Cursor-specific rules for Python
│   ├── project-structure.md    # Recommended project structure
│   ├── best-practices.md        # Python best practices
│   └── check.sh-template       # Template for check.sh
├── go/
│   ├── cursor-rules.md
│   ├── project-structure.md
│   ├── best-practices.md
│   └── check.sh-template
├── typescript-node/
│   ├── cursor-rules.md
│   ├── project-structure.md
│   ├── best-practices.md
│   └── check.sh-template
└── rust/
    ├── cursor-rules.md
    ├── project-structure.md
    ├── best-practices.md
    └── check.sh-template
```

## How It Works

1. **During Phase 0 Planning**: Overlord asks about tech stack preference
2. **Ecosystem Selection**: Overlord selects appropriate ecosystem rules
3. **Application**: Overlord applies:
   - Cursor rules to `.cursorrules` or `CLAUDE.md`
   - Project structure recommendations
   - Best practices to documentation
   - `check.sh` template for the gate

## Tech Stack Selection Process

The Overlord should:
1. **Ask one question at a time** and wait for response
2. **Suggest ecosystems** when appropriate (e.g., "For a CLI tool, I recommend Go or Python. Which do you prefer?")
3. **Explain trade-offs** to help user make informed decision
4. **Apply ecosystem rules** once selected

## Available Ecosystems

- **Python**: Fast development, rich ecosystem, great for CLI tools, APIs, data processing
- **Go**: Fast compilation, excellent concurrency, great for services, CLI tools
- **TypeScript/Node.js**: Web applications, full-stack development, rich npm ecosystem
- **Rust**: Performance-critical, memory safety, systems programming
- **More to be added...**

## Contributing

To add a new ecosystem:
1. Create directory: `ECOSYSTEM-RULES/<ecosystem-name>/`
2. Add `cursor-rules.md`, `project-structure.md`, `best-practices.md`
3. Add `check.sh-template` with ecosystem-specific checks
4. Update this README
