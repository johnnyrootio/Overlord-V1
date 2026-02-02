# Go Project Structure

Recommended project structure for Go projects.

## Standard Structure

```
project-name/
├── cmd/
│   └── project-name/
│       └── main.go
├── internal/
│   ├── server/
│   │   └── server.go
│   └── models/
│       └── user.go
├── pkg/
│   └── public/
│       └── api.go
├── api/
│   └── openapi.yaml
├── test/
│   └── fixtures/
├── .github/
│   └── workflows/
│       └── ci.yml
├── scripts/
│   └── check.sh
├── go.mod
├── go.sum
├── README.md
├── CLAUDE.md
└── .gitignore
```

## Directory Descriptions

- **`cmd/`**: Main applications (one per binary)
- **`internal/`**: Private application code (not importable)
- **`pkg/`**: Public library code (importable by others)
- **`api/`**: API definitions (OpenAPI, gRPC, etc.)
- **`test/`**: Test utilities and fixtures
- **`.github/workflows/`**: CI/CD configuration
- **`scripts/`**: Utility scripts (e.g., `check.sh`)

## Package Organization

### cmd/ Structure

```
cmd/
└── project-name/
    └── main.go          # Application entry point
```

### internal/ Structure

```
internal/
├── server/
│   └── server.go        # Server implementation
├── models/
│   └── user.go          # Data models
└── handlers/
    └── http.go          # HTTP handlers
```

### pkg/ Structure

```
pkg/
└── public/
    └── api.go           # Public API (importable)
```

## Test Organization

- Place tests in `*_test.go` files alongside source
- Use `test/` directory for test utilities and fixtures
- Mirror package structure in test files

## Module Structure

- Use Go modules (`go.mod`)
- Module path should match repository path
- Keep dependencies minimal
- Pin versions explicitly
