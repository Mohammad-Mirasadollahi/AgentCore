import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "docs_sync_service.api:app",
        factory=True,
        port=int(os.environ.get("AGENTCORE_DOCS_SYNC_PORT", "32130")),
    )
