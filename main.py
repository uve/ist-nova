#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import webapp2

import jinja2
import os
import logging

import models

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


from google.appengine.ext import db
from google.appengine.api import users

import random

def login_required(func):
    def check_auth(*args, **kwargs):
        #print "Authenticated."              
        
        login_url = users.create_login_url(args[0].request.uri)
        args[0].request.logout_url = users.create_logout_url(args[0].request.uri)        

        google_user = users.get_current_user()
        
        if not google_user:
            return args[0].redirect(login_url)
            
        user_id = google_user.user_id()
        user = models.User.get_item(user_id)
        if user is None:
            user = models.User(key_name=str(google_user.user_id()), id=str(google_user.user_id()),
                name=google_user.email())
            user.put()
            user = models.User.get_item(google_user.user_id())  
        
        args[0].request.user_id = user    
            
        return func(*args, **kwargs)
    
    return check_auth
    



class MainPage(webapp2.RequestHandler):
    
    @login_required
    def get(self):
        
        
        all_questions = models.Question.gql("Order by id asc").fetch(100)
                       
         
        template_values = {                        
            'logout_url': self.request.logout_url,
            'user_id': self.request.user_id,
            'all_questions': all_questions        
        }    
            
        template = jinja_environment.get_template('templates/index.html')
        self.response.out.write(template.render(template_values))




class Stat(webapp2.RequestHandler):
    
    @login_required
    def get(self):
                         
        all_questions = models.Question.gql("Order by id asc").fetch(100)
        
        
        for item in all_questions:
            
            item.answers = models.Answer.gql("WHERE question_id = :1", item).fetch(100)
            
            for value in item.answers:
                value.votes = random.randint(10, 1000)
        
        
        
        template_values = {                        
            'logout_url': self.request.logout_url,
            'user_id': self.request.user_id,
            'all_questions': all_questions,
            
        }    
            
        template = jinja_environment.get_template('templates/stat.html')
        self.response.out.write(template.render(template_values))



class Order(webapp2.RequestHandler):
        
    def get(self):
                
        questions = models.Question.gql("Order by id asc").fetch(100)
        
        last = None
        
        '''
        for item in questions:                                            
            if item.additional:
                item.additional.is_additional = True
            else:
                item.additional.is_additional = False
        '''
        
        
        db.put(questions)        
        
        questions = models.Question.gql("Order by id asc").fetch(100)
                
        for item in questions:            
            item.prev = last
            last = item
            
            
        questions.reverse()    
 
        last = None
               
        for item in questions:        
            item.next = last
            last = item     
            
        questions.reverse()   

        db.put(questions)            

            
        self.response.out.write('Questions are ordered')



class Vote(webapp2.RequestHandler):
    
    @login_required
    def get(self, id):
                
        question = models.Question.get_item(id)
        answers = models.Answer.gql("WHERE question_id = :1", question).fetch(100)
                                    
        template_values = {                        
            'logout_url': self.request.logout_url,
            'user_id': self.request.user_id,        
            'question': question,
            'answers': answers,
            #'first': first,    
        }    
            
        template = jinja_environment.get_template('templates/question.html')
        self.response.out.write(template.render(template_values))
        
            
    @login_required
    def post(self, id):
                
        all_answers = self.request.get_all('answer[]')
        
        
        q_id = self.request.get('q_id')
        
        question = models.Question.get_item(q_id)
        
        add = False
                
        for item in all_answers:
        
            answer_id = models.Answer.get_item(item)
            question_id = answer_id.question_id
                    
            logging.info("Question: %s \t Answer: %s", question_id.id, item)        
        
            params = {                    
                        'question_id': question_id,
                        'answer_id': answer_id,
                        'user_id': self.request.user_id
                      }  
            #new_vote = models.Vote.create(params)
            
            if item in ["1003", "1004", "1005", "1016", "1017", "1018"]:
                add = True
                self.redirect("/vote/" + question.additional.id + "/")
                return
        
        if add:
            question = question.next
        
        #self.response.out.write("ok")                
        
        self.get(question.next.id)



    
    
def create(question = "", answers = [], multiple = False, additional = None):
        
    params = {
                'name': question,
                'multiple': multiple,
                'order': 0,
                'additional': additional               
                
              }    
              
    new_question = models.Question.create(params)
    
    
    for item in answers:
    
        params = {
                    'name': item,
                    'question_id': new_question,
                    'order': 0
                  }  
            
        new_answer = models.Answer.create(params)
    
    return new_question.key()
    
    

class Create(webapp2.RequestHandler):
  def get(self):
  
    
    
    key = create( question = u"Что Вы думаете о качестве обслуживания в целом?",
            answers  = [u"Отлично", u"Хорошо", u"Могло бы быть лучше", u"Плохо", u"Ужасно"],
            multiple = False )
    
    
    #key = models.Question.get_item("1001").key()
                
    key = create( question = u"Что именно Вас не устроило в обслуживании?",
            answers  = [u"Отношение продавца-консультанта", u"Качество обслуживания кассира", u"Охрана", u"Сотрудник банка", u"Старший продавец", u"Товаровед"],
            multiple = True,
            additional = key )            
           

    
    key = create( question = u"Смог ли продавец-консультант подобрать для Вас изделие?",
            answers  = [u"Да", u"Нет"])    


    key = create( question = u"Соорентировал ли Вас продавец-консультант по действующим акциям? Предложил ли дополнительные скидки?",
            answers  = [u"Да", u"Нет"])            
    
    
    key = create( question = u"Часто ли Вы посещаете магазин Ист-Нова?",
            answers  = [u"Постоянный клиент", u"Часто", u"Изредка", u"Впервые"])    
    
    
    key = create( question = u"Как часто Вы уходите из нашего магазина с покупкой?",
            answers  = [u"Всегда", u"Иногда", u"Изредка"],
            additional = key )      
        
    
    key = create( question = u"Как Вы оцениваете разнообразие моделей и размерного ряда представленного в магазине Ист-Нова товара?",
            answers  = [u"Отличный выбор", u"Неплохой ассортимент", u"Бывало лучше", u"В других магазинах лучше (больше)"]) 
            
    key = create( question = u"Что Вы думаете о ценах на товар в магазине Ист-Нова?",
            answers  = [u"Низкие", u"Приемлемые", u"Дорогие", u"Неоправданно высокие"])

    key = create( question = u"Считаю Вам необходимо обратить внимание на ...",
            answers  = [u"Поведение продавцов-консультантов", u"Поведение охраны"],
            multiple = True)                
    
    
    self.redirect('/')



app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/vote/(\d+)/', Vote),
  ('/stat', Stat),
  ('/create', Create),
  ('/order', Order)
  
], debug=True)
