# Development Port Management

## Purpose

AgentCore development environments must avoid port conflicts. Many tools use common default ports. If AgentCore services also use those defaults, developers will hit conflicts with databases, dashboards, local servers, IDE helpers, model runtimes, and other projects.

The architecture must therefore require project-scoped, configurable, non-default development ports.

## Core Rule

Default vendor ports must be changed for AgentCore development unless the developer explicitly overrides them.

The system must not assume that common default ports are available.

## Why Default Ports Must Change in Development

Common local defaults are frequently occupied by other tools:

- API frameworks often use common web ports.
- PostgreSQL, Redis, Neo4j, and other databases have well-known defaults.
- Dashboards and admin UIs often collide.
- Local LLM runtimes and vector services may already be running.
- Multiple projects may run at the same time.

Using default ports makes the development experience fragile and makes failures look like application bugs when they are actually environment conflicts.

## Required Behavior

### 1. Ports Must Be Configurable

Every service port must come from configuration:

- environment variable,
- local development config file,
- tenant/project runtime profile,
- Docker Compose override,
- orchestration configuration.

Ports must not be hard-coded in source code, scripts, tests, or documentation examples.

### 2. Development Ports Must Be Project-Scoped

AgentCore should define a development port profile that is unlikely to conflict with common defaults. The profile should use a dedicated range for the project.

Recommended pattern:

```text
AGENTCORE_DEV_PORT_BASE=32xxx
service_port = AGENTCORE_DEV_PORT_BASE + service_offset
```

The exact base value should be configurable per developer machine.

### 3. Startup Must Check Port Availability

Before starting services, the development launcher should check whether required ports are available.

If a port is occupied, startup should fail with a clear error:

```text
Port 32xxx is already in use by another process.
Change AGENTCORE_DEV_PORT_BASE or override AGENTCORE_<SERVICE>_PORT.
```

### 4. Services Must Log Their Bound Ports

Every service should log the host and port it binds to at startup. This helps developers identify incorrect configuration quickly.

### 5. Documentation Examples Must Use Non-Default Ports

Documentation should not teach developers to use common defaults for development. Examples should use AgentCore-specific development ports and explain how to override them.

### 6. Tests Must Not Depend on Fixed Ports

Automated tests should use ephemeral ports or test-specific allocated ports. Fixed ports in tests create flaky behavior on shared machines and CI runners.

## Recommended Development Port Profile

The following is a documentation profile, not a hard-coded requirement. Values should be changed if they conflict on a developer machine.

```text
AGENTCORE_API_PORT=32100
AGENTCORE_ADMIN_PORT=32101
AGENTCORE_CORE_DATA_PORT=32110
AGENTCORE_MEMORY_PORT=32120
AGENTCORE_DOCS_SYNC_PORT=32130
AGENTCORE_CODE_GRAPH_PORT=32140
AGENTCORE_RULE_ENGINE_PORT=32150
AGENTCORE_BROKER_PORT=32160
AGENTCORE_ADAPTER_PORT=32170
AGENTCORE_WORKER_METRICS_PORT=32180
AGENTCORE_NEO4J_BOLT_PORT=32287
AGENTCORE_NEO4J_HTTP_PORT=32474
AGENTCORE_REDIS_PORT=32379
AGENTCORE_OBJECT_STORE_PORT=32390
```

These values intentionally avoid common defaults. They are still examples and must remain overrideable.

## Environment Variable Naming

Use explicit names:

```text
AGENTCORE_API_PORT
AGENTCORE_ADMIN_PORT
AGENTCORE_NEO4J_BOLT_PORT
AGENTCORE_NEO4J_HTTP_PORT
AGENTCORE_BROKER_PORT
AGENTCORE_REDIS_PORT
```

Avoid generic names such as `PORT` in multi-service development because they become ambiguous.

## Port Allocation Algorithm

```text
load development port profile
apply local overrides
for each service:
    validate port is numeric and in allowed range
    check port availability
    if unavailable:
        report owning process when possible
        suggest next available project-scoped port
        fail startup unless auto-reassign is explicitly enabled
write resolved port map to runtime summary
start services with resolved ports
```

## Auto-Reassignment Policy

Automatic reassignment can be useful, but it must be explicit. Silent reassignment makes debugging hard because services may start on unexpected ports.

Allowed behavior:

- explicit `AGENTCORE_AUTO_PORT=1` enables automatic reassignment,
- runtime summary prints final assigned ports,
- generated local `.env` or runtime file records resolved ports,
- dependent services receive updated ports through service discovery or config injection.

Disallowed behavior:

- silently choosing random ports without logging,
- hard-coding fallback ports,
- changing ports in one service without updating dependents,
- documenting default vendor ports as AgentCore development defaults.

## CI and Staging Behavior

CI should not rely on developer port profiles. It should use isolated network namespaces, ephemeral ports, or orchestration-level service discovery.

Staging and production should use service discovery rather than manually assigned local ports, except for explicitly exposed ingress endpoints.

## Acceptance Criteria

- No development service requires a hard-coded port.
- Common vendor defaults are not used as AgentCore development defaults.
- Startup validates port availability before binding.
- Port conflicts produce clear errors and remediation guidance.
- Tests use ephemeral or test-allocated ports.
- Documentation examples use AgentCore-specific non-default ports.
- Developers can override every service port without changing code.
