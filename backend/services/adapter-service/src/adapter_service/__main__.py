import os

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "adapter_service.api:app",
        factory=True,
        port=int(os.environ.get("AGENTCORE_ADAPTER_PORT", "32170")),
    )
