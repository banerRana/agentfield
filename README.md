<div align="center">

<img src="assets/github.png" alt="AgentField - Kubernetes, for AI Agents" width="100%" />

### Kubernetes for AI Agents — **Deploy, Scale, Observe, and Prove**

Open-source (Apache-2.0) **control plane** that runs AI agents like microservices.
Every agent gets **REST/gRPC APIs**, **async execution & webhooks**, **built-in observability**, and **cryptographic identity & audit**.


[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Go](https://img.shields.io/badge/go-1.21+-00ADD8.svg)](https://go.dev/)
[![Python](https://img.shields.io/badge/python-3.9+-3776AB.svg)](https://www.python.org/)
[![Deploy with Docker](https://img.shields.io/badge/deploy-docker-2496ED.svg)](https://docs.docker.com/)

**[📚 Docs](https://agentfield.ai/docs)** • **[⚡ Quickstart](#quickstart-in-60-seconds)** • **[🧠 Why AgentField](#why-agentfield)**

</div>

---

## TL;DR

- **Write agents in Python/Go** (or any language via REST/gRPC)
- **Deploy independently** like microservices—zero coordination between teams
- **Get production infrastructure automatically**: IAM, REST APIs, streaming, async queues, observability, cryptographic audit trails
- **Run anywhere**: local dev, Docker, Kubernetes, cloud

```bash
curl -fsSL https://agentfield.ai/install.sh | bash && af init my-agents
```
---

## 🚀 Try AgentField in 2 Minutes

### Option 1: Local Install

```bash
# macOS/Linux - install CLI
curl -fsSL https://agentfield.ai/install.sh | bash

# Start control plane + create your first agent
af init my-agents && cd my-agents
af run
```

### Option 2: Docker Compose

```bash
git clone https://github.com/agentfield/agentfield
cd agentfield && docker compose up
```

Your control plane is running at `http://localhost:8080`

**[📚 Full quickstart guide →](https://agentfield.ai/docs/quick-start)**

```python
from agentfield import Agent

# Create an agent
app = Agent(node_id="greeting-agent",
            model="openrouter/meta-llama/llama-4-maverick")

# Decorate a function—becomes a REST endpoint automatically
@app.reasoner()
async def say_hello(name: str) -> dict:

    message = await app.ai(f"Generate a personalized greeting for {name}")

    return {"greeting": message}
```

**Deploy:**
```bash
export OPENROUTER_API_KEY="sk-..."
af run
```

**Call from anywhere** (REST API auto-generated):
```bash
curl -X POST http://localhost:8080/api/v1/execute/greeting-agent.say_hello \
  -H "Content-Type: application/json" \
  -d '{"input": {"name": "Alice"}}'
```

**You automatically get:**
- ✅ REST API at `/execute/greeting-agent.say_hello` (OpenAPI spec at `/openapi.yaml`)
- ✅ Async execution: `/execute/async/...` with webhook callbacks (HMAC-signed)
- ✅ Prometheus metrics: `/metrics`
- ✅ Workflow Observability


**[📚 Docs](https://agentfield.ai/docs)** • **[⚡ More examples](https://github.com/agentfield/agentfield-examples)**

---

## Why AgentField?

Agent frameworks are great for **prototypes**. AgentField builds agents **and** runs them at production scale.

### What Hurts Today → What AgentField Does Automatically

| 🔴 **Without AgentField**                                      | 🟢 **With AgentField**                                                                      |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **Monolithic deploys** — one team's change redeploys everyone | **Independent deploys** — each agent ships on its own schedule; control plane coordinates  |
| **DIY orchestration** — queues, async, webhooks, state        | **Built-in orchestration** — durable queues, async + webhooks, shared memory scopes        |
| **No observability** — grep logs across services              | **Auto-observability** — workflow DAGs, Prometheus metrics, structured logs                |
| **No identity/audit** — logs can be edited                    | **Cryptographic proof** — DIDs per agent, Verifiable Credentials per execution             |
| **Fragile communication** — discovery/routing by hand         | **Auto-discovery & context propagation** — `await agent.call("other-agent.fn")`, zero glue |
| **Ad-hoc APIs** — custom wrappers for frontends               | **REST/OpenAPI by default** — every reasoner is an endpoint (gRPC optional)                |

```
Traditional Frameworks = Flask (single app)
AgentField = Kubernetes + Auth0 for AI (distributed infrastructure + identity)
```

> **AgentField isn't a framework you extend with infrastructure. It IS the infrastructure.**

Bring your own model/tooling; AgentField handles runtime, scale, and proof.

---

What You Get Out-of-the-Box

🧩 Scale Infrastructure — deploy like microservices
	•	Durable queues, async webhooks, event streaming
	•	Auto-discovery & cross-agent calls; context propagation
	•	Horizontal scaling & many more..!

🔐 Trust & Governance — cryptographic proof for every decision
	•	W3C IDs & Verifiable Credentials
	•	Tamper-proof audit trails; runtime policy enforcement
	•	Offline verification for auditors

🛰 Production Hardening — observability & reliability built in
	•	Auto-generated workflow DAGs
	•	Prometheus metrics, structured logs
	•	Graceful shutdowns, retries, zero-config memory

**Learn more:** [Features](https://agentfield.ai/docs/features) • [Identity & Trust](https://agentfield.ai/docs/why-agentfield/vs-agent-frameworks)

---

## 🏗️ Architecture

<div align="center">
<img src="assets/arch.png" alt="AgentField Architecture Diagram" width="80%" />
</div>

---

| Layer         | What It Does                                                  |
| ------------- | ------------------------------------------------------------- |
| Control Plane | Stateless Go service; routes, observes, verifies, scales      |
| Agent Nodes   | Your independent agent microservices (Python/Go/REST/gRPC)    |
| Interfaces    | Backends via REST; frontends & external APIs via webhooks/SSE |

Each agent is a microservice. Teams deploy independently; the control plane makes them behave as one coherent system.

**More:** [Architecture](https://agentfield.ai/docs/architecture) • [API Reference](https://agentfield.ai/docs/api)

---

## Real-Time & Async

- **Unified API:** `POST /api/v1/execute/{agent.reasoner}`
- **Async runs:** `/execute/async/...` + signed webhooks
- **Live streams:** Server-Sent Events (SSE) for real-time output
- **Auto retries, backpressure, dead-letter queues**

**Docs:** [API Reference](https://agentfield.ai/docs/api) • [Observability](https://agentfield.ai/docs/observability)

---

## Identity & Audit (opt-in per agent)

- DIDs auto-issued for agents (`did:web` / `did:key`)
- Verifiable Credentials (W3C JSON-LD) for each execution
- Input/output hashing for proof integrity
- Offline verification for auditors (`af vc verify audit.json`)

**Docs:** [Identity & Trust](https://agentfield.ai/docs/why-agentfield/vs-agent-frameworks)

---

## Installation

### macOS / Linux

```bash
curl -fsSL https://agentfield.ai/get | bash
agentfield --version
```

### Docker Compose

```bash
git clone https://github.com/Agent-Field/agentfield
cd agentfield && docker compose up
```

**Full guides:** [Installation](https://agentfield.ai/docs/installation) • [Deployment](https://agentfield.ai/docs/deployment)

---

## When to Use (and When Not)

### ✅ Use AgentField If:

- You're building **multi-agent systems** that need to coordinate
- You need **independent deployment**—multiple teams, different schedules
- You need **production infrastructure**: REST APIs, async queues, observability, health checks
- You need **compliance/audit trails** (finance, healthcare, legal)
- You want to **call agents from frontends** (React, mobile) without custom wrappers
- You're scaling to **multiple environments** (dev, staging, prod) and need consistency

### ❌ Start with a Framework If:

- You're building a **single-agent chatbot** that will never scale beyond one service
- You don't need REST APIs, observability, or multi-agent coordination
- You're prototyping and don't plan to deploy to production

### The Bottom Line

**Frameworks = Build agents** (perfect for learning)
**AgentField = Build and run agents at any scale** (perfect from prototype to production)

You can start with AgentField and skip migration pain later. Or start with a framework and migrate when you hit the pain points above.

---

## Community

We're building AgentField in the open. Join us:

- **[📚 Documentation](https://agentfield.ai/docs)** — Guides, API reference, examples
- **[💡 GitHub Discussions](https://github.com/agentfield/agentfield/discussions)** — Feature requests, Q&A
- **[🐦 Twitter/X](https://x.com/agentfield_dev)** — Updates and announcements

### Contributing

Apache 2.0 licensed. Built by developers like you.

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup and guidelines.


---

## 📖 Resources

- **[📚 Documentation](https://agentfield.ai/docs)** — Complete guides and API reference
- **[⚡ Quick Start Tutorial](https://agentfield.ai/docs/quick-start)** — Build your first agent in 5 minutes
- **[🏗️ Architecture Deep Dive](https://agentfield.ai/docs/architecture)** — How AgentField works under the hood
- **[📦 Examples Repository](https://github.com/agentfield/agentfield-examples)** — Production-ready agent templates
- **[📝 Blog](https://agentfield.ai/blog)** — Tutorials, case studies, best practices

---

<div align="center">

### ⭐ Star us to follow development

**Built by developers who got tired of duct-taping agents together**

**Join the future of autonomous software**

**[🌐 Website](https://agentfield.ai) • [📚 Docs](https://agentfield.ai/docs) • [🐦 Twitter](https://x.com/agentfield_dev)**

**License:** [Apache 2.0](LICENSE)

---

*We believe autonomous software needs infrastructure that respects what makes it different—agents that reason, decide, and coordinate—while providing the same operational excellence that made traditional software successful.*

</div>
