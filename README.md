# improved-doodle

RD Station CRM worker for the **modest-galois** project. Fetches the full CRM graph from the RD Station v2 API, builds the domain model via **fluffy-waddle**, and writes it to the sales schema in Postgres.

The sync strategy is a full replace every run: nuke the sales schema, repopulate from scratch. At ~2000 records this is faster than diffing.

## Flow

```mermaid
flowchart TD
    S([start]) --> RT[rotate token\nDB + env → POST /oauth2/token → DB]
    RT --> F1(( ))

    F1 --> U[fetch /users]
    F1 --> T[fetch /teams]
    F1 --> PL[fetch /pipelines]
    F1 --> CA[fetch /campaigns]
    F1 --> LR[fetch /lost_reasons]
    F1 --> SO[fetch /sources]
    F1 --> SE[fetch /segments]
    F1 --> PR[fetch /products]
    F1 --> OR[fetch /organizations]
    F1 --> CO[fetch /contacts]
    F1 --> TA[fetch /tasks]

    U --> PU{next page?}
    PU -- yes --> U
    PU -- no --> J1(( ))

    T --> PT{next page?}
    PT -- yes --> T
    PT -- no --> J1

    PL --> PPL{next page?}
    PPL -- yes --> PL
    PPL -- no --> J1

    CA --> PCA{next page?}
    PCA -- yes --> CA
    PCA -- no --> J1

    LR --> PLR{next page?}
    PLR -- yes --> LR
    PLR -- no --> J1

    SO --> PSO{next page?}
    PSO -- yes --> SO
    PSO -- no --> J1

    SE --> PSE{next page?}
    PSE -- yes --> SE
    PSE -- no --> J1

    PR --> PPR{next page?}
    PPR -- yes --> PR
    PPR -- no --> J1

    OR --> POR{next page?}
    POR -- yes --> OR
    POR -- no --> J1

    CO --> PCO{next page?}
    PCO -- yes --> CO
    PCO -- no --> J1

    TA --> PTA{next page?}
    PTA -- yes --> TA
    PTA -- no --> J1

    J1 --> F2(( ))

    F2 --> STG[fetch /pipelines/id/stages\nonce per pipeline]
    F2 --> OND[fetch /deals status:ongoing\nonce per product]
    F2 --> WON[fetch /deals status:won last 12mo\nonce per product]

    STG --> PSTG{next page?}
    PSTG -- yes --> STG
    PSTG -- no --> J2(( ))

    OND --> POND{next page?}
    POND -- yes --> OND
    POND -- no --> J2

    WON --> PWON{next page?}
    PWON -- yes --> WON
    PWON -- no --> J2

    J2 --> INJ[inject pipeline_id into stages]
    INJ --> DD[deduplicate deals\nbuild deal → products map]
    DD --> BLD[build domain models]
    BLD --> NK[nuke sales schema]
    NK --> INS[insert deals graph]
    INS --> E([end])
```

The two fork/join circles mark the round boundaries. Everything between a fork and its join fires in parallel. Pagination within each branch is sequential — follow `next` until it is absent.

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
