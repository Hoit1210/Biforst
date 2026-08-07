import asyncio

import httpx

WEBHOOK_URL = "http://localhost:8000/eks-alert"


async def main() -> None:
    payload = {
        "pod_name": "bifrost-backend-deployment-85b9b8c7-abcde",
        "reason": "OOMKilled",
    }
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(response.json())


if __name__ == "__main__":
    asyncio.run(main())
