import json
with open("src/machines/local/local.json", "r") as r:
    data = json.load(r)

with open(data["home"]["user"]["Desktop"]["cool.txt"], "r") as r:
    text = r.read()
    print(text)