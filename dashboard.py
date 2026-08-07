import json
import os
import time

import streamlit as st

DATA_FILE = os.getenv("INCIDENT_FILE", "incident_data.json")

st.set_page_config(page_title="Bifrost SRE Dashboard", page_icon="🛡️", layout="wide")
st.title("Bifrost Incident Dashboard")
st.caption("Latest incident context and response status")

placeholder = st.empty()

while True:
    data = None
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            data = None

    with placeholder.container():
        if not data:
            st.info("No incident data yet. Waiting for an alert...")
        else:
            st.subheader(f"Latest incident: {data.get('alert_name', 'Unknown')}")
            c1, c2, c3 = st.columns(3)
            c1.metric("Target IP", data.get("target_ip", "-"))
            c2.metric("EC2 CPU", data.get("cpu_usage", "-"))
            c3.metric("Status", data.get("status", "-"))

            left, right = st.columns(2)
            with left:
                st.markdown("### Incident analysis")
                st.info(data.get("ai_analysis", "No analysis"))
                st.markdown("### Recent GitHub deployment history")
                st.code(data.get("github_commits", "No deployment context"), language="text")
            with right:
                st.markdown("### Loki log context")
                st.code(data.get("loki_logs", "No log context"), language="text")

            st.caption(f"Updated: {data.get('timestamp', '-')}")

    time.sleep(3)
