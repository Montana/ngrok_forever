import json
import subprocess
import time
from pathlib import Path
import atexit
import boto3
import requests
import datetime

ngrokDir = "/home/pi"
port = "5000"

useDynamo = True
dynamodb = boto3.resource("dynamodb")
dbPiNgRok = dynamodb.Table("PiNgrok")
deviceId = "mypi"

localhost_url = "http://localhost:4040/api/tunnels"  # Url with tunnel details


def updateDynamoDB(ngrok_address):
    dbPiNgRok.update_item(
        Key={"deviceId": deviceId},
        UpdateExpression="SET address = :address, createdOn=:createdOn",
        ExpressionAttributeValues={
            ":address": ngrok_address,
            ":createdOn":
            "{:%Y-%m-%d %H:%M:%S}".format(datetime.datetime.now()),
        },
    )


def is_running():
    try:
        ngrok_req = requests.get(localhost_url).text
        ngrok_address = get_ngrok_url(ngrok_req)
        print("ngrok is already running {ngrok_address}".format(
            ngrok_address=ngrok_address))
        r = requests.get(ngrok_address)
        if r.status_code == 402:
            return _run_ngrok()
        return ngrok_address
    except Exception as e:
        print("exception", e)
        return _run_ngrok()


def get_ngrok_url(ngrok_req):
    j = json.loads(ngrok_req)
    tunnel_url = j["tunnels"][len(j["tunnels"]) - 1]["public_url"]
    return tunnel_url


def _run_ngrok():
    global ngrokDir
    command = "ngrok"
    executable = str(Path(ngrokDir, command))
    ngrok = subprocess.Popen(
        [executable, "http", "-inspect=false", "-bind-tls=true", port])
    atexit.register(ngrok.terminate)
    time.sleep(3)
    tunnel_url = requests.get(localhost_url).text 
    ngrok_address = get_ngrok_url(tunnel_url)
    print("ngrok created  {ngrok_address}".format(ngrok_address=ngrok_address))

    updateDynamoDB(ngrok_address)

    time.sleep(3540)
    return ngrok_address


is_running()
