import json

def jsonLoad(DIR, getKeys=[]):
  with open(DIR,"r") as f:
    data = json.load(f)
    if getKeys:
      return {key: data.get(key) for key in getKeys}
    return data
