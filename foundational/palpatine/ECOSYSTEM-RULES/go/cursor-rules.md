# Go Cursor Rules

These rules should be added to `.cursorrules` or `CLAUDE.md` for Go projects.

## Go-Specific Rules

### Code Style

- Follow `gofmt` formatting (run automatically)
- Follow `golint` and `golangci-lint` recommendations
- Use `go vet` for static analysis
- Maximum line length: 100 characters (soft limit)

### Project Structure

- Use standard Go project layout
- `cmd/` for main applications
- `internal/` for private packages
- `pkg/` for public packages
- `api/` for API definitions
- `test/` for test utilities

### Naming Conventions

- Use short, clear names
- Exported names start with capital letter
- Unexported names start with lowercase
- Use `NewXxx` for constructors
- Use interfaces for abstractions

### Error Handling

- Always check errors
- Return errors, don't ignore them
- Use `fmt.Errorf` with `%w` for error wrapping
- Create custom error types when appropriate
- Use `errors.Is` and `errors.As` for error checking

### Testing

- Use `testing` package (standard library)
- Place tests in `*_test.go` files
- Use table-driven tests for multiple cases
- Use subtests for complex test scenarios
- Aim for high test coverage

### Dependencies

- Use Go modules (`go.mod`)
- Pin versions explicitly
- Use `go get` for dependencies
- Run `go mod tidy` regularly
- Minimize dependencies

### Concurrency

- Use goroutines for concurrent operations
- Use channels for communication
- Use `context.Context` for cancellation
- Avoid goroutine leaks
- Use `sync` package appropriately

### Documentation

- Write package-level documentation
- Document all exported functions and types
- Use examples in `example_test.go`
- Keep documentation up to date

### Performance

- Profile before optimizing
- Use `pprof` for profiling
- Consider memory allocations
- Use appropriate data structures
- Benchmark critical paths
