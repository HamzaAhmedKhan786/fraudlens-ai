# ADR 0001: Begin with a modular monolith

Status: accepted

The MVP uses one FastAPI control plane with explicit domain and port boundaries. Kafka is used for
durable asynchronous work, not as a substitute for internal architecture. This reduces deployment
and consistency overhead while preserving a clean path to extract high-cost workers.

