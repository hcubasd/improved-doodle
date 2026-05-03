# improved-doodle

RD Station CRM worker for the **modest-galois** project. Fetches the full CRM graph from the RD Station v2 API, builds the domain model via **fluffy-waddle**, and writes it to the sales schema in Postgres.

The sync strategy is a full replace every run: nuke the sales schema, repopulate from scratch. At ~2000 records this is faster than diffing.

## Fetch flow

```mermaid
flowchart LR
    S([start])

    S --> U[fetch users page]
    S --> T[fetch teams page]
    S --> PL[fetch pipelines page]
    S --> CA[fetch campaigns page]
    S --> LR[fetch lost_reasons page]
    S --> SO[fetch sources page]
    S --> SE[fetch segments page]
    S --> OR[fetch organizations page]
    S --> CO[fetch contacts page]
    S --> TA[fetch tasks page]
    S --> PR[fetch products page]

    U --> PU{more pages?}
    PU -- yes --> U
    PU -- no --> E([end])

    T --> PT{more pages?}
    PT -- yes --> T
    PT -- no --> E

    PL --> PPL{more pages?}
    PPL -- yes --> PL
    PPL -- yes --> STG[fetch stages page\nfor each pipeline in batch]
    PPL -- no --> STG
    STG --> PSTG{more pages?}
    PSTG -- yes --> STG
    PSTG -- no --> E

    CA --> PCA{more pages?}
    PCA -- yes --> CA
    PCA -- no --> E

    LR --> PLR{more pages?}
    PLR -- yes --> LR
    PLR -- no --> E

    SO --> PSO{more pages?}
    PSO -- yes --> SO
    PSO -- no --> E

    SE --> PSE{more pages?}
    PSE -- yes --> SE
    PSE -- no --> E

    OR --> POR{more pages?}
    POR -- yes --> OR
    POR -- no --> E

    CO --> PCO{more pages?}
    PCO -- yes --> CO
    PCO -- no --> E

    TA --> PTA{more pages?}
    PTA -- yes --> TA
    PTA -- no --> E

    PR --> PPR{more pages?}
    PPR -- yes --> PR
    PPR -- yes --> OND[fetch ongoing deals page\nfor each product in batch]
    PPR -- yes --> CLD[fetch closed deals page\nfor each product in batch]
    PPR -- no --> OND
    PPR -- no --> CLD

    OND --> POND{more pages?}
    POND -- yes --> OND
    POND -- no --> E

    CLD --> PCLD{more pages?}
    PCLD -- yes --> CLD
    PCLD -- no --> E
```

ISO 5807 convention: multiple lines leaving a symbol all fire in parallel. Every chain drains independently to `end`.

## Runtime

The worker reads the following from the environment:

| Variable | Source | Purpose |
|---|---|---|
| `RDS_CLIENT_ID` | k8s secret | OAuth2 app client ID |
| `RDS_CLIENT_SECRET` | k8s secret | OAuth2 app client secret |
| `PGHOST` / `PGPORT` / `PGUSER` / `PGPASSWORD` / `PGDATABASE` | k8s secret | Postgres connection |

`access_token` and `refresh_token` are read from and written back to the `tokens` table (`provider = 'rdstation'`).

## Scripts

Helper scripts for setting up a development environment on a new machine:

- `scripts/config-helix.sh` — configures the Helix editor for this project's stack
- `scripts/install-requirements.sh` — installs Python dependencies and the package in editable mode
