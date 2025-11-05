# Brain Go SDK

The Brain Go SDK provides idiomatic Go bindings for interacting with the Brain control plane.

## Installation

```bash
go get github.com/your-org/brain/sdk/go
```

## Quick Start

```go
package main

import (
    "context"
    "log"

    brainagent "github.com/your-org/brain/sdk/go/agent"
)

func main() {
    agent, err := brainagent.New(brainagent.Config{
        NodeID:   "example-agent",
        BrainURL: "http://localhost:8080",
    })
    if err != nil {
        log.Fatal(err)
    }

    agent.RegisterSkill("health", func(ctx context.Context, _ map[string]any) (any, error) {
        return map[string]any{"status": "ok"}, nil
    })

    if err := agent.Run(context.Background()); err != nil {
        log.Fatal(err)
    }
}
```

## Modules

- `agent`: Build Brain-compatible agents and register reasoners/skills.
- `client`: Low-level HTTP client for the Brain control plane.
- `types`: Shared data structures and contracts.
- `ai`: Helpers for interacting with AI providers via the control plane.

## Testing

```bash
go test ./...
```

## License

Distributed under the Apache 2.0 License. See the repository root for full details.
