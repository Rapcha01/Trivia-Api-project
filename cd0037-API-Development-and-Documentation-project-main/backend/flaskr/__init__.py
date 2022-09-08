import os
import flask_cors
from flask import Flask, request, abort, jsonify, json
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
import models

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10
def paginate_questions(request, selection):
  page = request.args.get('page', 1, type=int)
  start =  (page - 1) * QUESTIONS_PER_PAGE
  end= start + 10

  questions = [question.format() for question in selection]
  current_questions = questions[start:end,]

  return current_questions

def create_app(test_config=None):
  # create and configure the app
  app = Flask(__name__)
  setup_db(app)

  
  @app.after_request
  def after_request(response):
      response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
      response.headers.add('Access-Control-Allow-Methods', 'GET,PATCH,POST,DELETE,OPTIONS')
      return response


  @app.route("/categories")
  def get_categories():
      categories = list(map(Category.format, Category.query.all()))
      result = {
          "success": True,
          "categories": categories
      }
      return jsonify(result)


  @app.route('/questions')
  def retrieve_questions():
    selection = Question.query.order_by(Question.id).all()
    current_questions = paginate_questions(request, selection)
    categories = list(map(Category.format, Category.query.all()))


    if len(current_questions) == 0:
      abort(404)

    return jsonify({
      'success': True,
      'questions': current_questions,
      'total_questions': len(Question.query.all()),
      'categories': categories,
      'current_category': None,
    })



  @app.route('/questions/<int:question_id>', methods=['DELETE'])
  def delete_question(question_id):
    try:
      question = Question.query.filter(Question.id == question_id).one_or_none()

      if question is None:
        abort(404)

      question.delete()
      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'deleted': question_id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)



  @app.route("/questions", methods=['POST'])
  def add_question():
    body = request.get_json()
    
    new_question = body.get('question', None)
    new_answer = body.get('answer', None)
    new_category = body.get('category', None)
    new_difficulty = body.get('difficulty', None)
    try:

      question = Question(question=new_question,answer=new_answer, category=new_category, difficulty=new_difficulty)
      question.insert()

      selection = Question.query.order_by(Question.id).all()
      current_questions = paginate_questions(request, selection)

      return jsonify({
        'success': True,
        'created': question.id,
        'questions': current_questions,
        'total_questions': len(Question.query.all())
      })

    except:
      abort(422)



  @app.route("/searchQuestions", methods=['POST'])
  def search_questions():
      if request.data:
          page = 1
          if request.args.get('page'):
              page = int(request.args.get('page'))
          search_data = json.loads(request.data.decode('utf-8'))
          if 'searchTerm' in search_data:
              questions_query = Question.query.filter(
                  Question.question.like(
                      '%' +
                      search_data['searchTerm'] +
                      '%')).paginate(
                  page,
                  QUESTIONS_PER_PAGE,
                  False)
              questions = list(map(Question.format, questions_query.items))
              if len(questions) > 0:
                  result = {
                      "success": True,
                      "questions": questions,
                      "total_questions": questions_query.total,
                      "current_category": None,
                  }
                  return jsonify(result)
          abort(404)
      abort(422)



  @app.route("/categories/<int:category_id>/questions")
  def get_question_by_category(category_id):
      category_data = Category.query.get(category_id)
      page = 1
      if request.args.get('page'):
          page = int(request.args.get('page'))
      categories = list(map(Category.format, Category.query.all()))
      questions_query = Question.query.filter_by(
          category=category_id).paginate(
          page, QUESTIONS_PER_PAGE, False)
      questions = list(map(Question.format, questions_query.items))
      if len(questions) > 0:
          result = {
              "success": True,
              "questions": questions,
              "total_questions": questions_query.total,
              "categories": categories,
              "current_category": Category.format(category_data),
          }
          return jsonify(result)
      abort(404)


 
  @app.route("/quizzes", methods=['POST'])
  def get_question_for_quiz():
      if request.data:
          search_data = json.loads(request.data.decode('utf-8'))
          if (('quiz_category' in search_data
                and 'id' in search_data['quiz_category'])
                  and 'previous_questions' in search_data):
              questions_query = Question.query.filter_by(
                  category=search_data['quiz_category']['id']
              ).filter(
                  Question.id.notin_(search_data["previous_questions"])
              ).all()
              length_of_available_question = len(questions_query)
              if length_of_available_question > 0:
                  result = {
                      "success": True,
                      "question": Question.format(
                          questions_query[random.randrange(
                              0,
                              length_of_available_question
                          )]
                      )
                  }
              else:
                  result = {
                      "success": True,
                      "question": None
                  }
              return jsonify(result)
          abort(404)
      abort(422)

  '''
  @TODO: 
  Create error handlers for all expected errors 
  including 404 and 422. 
  '''
 
  @app.errorhandler(404)
  def not_found(error):
    return jsonify({
      "success":False,
      'error': 404,
      "message":"not found the given resource"
      }), 404

  @app.errorhandler(422)
  def unprocessable(error):
    return jsonify({
      "success":False,
      'error': 422,
      "message":"Unprocessable"
      }), 422

  @app.errorhandler(400)
  def bad_request(error):
    return jsonify({
      "success":False,
      'error': 400,
      "message":"Bad Request"
      }), 400

  @app.errorhandler(500)
  def server_error(error):
    return jsonify({
      "success":False,
      'error': 500,
      "message":"Internal server error"
      }), 500
  
  return app

  
  return app

    