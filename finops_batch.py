import httpx
import asyncio
from google import genai
from datetime import datetime, timedelta, timezone

# ================= [ 설정 값 입력 부분 ] =================
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
# =======================================================

client = genai.Client(api_key=GEMINI_API_KEY)

def generate_finops_threat_report():
    """비용 데이터와 보안 데이터를 종합하여 AI 리포트를 생성합니다."""
    
    # 프리티어 과금 방지를 위한 데이터 Mocking (실무에서는 boto3 CE, GuardDuty API 호출)
    mock_cost_data = "현재 AWS 이번 달 예상 요금: 0.00 USD (Free Tier 100% 활용 중). EC2 t2.micro 1대 가동 중."
    mock_threat_data = "최근 24시간 내 WAF 차단 이력: 1건 (203.0.113.50 - SSH Brute Force 시도)."
    
    prompt = f"""
    당신은 시니어 SRE 및 클라우드 FinOps 전문가입니다.
    아래의 클라우드 비용 데이터와 보안 위협 데이터를 분석하여, 
    1. '리소스 비용 최적화(FinOps) 제안' 1줄
    2. '잠재적 위협 사전 탐지(Threat Hunting) 의견' 1줄
    을 작성해 주세요.
    
    [비용 데이터]: {mock_cost_data}
    [보안 데이터]: {mock_threat_data}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash', 
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"[Fallback] 리포트 생성 실패 (API 지연): {str(e)}"

async def send_daily_report():
    print("[Batch] FinOps & Threat Hunting 리포트 생성을 시작합니다...")
    report = generate_finops_threat_report()
    
    time_now = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
    message = f"**[Bifrost Daily 일일 브리핑]**\n\n"
    message += f"**일시:** {time_now} (KST)\n\n"
    message += f"**[ FinOps & Threat Hunting AI 리포트 ]**\n"
    message += f"{report}\n\n"
    message += "> *본 리포트는 매일 자정 Bifrost 자동화 배치에 의해 발송됩니다.*"
    
    async with httpx.AsyncClient() as http_client:
        await http_client.post(DISCORD_WEBHOOK_URL, json={"content": message})
    print("[Batch] 디스코드 발송 완료!")

if __name__ == "__main__":
    asyncio.run(send_daily_report())
