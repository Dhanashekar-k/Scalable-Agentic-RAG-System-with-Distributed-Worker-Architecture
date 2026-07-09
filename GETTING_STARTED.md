# Getting Started

This guide takes you from a clean checkout to a running instance of the Scalable RAG system — first on Docker Compose for local work, then on Kubernetes for a scaled deployment. If you just want to see it run, the [Local setup](#local-setup) section is enough.

## Prerequisites

You'll need Docker (20.10+) with Compose v2, Node.js 18+ for the frontends, and a [Groq API key](https://console.groq.com) for LLM inference. Python 3.10+ is only required if you plan to run the backend outside a container. A machine with 8 GB of free RAM is comfortable; the vector, graph, cache, and queue services are memory-hungry when run together.

## Local setup

Clone the repository and create your environment file from the template:

```bash
git clone https://github.com/Dhanashekar-k/Scalable-Agentic-RAG-System-with-Distributed-Worker-Architecture.git
cd Scalable-Agentic-RAG-System-with-Distributed-Worker-Architecture
cp docker/config/.env.example .env
```

Open `.env` and set at minimum your `GROQ_API_KEY`. Then bring up the full stack:

```bash
cd docker
docker-compose up -d
docker-compose ps        # wait until services report healthy
```

The first start pulls images and initializes the databases, so give it a minute or two. Once everything is healthy, the interfaces are:

| Service | URL |
|---|---|
| Ingestion UI | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Grafana | http://localhost:3000 (admin/admin) |
| Prometheus | http://localhost:9090 |

Confirm the backend is up and all dependencies connected:

```bash
curl http://localhost:8000/health
# {"status":"healthy","services":{"redis":true,"chromadb":true,"neo4j":true,"rabbitmq":true}}
```

## Your first query

Ingest a source, then ask a question against it:

```bash
# Ingest a GitHub repository
curl -X POST http://localhost:8000/ingest/url \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/expressjs/express"}'

# Ask a question once ingestion completes
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Why was body-parser split out of express?"}'
```

Simple factual questions take the fast path (direct vector retrieval, one LLM call). Multi-part or comparative questions are routed to the agentic pipeline, which plans several steps, fans them out to the worker pool, and evaluates the result before answering.

## Scaling with Kubernetes

For a horizontally scalable deployment, apply the manifests in `k8s/`. They provision the databases as StatefulSets, the API and workers as Deployments, and a HorizontalPodAutoscaler that grows the worker pool with queue depth.

```bash
kubectl apply -f k8s/
kubectl rollout status deployment/backend -n niyanta
kubectl get pods -n niyanta
```

> The manifests deploy into the `niyanta` namespace and reference container names such as `niyanta_redis`; adjust those identifiers in `k8s/` and `docker/` if you want a different naming scheme.

Workers scale on their own under load, but you can also set the count directly:

```bash
kubectl scale deployment/worker --replicas=5 -n niyanta
kubectl get hpa -n niyanta          # inspect autoscaling state
```

## Observability

Metrics are exposed on the backend's `/metrics` endpoint and scraped by Prometheus; Grafana ships with a pre-provisioned overview dashboard, and Loki aggregates container logs. See [docker/MONITORING.md](./docker/MONITORING.md) for the full stack and the queries behind each panel.

## Troubleshooting

If containers restart in a loop, check `docker-compose logs <service>` first — the usual causes are a missing `GROQ_API_KEY` or insufficient memory. "Connection refused" right after startup usually means a dependency is still initializing; the databases can take 30–60 seconds, so re-check `docker-compose ps` before assuming a failure. If a port is already bound on your machine, find the holder with `lsof -i :8000` and stop it or remap the port in `docker/docker-compose.yml`. To wipe all state and start clean, run `docker-compose down -v` (the `-v` also removes the data volumes).

## Where to go next

The [architecture overview](./docs/AGENTIC_ARCHITECTURE.md) explains how the planner, orchestrator, and workers fit together. The [deployment guide](./docs/DEPLOYMENT.md) covers production concerns, and [backend documentation](./docs/BACKEND.md) details the API surface and retrieval internals.
