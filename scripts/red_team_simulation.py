import asyncio

import httpx

WEBHOOK_URL = "http://localhost:8000/alert"


async def main() -> None:
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "SSH_Brute_Force_Attack_Detected",
                    "severity": "critical",
                    "instance": "bifrost-test-instance",
                    "attacker_ip": "203.0.113.50",
                },
                "annotations": {
                    "summary": "Controlled incident-response validation payload."
                },
            }
        ]
    }
    async with httpx.AsyncClient(timeout=8) as client:
        response = await client.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(response.json())


if __name__ == "__main__":
    asyncio.run(main())
