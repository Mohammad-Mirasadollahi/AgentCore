# Third-Party Notices — Code Intelligence Prior Art

Path: `docs/07-code-knowledge-graph/THIRD_PARTY_NOTICES.md`

This file records **attribution** for MIT-licensed open-source projects whose
**ideas** (and, if ever approved by ADR, source) inform AgentCore Code-Knowledge
Graph intelligence features. AgentCore’s default policy is clean-room
re-implementation; see
[`21-code-intelligence-prior-art-ideas-and-license.md`](21-code-intelligence-prior-art-ideas-and-license.md).

Verification date for LICENSE URLs: **2026-07-20**.

---

## colbymchenry/codegraph

- Repository: https://github.com/colbymchenry/codegraph
- License: MIT
- Copyright: Copyright (c) 2026 Colby Mchenry
- AgentCore use: ideas (explore packing, framework routes, MCP UX); no vendored source as of this notice

```text
MIT License

Copyright (c) 2026 Colby Mchenry

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## tirth8205/code-review-graph

- Repository: https://github.com/tirth8205/code-review-graph
- License: MIT
- Copyright: Copyright (c) 2026 Tirth Kanani
- AgentCore use: ideas (flows, risk scoring, communities, TESTED_BY, hybrid search); no vendored source as of this notice

```text
MIT License

Copyright (c) 2026 Tirth Kanani

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Graphify-Labs/graphify

- Repository: https://github.com/Graphify-Labs/graphify
- License: MIT
- Copyright: Copyright (c) 2026 Safi Shamsi
- AgentCore use: ideas (edge confidence UX, god/surprise nodes, path queries, rationale); no vendored source as of this notice

```text
MIT License

Copyright (c) 2026 Safi Shamsi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## Runtime Python packages (retrieval stack)

These are **dependencies**, not prior-art idea sources. Keep versions pinned in
`pyproject.toml`.

### rank-bm25

- Package: `rank-bm25`
- License: Apache License 2.0
- Role: Optional Okapi BM25 accelerator for larger in-process corpora
  (`domain/hybrid_search.py`). Lucene-style BM25 remains the small-corpus path.

### scikit-network

- Package: `scikit-network` (optional extra `graph-analytics`)
- License: BSD
- Role: Leiden community detection when installed; Louvain fallback otherwise.
  AgentCore does not call Neo4j GDS for communities (portability). GDS Community
  Edition can run algorithms without an Enterprise key — see doc `32`.

---

## Maintenance

When adding a vendored dependency or copying substantial upstream source:

1. Update this file with the exact commit/tag and copyright year from upstream.
2. Ensure redistributed artifacts include the MIT notices.
3. Record an ADR acceptance for the vendoring decision.
4. Update SBOM generation inputs used by release pipelines.
