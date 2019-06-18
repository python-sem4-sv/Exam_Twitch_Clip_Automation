from flask import (Flask, request, jsonify)
import pymongo
from flask_pymongo import PyMongo
from settings import (rest_password, connection_string)
from flask import render_template
from flask_cors import CORS


app = Flask(__name__)
app.config["MONGO_URI"] = connection_string
CORS(app)
mongo = PyMongo(app)
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/clips', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        return post_method()
    elif request.method == 'GET':
        return get_method()


def post_method():
    #body returns a dictionary
    body = request.json
    if body.get('password') != None and body['password'] == rest_password:
        #mongodb expects a dictionary
        mongo.db.clips.insert_one({'url': body['url'], 'date': body['date']})
        return "Inserted :)"
    else:
        return jsonify({'msg': 'Error!'})

def get_method():
    clips = mongo.db.clips.find({})
    response = [ {'url':clip['url'], 'date':clip['date']} for clip in clips ]
    
    return jsonify(response)

if __name__ == '__main__':
    app.run()