# Technical Logic and Verification - Risks, Challenges, and Acceptance

## Challenges

- Technical logic can drift from implemented vertical slices if docs and tests are updated separately.
- Teams may treat Phase 6 as optional reading and jump to Phase 7 graph work too early.
- Cross-domain runtime scenarios are easy to under-specify, leaving hidden handoffs.
- Model judgment without deterministic guards reappears when pressure for speed rises.
- Waivers can become a permanent escape hatch if they lack owners and expirations.

## Mitigation Strategy

- Keep Phase 6 as an explicit roadmap gate between Phase 5 and Phase 7.
- Require canonical `tests/` commands in every Phase 1 through 5 service README.
- Maintain one end-to-end runtime document that names every handoff.
- Fail closed on missing evidence for high-risk paths.
- Record waivers with owner, reason, expiration, and linked Issue or Decision.

## Acceptance Criteria

- Roadmap Phase 6 exists as a separate gated phase, not only a documentation folder name.
- `docs/06-technical-logic/` contains both phase-design files and domain technical logic packs.
- Every owned vertical slice names a canonical pytest command under `tests/backend/services/<service>/`.
- The technical-logic feature gate at `tests/backend/gates/technical-logic-verification/` passes (or is waived with an owner).
- End-to-end runtime logic can be traced from agent action to brokered completion without undocumented steps.
- Contract, state-machine, idempotency, and redaction expectations are defined for the owned surfaces.
- Phase 7 work requires Phase 6 gate pass or an explicit owned waiver.
