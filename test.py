from urllib import request
import json

url = 'https://adsai.dk/twitch-clipper/clips' 


def post_clip(link, date, password):
    jsonObject = {"link": link,
                  "date": date,
                  "password":password
                  }

    req = request.Request(url)
    req.add_header('Content-Type', 'application/json; charset=utf-8')
    jsondata = json.dumps(jsonObject)
    jsondataasbytes = jsondata.encode('utf-8')   # needs to be bytes
    req.add_header('Content-Length', len(jsondataasbytes))
    print (jsondataasbytes)
    response = request.urlopen(req, jsondataasbytes) 
    print(response)

post_clip('https://clips.twitch.tv/DignifiedYawningChipmunkFreakinStinkin','01-01-01 00:00','datbois')