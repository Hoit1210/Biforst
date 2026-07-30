import httpx
import asyncio

WEBHOOK_URL = "http://localhost:8000/eks-alert"

async def simulate_eks_crash():
    print("♻️ [Red Team] EKS Pod OOMKilled 장애 시뮬레이션을 시작합니다...")
    
    payload = {
        "pod_name": "bifrost-backend-deployment-85b9b8c7-abcde",
        "reason": "OOMKilled"
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(WEBHOOK_URL, json=payload)
            if response.status_code == 200:
                print("[Red Team] EKS 장애 이벤트 트리거 성공!")
                print("디스코드에서 K8s 자가 복구 알림과 AI RCA 리포트를 확인하세요.")
        except Exception as e:
            print(f"연결 오류: {str(e)}")

if __name__ == "__main__":
    asyncio.run(simulate_eks_crash())
