#!/usr/bin/env python3

import argparse
import json
import sys
import requests
import os
import urllib3
from dotenv import load_dotenv


load_dotenv("config.env.local")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SEMS_USER=os.getenv("SEMS_USER")
SEMS_PW=os.getenv("SEMS_PW")
SEMS_URL=os.getenv("SEMS_URL")
SEMS_SEALMAN_CONFIG_NAME=os.getenv("SEMS_SEALMAN_CONFIG_NAME")
SEMS_SEALMAN_TEMPLATE_NAME=os.getenv("SEMS_SEALMAN_TEMPLATE_NAME")

IOTHUB_URL=os.getenv("IOTHUB_URL")
IOTHUB_SAS_TOKEN=os.getenv("IOTHUB_SAS_TOKEN")

def create_iot_device(device_id):
    print(f"➡️  Creating IoT Edge device '{device_id}'...")
    headers = {
        "Authorization": IOTHUB_SAS_TOKEN,
        "Content-Type": "application/json"
    }
    data = {
        "deviceId": device_id,
        "capabilities": {
            "iotEdge": True
        }
    }
    response = requests.put(f"https://{IOTHUB_URL}/devices/{device_id}?api-version=2021-04-12",
                            headers=headers, json=data)

    if response.status_code not in [200, 409]:
        print(f"❌ Failed to create device. HTTP status code: {response.status_code}")
        sys.exit(1)
    elif response.status_code == 409:
        print(f"ℹ️  Device '{device_id}' already exists.")
    else:
        device_key = response.json()["authentication"]["symmetricKey"]["primaryKey"]
        device_connection_string = f"HostName={IOTHUB_URL};DeviceId={device_id};SharedAccessKey={device_key}"
        print("✅ Device successfully created.")
        return device_connection_string

def update_device_tag(device_id, deployment="base"):
    print(f"➡️  Setting 'deployment' tag for device '{device_id}'...")
    headers = {
        "Authorization": IOTHUB_SAS_TOKEN,
        "Content-Type": "application/json"
    }
    payload = {
        "tags": {
            "deployment": deployment
        }
    }
    response = requests.patch(f"https://{IOTHUB_URL}/twins/{device_id}?api-version=2021-04-12",
                              headers=headers, json=payload)
    if response.status_code == 200:
        print("✅  Deployment tag successfully applied.")
    else:
        print(f"❌  Failed to update deployment tag. HTTP status code: {response.status_code}")
        sys.exit(2)

def create_sems_device(device_id, device_connection_string=None):
    print(f"➡️  Creating SEMS device '{device_id}'...")
    auth_payload = {
        "username": SEMS_USER,
        "password": SEMS_PW
    }
    try:
        auth_response = requests.post(f"{SEMS_URL}/web/api/authentication/login_check",
                                      json=auth_payload, verify=False)
        auth_response.raise_for_status()
        token = auth_response.json().get("token")
    except Exception as e:
        print(f"❌  Failed to authenticate with SEMS: {e}")
        sys.exit(2)

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    search_response = requests.post(f"{SEMS_URL}/web/api/template/list", headers=headers, verify=False,
                                    json={"page": 1, "rowsPerPage": 10,
                                          "sorting": [{"field": "createdAt", "direction": "desc"}], "filters": {
                                            "name": {"filterBy": "name", "filterType": "equal",
                                                     "filterValue": SEMS_SEALMAN_TEMPLATE_NAME}}})

    if search_response.status_code != 200:
        print(f"❌  Failed to connect SEMS. HTTP status code: {search_response.status_code}")
        sys.exit(2)
    if search_response.json().get("rowCount") == 1:
        template_id = search_response.json()["results"][0]["id"]

    def get_env_variable(name):
        value = os.getenv(name)
        return value if value else None

    env_variable_names = [
        "EDGE_AGENT_IMAGE",
        "EDGE_AGENT_SERVERADDRESS",
        "EDGE_AGENT_USERNAME",
        "EDGE_AGENT_PASSWORD",
        "COMPOSE_DOCKER_AUTH_SERVERADDRESS",
        "COMPOSE_DOCKER_AUTH_TOKEN",
        "VPN_IMAGE",
        "VPN_VSS_ADDRESS",
        "VPN_VSS_API_USER",
        "VPN_VSS_API_KEY"
    ]

    variables = [{"name": "iothub_device_connection_string", "variableValue": device_connection_string}]
    for name in env_variable_names:
        value = get_env_variable(name)
        if value is not None:
            variables.append({
                "name": name.lower(),
                "variableValue": value
            })

    device_payload = {
        "variables": variables,
        "name": device_id,
        "serialNumber": device_id,
        "template": int(template_id),
        "imei": "123",
        "model": "EG500",
        "registrationId": "123",
        "endorsementKey": "123",
        "enabled": True,
        "reinstallConfig1": True,
        "deviceType": "10"
    }

    response = requests.post(f"{SEMS_URL}/web/api/device/create",
                             headers=headers, json=device_payload, verify=False)

    if response.status_code == 200:
        print("✅  SEMS device successfully created.")
    else:
        print(f"❌  Failed to create SEMS device. HTTP status code: {response.status_code}")
        sys.exit(2)


# -------------------- Main --------------------
def main():
    parser = argparse.ArgumentParser(description="IoTHub and SEMS device deployment script")
    parser.add_argument("device_id", help="e.g. 12345678")

    args = parser.parse_args()

    device_connection_string = create_iot_device(args.device_id)
    update_device_tag(args.device_id)
    create_sems_device(args.device_id, device_connection_string)

if __name__ == "__main__":
    main()
