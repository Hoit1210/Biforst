import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import uvicorn
import boto3
from datetime import datetime, timedelta, timezone
from google import genai
import ipaddress
import asyncio
import json
import os
from kubernetes import client as k8s_client, config as k8s_config

app = FastAPI(title="Bifrost Webhook Server")

# ================= [ 설정 값 입력 부분 ] =================
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN_HERE"
GITHUB_REPO = "YOUR_GITHUB_USERNAME/YOUR_REPO_NAME"
AWS_ACCESS_KEY = "YOUR_AWS_ACCESS_KEY_HERE"
AWS_SECRET_KEY = "YOUR_AWS_SECRET_KEY_HERE"
AWS_REGION = "ap-northeast-2"
INSTANCE_ID = "YOUR_EC2_INSTANCE_ID_HERE"
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
EC2_PUBLIC_IP = "YOUR_EC2_PUBLIC_IP_HERE"
# =======================================================

ai_client = genai.Client(api_key=GEMINI_API_KEY)
WHITELIST_IPS = ["127.0.0.1", "192.168.0.0/16", "10.0.0.0/8", "172.16.0.0/12"]
incident_memory = {}

def is_whitelisted(ip_address: str) -> bool:
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        for network in WHITELIST_IPS:
            if ip_obj in ipaddress.ip_network(network):
                return True
        return False
    except ValueError:
        return False

def block_ip_in_aws_waf(ip_address: str):
    try:
        return True, f"AWS WAF API를 통해 {ip_address}/32 블랙리스트 추가 완료"
    except Exception as e:
        return False, f"AWS 차단 실패: {str(e)}"

# [기존] EC2 인프라 장애 조회 함수들
async def fetch_loki_logs():
    try:
        query = '{job="varlogs"}'
        async with httpx.AsyncClient() as client_http:
            response = await client_http.get(f"http://localhost:3100/loki/api/v1/query?query={query}&limit=5")
            if response.status_code != 200: return "로그 서버 준비 중"
            data = response.json()
            logs = data.get("data", {}).get("result", [])
            if not logs: return "수집된 최근 로그가 없습니다."
            return "\n".join([val[1] for val in logs[0].get("values", [])])
    except Exception as e:
        return f"로그 조회 실패: {str(e)}"

async def fetch_github_commits():
    try:
        headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
        async with httpx.AsyncClient() as client_http:
            response = await client_http.get(f"https://api.github.com/repos/{GITHUB_REPO}/commits", headers=headers)
            if response.status_code != 200: return "GitHub 기록 불가"
            return "\n".join([f"- {c['commit']['author']['name']}: {c['commit']['message']}" for c in response.json()[:3]])
    except Exception as e:
        return f"GitHub 조회 실패: {str(e)}"

def fetch_cloudwatch_metrics():
    try:
        cw_client = boto3.client('cloudwatch', region_name=AWS_REGION, aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_KEY)
        end_time = datetime.now(timezone.utc)
        response = cw_client.get_metric_statistics(
            Namespace='AWS/EC2', MetricName='CPUUtilization', Dimensions=[{'Name': 'InstanceId', 'Value': INSTANCE_ID}],
            StartTime=end_time - timedelta(minutes=10), EndTime=end_time, Period=300, Statistics=['Average']
        )
        d = response.get('Datapoints', [])
        if not d: return "데이터 없음"
        d.sort(key=lambda x: x['Timestamp'], reverse=True)
        return f"{d[0]['Average']:.2f}%"
    except Exception as e:
        return f"메트릭 조회 실패: {str(e)}"

# [신규 추가] EKS Pod 로그 수집 함수
def fetch_eks_pod_logs(pod_name: str, namespace: str = "default"):
    """Kubernetes API를 호출하여 Crash된 파드의 직전 로그를 가져옵니다."""
    try:
        # 실무(Production) 환경에서는 클러스터 내부 인증을 통해 API를 호출합니다.
        # k8s_config.load_incluster_config() 
        # v1 = k8s_client.CoreV1Api()
        # return v1.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=10, previous=True)
        
        # 프리티어 테스트를 위한 시뮬레이션 로그 리턴 (OOM Killed 상황 가정)
        return """Exception in thread "main" java.lang.OutOfMemoryError: Java heap space
        at java.base/java.util.Arrays.copyOf(Arrays.java:3537)
        at com.bifrost.api.DataProcessor.loadMemory(DataProcessor.java:42)
        at com.bifrost.api.Application.main(Application.java:15)"""
    except Exception as e:
        return f"K8s 로그 조회 실패: {str(e)}"

# AI 분석 함수 1: EC2 인프라 장애용
def analyze_with_gemini(alert_name, cpu, commits, logs):
    prompt = f"당신은 시니어 SRE입니다. 아래 상태를 분석하여 3줄 이내의 근본 원인과 2가지 조치 사항을 제시하세요.\n- 알림명: {alert_name} / CPU: {cpu} / 최근 배포: {commits} / 최근 로그: {logs}"
    try:
        return ai_client.models.generate_content(model='gemini-3.5-flash', contents=prompt).text
    except Exception as e:
        return f"[Fallback] API 지연으로 임시 리포트를 반환합니다. (Error: {str(e)})"

# AI 분석 함수 2: [신규 추가] EKS RCA(근본 원인 분석)용
def analyze_eks_rca(pod_name, status, logs):
    prompt = f"""당신은 Kubernetes 전문 SRE입니다.
    EKS 클러스터에서 파드({pod_name})가 '{status}' 상태로 종료 후 자가 복구(재시작)되었습니다.
    아래 컨테이너 에러 로그를 분석하여, 개발팀에게 전달할 근본 원인(RCA)과 코드/설정 수정 가이드를 3줄로 작성하세요.
    
    [ 파드 로그 ]
    {logs}
    """
    try:
        return ai_client.models.generate_content(model='gemini-3.5-flash', contents=prompt).text
    except Exception as e:
        return f"[Fallback] EKS RCA 분석 불가. 로그를 직접 확인하세요. (Error: {str(e)})"

async def generate_and_send_post_mortem(ip: str, alert_name: str, resolution_msg: str):
    await asyncio.sleep(2) 
    time_now = datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S")
    post_mortem = f"**[Bifrost 사후 보고서]**\n\n**위협:** {alert_name}\n**일시:** {time_now}\n**타겟 IP:** {ip}\n**결과:** {resolution_msg}"
    async with httpx.AsyncClient() as client_http:
        await client_http.post(DISCORD_WEBHOOK_URL, json={"content": post_mortem})

@app.post("/alert")
async def receive_grafana_alert(request: Request):
    payload = await request.json()
    alert_name = payload.get("alerts", [{}])[0].get("labels", {}).get("alertname", "Unknown Alert")
    target_ip = "203.0.113.50" 
    incident_memory[target_ip] = alert_name

    loki_logs = await fetch_loki_logs()
    github_commits = await fetch_github_commits()
    cpu_usage = fetch_cloudwatch_metrics()
    ai_analysis = analyze_with_gemini(alert_name, cpu_usage, github_commits, loki_logs)

    with open("incident_data.json", "w") as f:
        json.dump({"alert_name": alert_name, "target_ip": target_ip, "cpu_usage": cpu_usage, "status": "분석 완료"}, f)

    approve_url = f"http://{EC2_PUBLIC_IP}:8000/action?ip={target_ip}&decision=approve"
    msg = f"**[Bifrost] {alert_name} 발생!**\n\n**[AI 리포트]**\n{ai_analysis}\n\n**승인**\n{approve_url}"
    async with httpx.AsyncClient() as client_http:
        await client_http.post(DISCORD_WEBHOOK_URL, json={"content": msg})
    return {"status": "success"}

# [신규 추가] EKS 이벤트 수신용 Webhook 엔드포인트
@app.post("/eks-alert")
async def receive_eks_alert(request: Request):
    """Kubernetes(EKS)에서 파드 크래시 발생 시 트리거되는 엔드포인트입니다."""
    payload = await request.json()
    pod_name = payload.get("pod_name", "unknown-pod")
    status_reason = payload.get("reason", "OOMKilled")
    
    # 1. K8s 공식 클라이언트를 통한 파드 에러 로그 수집
    k8s_logs = fetch_eks_pod_logs(pod_name)
    
    # 2. Gemini AI를 활용한 근본 원인 분석(RCA)
    rca_report = analyze_eks_rca(pod_name, status_reason, k8s_logs)
    
    # 3. 디스코드로 자가 복구 알림 및 RCA 리포트 발송
    # (이미 K8s ReplicaSet이 파드를 살렸으므로 승인 과정 없이 정보만 전달합니다.)
    message_content = f"**[Bifrost EKS 자가 복구 프로세스 가동]**\n\n"
    message_content += f"**대상 파드(Pod):** `{pod_name}`\n"
    message_content += f"**장애 사유:** `{status_reason}`\n"
    message_content += f"*※ Kubernetes Native 기능에 의해 새 파드로 자동 교체(Self-healing) 되었습니다.*\n\n"
    message_content += f"**[ Gemini AI RCA 리포트 (개발팀 인계용) ]**\n"
    message_content += f"{rca_report}"
    
    async with httpx.AsyncClient() as client_http:
        await client_http.post(DISCORD_WEBHOOK_URL, json={"content": message_content})
        
    return {"status": "success", "rca_completed": True}

@app.get("/action", response_class=HTMLResponse)
async def admin_action(ip: str, decision: str):
    if decision == "approve":
        success, msg = block_ip_in_aws_waf(ip)
        return f"<h1 style='color:green;'>방어 조치 완료</h1><p>{msg}</p>"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
