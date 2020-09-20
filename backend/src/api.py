import os
import sys
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
from sqlalchemy.exc import IntegrityError
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink, roll_back
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
-> done for the first run
'''
# db_drop_and_create_all()

# ROUTES


@app.route('/drinks', methods=["GET"])
def get_drinks():
    drinks = Drink.query.all()
    drinks = [drink.short() for drink in drinks]
    return jsonify(success=True, drinks=drinks), 200


@app.route('/drinks-detail', methods=["GET"])
@requires_auth(["get:drinks-detail"])
def get_detail_drinks(payload):
    drinks = Drink.query.all()
    drinks = [drink.long() for drink in drinks]
    return jsonify(success=True, drinks=drinks), 200


@app.route('/drinks', methods=["POST"])
@requires_auth(["post:drinks"])
def post_drinks(payload):
    drinks = []
    try:
        data = request.get_json()
        if data.get('id', None):
            del data['id']
        if data.get('recipe', None):
            if isinstance(data.get('recipe', None), dict):
                data['recipe'] = [data['recipe']]
            if isinstance(data['recipe'], list):
                data['recipe'] = json.dumps(data['recipe'])
        drink = Drink(**data)
        drink.insert()
        drink = Drink.query.get(drink.id)
        drinks = [drink.long()]
    except IntegrityError:
        abort(422)
        print(sys.exc_info())
    except:
        roll_back()
        print(sys.exc_info())
        abort(400)
    return jsonify(success=True, drinks=drinks), 200


@app.route('/drinks/<int:id>', methods=["PATCH"])
@requires_auth(["patch:drinks"])
def update_drink(payload, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)
    try:
        data = request.get_json()
        if data.get('recipe', None):
            if isinstance(data.get('recipe', None), dict):
                data['recipe'] = [data['recipe']]
            if isinstance(data['recipe'], list):
                data['recipe'] = json.dumps(data['recipe'])
        for field in data:
            setattr(drink, field, data[field])
        drink.update()
        drink = Drink.query.get(id)
        return jsonify(success=True, drinks=[drink.long()]), 200
    except:
        abort(400)


@app.route('/drinks/<int:id>', methods=["DELETE"])
@requires_auth(["delete:drinks"])
def delete_drink(payload, id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)
    try:
        drink.delete()
    except:
        print(sys.exc_info())
        abort(500)
    return jsonify(success=True, delete=id), 200

# Error Handling
'''
Example error handling for unprocessable entity
'''


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
                    "success": False,
                    "error": 422,
                    "message": "unprocessable"
                    }), 422

'''
error handling for bad_request entity
'''


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
                    "success": False,
                    "error": 400,
                    "message": "bad request"
                    }), 400

'''
@TODO implement error handlers using the @app.errorhandler(error) decorator
    each error handler should return (with approprate messages):
             jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404

'''

'''
@TODO implement error handler for 404
    error handler should conform to general task above
'''


@app.errorhandler(404)
def bad_request(error):
    return jsonify({
                    "success": False,
                    "error": 404,
                    "message": "resource not found"
                    }), 404


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above
'''


@app.errorhandler(401)
def authentication_error(error):
    return jsonify({
                    "success": False,
                    "error": 401,
                    "message": "authentication failed"
                    }), 401


@app.errorhandler(403)
def authorization_error(error):
    return jsonify({
                    "success": False,
                    "error": 403,
                    "message": "you aren't authorized to do this action"
                    }), 403
