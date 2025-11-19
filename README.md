<div align="center">

<img src="assets/github hero.png" alt="AgentField - Kubernetes, for AI Agents" width="100%" />

# The Control Plane for Autonomous Software

### **Deploy, Scale, Observe, and Prove.**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Go](https://img.shields.io/badge/go-1.21+-00ADD8.svg)](https://go.dev/)
[![Python](https://img.shields.io/badge/python-3.9+-3776AB.svg)](https://www.python.org/)
[![Deploy with Docker](https://img.shields.io/badge/deploy-docker-2496ED.svg)](https://docs.docker.com/)

**[📚 Documentation](https://agentfield.ai/docs)** • **[⚡ Quick Start](#-quick-start-in-60-seconds)** • **[🧠 The Paradigm Shift](#-why-agentfield)**

</div>

---

> **👋 Welcome Early Adopter!**
>
> You've discovered AgentField before our official launch. We're currently in private beta, building the infrastructure for the next generation of software. We'd love your feedback via [GitHub Issues](https://github.com/Agent-Field/agentfield/issues).

---

## 🚀 What is AgentField?

**AgentField is "Kubernetes for AI Agents."**

It is an open-source **Control Plane** that treats AI agents as first-class citizens. Instead of building fragile, monolithic scripts, AgentField lets you deploy agents as **independent microservices** that can discover each other, coordinate complex workflows, and scale infinitely—all with built-in observability and cryptographic trust.

### The "Aha!" Moment

Write standard Python (or Go). Get a production-grade distributed system automatically.

```python
from agentfield import Agent

# 1. Define an Agent (It's just a microservice)
app = Agent(node_id="researcher", model="gpt-4o")

# 2. Create a Skill (Deterministic code)
@app.skill()
def fetch_url(url: str) -> str:
    return requests.get(url).text

# 3. Create a Reasoner (AI-powered logic)
# This automatically becomes a REST API endpoint: POST /execute/researcher.summarize
@app.reasoner()
async def summarize(url: str) -> dict:
    content = fetch_url(url)
    # Native AI call with structured output
    return await app.ai(f"Summarize this content: {content}")

# 4. Run it
if __name__ == "__main__":
    app.run()
```

**What just happened?**
*   ✅ **Instant API:** Your function is now `POST /api/v1/execute/researcher.summarize`.
*   ✅ **Async & Durable:** It runs on a durable execution engine. If the server crashes, it resumes.
*   ✅ **Observable:** You get a full execution DAG, metrics, and logs automatically.
*   ✅ **Auditable:** Every step produced a cryptographically signed Verifiable Credential (VC).

---

## 🧠 Why AgentField?

**The Paradigm Shift: From "Chatbots" to "Systems"**

Most agent frameworks are designed for prototyping single-loop chatbots. But when you try to build **production systems** with multiple agents, you hit a wall.

| 🔴 The Old Way (Frameworks) | 💚 The AgentField Way (Infrastructure) |
| :--- | :--- |
| **Monolithic Deployment**<br>One team's bug crashes the whole system. | **Microservices Architecture**<br>Teams deploy agents independently. Zero coordination required. |
| **"Trust Me" Logs**<br>Text logs that can be edited or lost. | **Cryptographic Proof**<br>Every action is signed (W3C DIDs). You can prove *exactly* what the AI did in court. |
| **Black Box Execution**<br>Agent A calls Agent B... and context is lost. | **Distributed Tracing**<br>Visualize the entire DAG. See how data flows across the network. |
| **Fragile State**<br>Restart the server, lose the memory. | **Durable Execution**<br>Workflows can run for days. State is persisted and recoverable. |
| **Manual Plumbing**<br>Build your own queues, webhooks, and APIs. | **Batteries Included**<br>REST/gRPC, Async Queues, Webhooks, and Shared Memory out of the box. |

---

## ⚡ Quick Start in 60 Seconds

### 1. Install the CLI
```bash
curl -fsSL https://agentfield.ai/install.sh | bash
```

### 2. Initialize a New Agent
```bash
af init my-first-agent --defaults
cd my-first-agent
```

### 3. Run It
```bash
# Starts the Control Plane + Your Agent
af run
```

Your Control Plane is now live at **`http://localhost:8080`**.
Open the dashboard to see your agent in action!

---

## 🏗️ Architecture

AgentField is composed of a **Control Plane** (Go) and **Agent Nodes** (Python/Go/Any).

<div align="center">
<img src="assets/arch.png" alt="AgentField Architecture Diagram" width="80%" />
</div>

1.  **Control Plane:** The brain. Stateless, scalable. Handles routing, state, and verification.
2.  **Agent Nodes:** Your code. Lightweight microservices that connect to the plane.
3.  **Shared Memory Fabric:** Zero-config distributed state management.

---

## 💎 Key Features

### 🛡️ Identity & Trust (The Enterprise Killer Feature)
Every agent gets a **W3C Decentralized Identifier (DID)**. Every execution produces a **Verifiable Credential (VC)**.
*   **Audit Trails:** Export a cryptographic chain of custody for every decision.
*   **Policy Enforcement:** "Only agents signed by 'Finance Team' can access this data."

### 🧩 Durable Async Execution
Long-running tasks? No problem.
*   **No Timeouts:** Reasoners can run for hours or days.
*   **Webhooks:** Get notified via HMAC-signed webhooks when a job is done.
*   **Retries:** Automatic exponential backoff for failures.

### 🔌 Interoperability
*   **REST & gRPC:** Call agents from React, iOS, or `curl`.
*   **Language Agnostic:** Write agents in Python, Go, or any language with a gRPC client.

---

## 🎨 See It In Action

<div align="center">
<img src="assets/UI.png" alt="AgentField Dashboard" width="90%" />
<br/>
<i>Real-time Observability • Execution DAGs • Verifiable Credentials</i>
</div>

---

## 🤝 Community & Support

We are building the operating system for the agentic future. Join us!

*   **[📚 Documentation](https://agentfield.ai/docs)** - Deep dives and API references.
*   **[💡 GitHub Discussions](https://github.com/agentfield/agentfield/discussions)** - Feature requests and Q&A.
*   **[🐦 Twitter/X](https://x.com/agentfield_dev)** - Updates and announcements.

### Contributing
AgentField is Apache 2.0 licensed. We welcome contributions from the community. See [CONTRIBUTING.md](CONTRIBUTING.md) to get started.

---

<div align="center">

**Built by developers who got tired of duct-taping agents together.**

**[🌐 Website](https://agentfield.ai)**

</div>
