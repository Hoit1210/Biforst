import httpx
import asyncio
import json

# 우리가 앞서 구축한 FastAPI 웹훅 서버 주소
WEBHOOK_URL = "http://localhost:8000/alert"

async def simulate_brute_force():
    print("[Red Team] SSH Brute Force 공격 시뮬레이션을 시작합니다...")
    
    # Grafana가 공격을 감지했을 때 FastAPI로 보낼 법한 악의적인 알림 페이로드 조작
    payload = {
        "alerts": [
            {
                "status": "firing",
                "labels": {
                    "alertname": "SSH_Brute_Force_Attack_Detected",
                    "severity": "critical",
                    "instance": "bifrost-production-ec2",
                    "attacker_ip": "203.0.113.50" # Step 5에서 설정한 타겟 공격자 IP
                },
                "annotations": {
                    "summary": "동일한 IP에서 비정상적인 SSH 로그인 실패가 연속으로 감지되었습니다."
                }
            }
        ]
    }

    # FastAPI 서버로 공격 알림 강제 전송
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(WEBHOOK_URL, json=payload)
            if response.status_code == 200:
                print("[Red Team] 공격 알림 트리거 성공! 디스코드로 Bifrost 방어 프로세스가 시작되었습니다.")
                print("디스코드 채널로 이동하여 AI 리포트를 확인하고 '승인'을 진행하세요.")
            else:
                print(f"[Red Team] 전송 실패: HTTP {response.status_code}")
        except Exception as e:
            print(f"[Red Team] 연결 오류: {str(e)}\n(FastAPI 서버가 켜져 있는지 확인하세요!)")

if __name__ == "__main__":
    # 비동기 함수 실행
    asyncio.run(simulate_brute_force())
