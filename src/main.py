"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Todo
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/todos/<username>', methods=['GET'])
def get_todos(username):
    todos = Todo.query.filter_by(username=username)
    todos = list(map(lambda x: x.serialize(), todos))
    print("The todos: ", todos)
    return jsonify(todos), 200        

@app.route('/todos/<username>', methods=['POST'])
def post_todo(username):
    body = request.get_json()
    exists = Todo.query.filter_by(username=username, label=body['label']).first()
    if exists is not None:
        raise APIException('You already have this ToDo item', status_code=404)
    todo = Todo(label=body['label'], done=body['done'], username=username)
    db.session.add(todo)
    db.session.commit()
    todos = Todo.query.filter_by(username=username)
    todos = list(map(lambda x: x.serialize(), todos))
    return jsonify(todos), 200
    
@app.route('/todos/<int:id>', methods=['PUT'])    
def edit_todos(id):
    body = request.get_json()
    updating_item = Todo.query.get(id)
    if updating_item is None:
        raise APIException('Entry does not exist', status_code=400)
    updating_item.label = body['label']
    updating_item.done = body['done']
    db.session.commit()
    todos = Todo.query.filter_by(username=body['username'])
    the_todos = list(map(lambda x: x.serialize(), todos))
    return jsonify(the_todos), 200

@app.route('/todos/<username>/<int:id>', methods=['DELETE'])
def delete_todo(username, id):
    todo = Todo.query.get(id)
    print(todo)
    if todo is None:
        raise APIException('The entry does not exist', status_code=400)
    db.session.delete(todo)
    db.session.commit()
    todos = Todo.query.filter_by(username=username)
    todos = list(map(lambda x: x.serialize(), todos))
    return jsonify(todos), 200   


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
