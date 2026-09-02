# Hybrid cloud proof of concept

This is a deliberately small, **opt-in** architecture sketch:

```text
AWS Step Functions → GCP Cloud Function tools
        │                    │
        └──────────────→ Azure Cosmos DB state
                             │
                     GCP Vertex AI Vector Search
```

The modules show provider boundaries and least-privilege inputs without making a
cloud call. `envs/dev` defaults `enable_resources` to `false`; review provider
credentials, networking, data residency, and costs before enabling it. Run
`terraform fmt -check` locally, then use `terraform plan` only in an explicitly
configured, non-production account. Never commit a state file or credentials.

The POC intentionally passes URLs and resource IDs between modules as outputs rather
than sharing credentials. The AWS orchestrator receives only the tool endpoint and
the state endpoint; each provider's identity remains in its own module.
