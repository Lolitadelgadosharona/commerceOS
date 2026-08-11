# Reddit Market Intelligence Connector v1

Status: Sprint 020 implementation contract

## Purpose and ownership

The Reddit connector is an Intelligence-owned, read-only ingestion boundary for discovering customer pain language in explicitly configured subreddits. It stores source records, deterministic pain candidates, and evidence. Decision recommendations, Governance approvals, Operations execution, and Finance economics remain separate.

## Connector and access contract

`RedditConnector` composes the generic connector definition with subreddit scope, keyword scope, and a bounded time window. Its only transport capabilities are `read_posts`, `read_comments`, and metadata storage. The transport authenticates through registered OAuth and identifies itself with an externally configured User-Agent.

Credentials and the User-Agent are injected through `COMMERCE_OS_REDDIT_CLIENT_ID`, `COMMERCE_OS_REDDIT_CLIENT_SECRET`, and `COMMERCE_OS_REDDIT_USER_AGENT`. Secret values are never persisted in connector configuration, responses, raw records, or logs.

The implementation follows Reddit's [Data API guidance](https://support.reddithelp.com/hc/en-us/articles/16160319875092-Reddit-Data-API-Wiki): OAuth is mandatory, the User-Agent must be truthful, provider rate-limit headers are monitored and exhausted clients fail closed, and deleted user content must be removed. Production activation additionally requires approved Reddit access and an operational deletion/reconciliation process.

## Raw Reddit records

`MarketDataRecord` now supports Reddit post and comment records with platform, external identifier, subreddit, title, content, minimized author reference, engagement metrics, and publication time. The raw JSON representation is retained for provenance. Repeated external identifiers from the same connector are skipped by the ingestion service.

## Pain candidates and evidence

`CustomerPainCandidate` stores bounded-confidence observations in five categories: problem, complaint, request, frustration, and want. Detection is deterministic keyword/rule matching; there is no LLM or autonomous analysis. Candidates begin in `DETECTED` and require explicit review before acceptance or rejection.

`PainEvidence` links a candidate to its organization-scoped Reddit source record. V1 requires evidence to reference the same source record that produced the candidate.

## Ingestion lifecycle

An activated connector creates a Reddit-labeled ingestion job and reads only the configured scope:

```text
PENDING/RUNNING -> COMPLETED
                -> FAILED
```

The synchronous V1 command reports records stored during that job and pain candidates detected. It creates no market signal, market opportunity, recommendation, approval, marketing action, message, post, reply, or customer contact.

## Safety and activation limits

- The client exposes only OAuth token acquisition and HTTP GET reads.
- No posting, replying, voting, messaging, moderation, or account action exists.
- Subreddit, keyword, time, and result limits are validated before transport use.
- All persisted records and relationships enforce organization scope.
- Author identity is minimized to Reddit's opaque account fullname when supplied.
- Public deployment remains prohibited until verified authentication and authorization are activated.
- Live runtime validation requires separately provisioned Reddit API approval and OAuth credentials.
