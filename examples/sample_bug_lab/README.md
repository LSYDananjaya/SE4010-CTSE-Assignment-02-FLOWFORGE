# Sample Bug Lab

`sample_bug_lab` is a compact full-stack TypeScript repository designed to exercise FlowForge against realistic software-engineering requests.

## Tech Stack

- React + TypeScript style frontend structure under `client/`
- Express + TypeScript style backend structure under `server/`
- Shared types and validation helpers under `shared/`
- Lightweight Vitest-style test files under `tests/`

The project is intentionally small and does not need to be production-ready. It exists so FlowForge can analyze:

- frontend bugs
- backend bugs
- full-stack contract mismatches
- low, medium, and high severity issues

## Bug Catalog

### High / Backend

| ID | Severity | Area | Description | Primary Files |
| --- | --- | --- | --- | --- |
| B1 | High | Backend | Broken route protection lets unauthenticated requests reach protected task APIs. | `server/src/routes/auth.ts`, `server/src/services/sessionService.ts` |
| B2 | High | Backend | Task update endpoint can wipe fields and crash on malformed payloads. | `server/src/routes/tasks.ts`, `server/src/services/taskStore.ts` |

### Medium / Frontend

| ID | Severity | Area | Description | Primary Files |
| --- | --- | --- | --- | --- |
| B3 | Medium | Frontend | Edit modal allows invalid submissions and lacks proper keyboard/accessibility handling. | `client/src/components/EditTaskModal.tsx` |

### Medium / Fullstack

| ID | Severity | Area | Description | Primary Files |
| --- | --- | --- | --- | --- |
| B4 | Medium | Fullstack | Client and shared status values drift from server expectations, causing silent UI inconsistencies. | `client/src/api/tasks.ts`, `shared/types.ts` |

### Low / Frontend

| ID | Severity | Area | Description | Primary Files |
| --- | --- | --- | --- | --- |
| B5 | Low | Frontend | Filter bar uses the wrong default sort order and creates confusing result ordering. | `client/src/components/FilterBar.tsx` |
| B6 | Low | Frontend | Feature badge color mapping is misleading for severity display. | `client/src/components/FeatureCard.tsx` |

### Low / Backend

| ID | Severity | Area | Description | Primary Files |
| --- | --- | --- | --- | --- |
| B7 | Low | Backend | Stats route uses weak diagnostics and repository filtering is inefficient. | `server/src/routes/stats.ts`, `server/src/services/taskStore.ts` |

## Recommended FlowForge prompts

- `what are the improvements can be done on @client/src/components/FeatureCard.tsx`
- `fix the auth bypass in @server/src/routes/auth.ts and @server/src/services/sessionService.ts`
- `review the fullstack status mismatch in @client/src/api/tasks.ts and @shared/types.ts`
- `identify validation issues in @client/src/components/EditTaskModal.tsx`

## Notes

- Bugs are intentionally seeded and documented.
- Some tests are incomplete on purpose so QA and planning can detect coverage gaps.
- The code is optimized for repository analysis, not runtime completeness.
