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

## ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks',methods=["GET"])
def get_drinks():
    drinks = Drink.query.all()
    drinks = [drink.short() for drink in drinks]
    return jsonify(success=True,drinks=drinks),200

'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks-detail',methods=["GET"])
@requires_auth(["get:drinks-detail"])
def get_detail_drinks(payload):
    drinks = Drink.query.all()
    drinks = [drink.long() for drink in drinks]
    return jsonify(success=True,drinks=drinks),200


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks',methods=["POST"])
@requires_auth(["post:drinks"])
def post_drinks(payload):
    drinks=[]
    try:
        data = request.get_json()
        # print(data)
        if data.get('id',None):
            del data['id']
        if type(data['recipe']) == type([]):        
            data['recipe'] = json.dumps(data['recipe'])
        drink = Drink(**data)
        drink.insert()
        drink = Drink.query.get(drink.id)
        drinks=[drink.long()]
    except IntegrityError:
        abort(422)
        print(sys.exc_info())
    except:
        roll_back()
        print(sys.exc_info())
        abort(400)
    return jsonify(success=True,drinks=drinks),200


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>',methods=["PATCH"])
@requires_auth(["patch:drinks"])
def update_drink(payload,id):
    drink = Drink.query.get(id)
    if not drink:
        abort(404)
    try:
        data = request.get_json()
        if type(data['recipe']) == type([]):
            data['recipe'] = json.dumps(data['recipe'])
        for field in data:
            setattr(drink,field,data[field])
        drink.update()
        drink = Drink.query.get(id)
        return jsonify(success=True, drinks=[drink.long()]),200
    except:
        abort(400)
    


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route('/drinks/<int:id>',methods=["DELETE"])
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
    return jsonify(success=True,delete=id),200

## Error Handling
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
