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
        
        #if google_user.email() == "nikita.grachev@gmail.com":
        #    user_id = "107581787154497832805" 
        #elif not google_user.email().endswith("ist-nova.ru"):
        #    return args[0].redirect(login_url)
        
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
        
        all_questions = models.Question.gql("WHERE enabled=True Order by order asc").fetch(100)
                       
        logout_url = users.create_logout_url("/")
         
        template_values = {                        
            'logout_url': logout_url,
            'user_id': self.request.user_id,
            'all_questions': all_questions,
            'is_main': True
        }    
        
        '''
        u = models.User.get_item("101218544535968046707")
        u.city = u"Тюмень"
        u.put()
        '''
           
        template = jinja_environment.get_template('templates/index.html')
        self.response.out.write(template.render(template_values))



class City(webapp2.RequestHandler):
    
    @login_required
    def get(self):
    
        all_users = models.User.gql("Order by id asc").fetch(100)                   
        
        if self.request.user_id.name != "novosibirsk@ist-nova.ru":
            all_users = [self.request.user_id]
        
        
        template_values = {                        
            'logout_url': self.request.logout_url,
            'user_id': self.request.user_id,
            'all_users': all_users,            
        }    
            
        template = jinja_environment.get_template('templates/city.html')
        self.response.out.write(template.render(template_values))
        

class End(webapp2.RequestHandler):
    
    @login_required
    def get(self):
           
        
        template_values = {                        
            'logout_url': self.request.logout_url,
            'user_id': self.request.user_id

        }    
            
        template = jinja_environment.get_template('templates/end.html')
        self.response.out.write(template.render(template_values))        
        


class Stat(webapp2.RequestHandler):
    
    @login_required
    def get(self, id):
    
        user = models.User.get_item(id)
        
        logging.info(user.name)
        
        
        first = models.Question.get_item("1001")
        total = models.Vote.gql("WHERE question_id = :1 and user_id =:2",
                                             first, user).count() + 5
        
        
                         
        all_questions = models.Question.gql("WHERE enabled=True Order by order asc").fetch(100)
        
        
        for item in all_questions:
            
            item.answers = models.Answer.gql("WHERE question_id = :1 ORDER by id asc", item).fetch(100)
            
            for value in item.answers:
                value.votes = models.Vote.gql("WHERE answer_id = :1 and user_id =:2 ORDER by id asc",
                                             value, user).count() + 1#random.randint(10, 1000)                
                
                #logging.info("%s : %s", value.votes, 	value.name)
        

        template_values = {                        
            'logout_url': self.request.logout_url,
            'user_id': self.request.user_id,
            'stat_user': self.request.user_id,            
            'all_questions': all_questions,
            'is_stat': True,
            'total': total
            
        }    
            
        template = jinja_environment.get_template('templates/stat.html')
        self.response.out.write(template.render(template_values))



class Order(webapp2.RequestHandler):
        
    def get(self):
                
        last = None
        
        questions = ["1001", "1009", "1007", "1008", "1004", "1005", "1006", "1010"] 
 
  
        order = 1       
        
        for value in questions:                                            
   
            item = models.Question.get_item(value)
            
            
            if value in ["1002", "1003"]:
                item.enabled = False
            
            
            if value in ["1002", "1006", "1009"]:
                item.is_additional = True
    
            item.order = order
            order += 1
                 
            item.put()          
        
        
        questions = models.Question.gql("WHERE enabled=True Order by order asc").fetch(100)
                
        for item in questions:            
            item.prev = last
            
            if last and last.is_additional:
                item.prev = last.prev
            
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
        
        
        prev_id = None
        
        #if question.prev:
        #    prev_id = question.prev.id
            
        #logging.info(self.request.headers['Referer'])
        
        #if question.id in ["1003", "1007"]:
        #    prev_id = question.prev.prev.id
             
        #prev_id = self.request.headers['Referer']
       
        if question.prev:
            prev_id = "/vote/" + question.prev.id + "/"
        
        
        next_id = question.id
        
        if question.next:
            next_id = question.next.id
        
        
        answers = models.Answer.gql("WHERE question_id = :1", question).fetch(100)
                                    
        template_values = {                        
            'logout_url': self.request.logout_url,
            'user_id': self.request.user_id,        
            'question': question,
            'answers': answers,
            'prev_id': prev_id,
            'next_id': next_id
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
            new_vote = models.Vote.create(params)
            
            if item in ["1003", "1004", "1005", "1016", "1017", "1018"]:
                add = True
                self.redirect("/vote/" + question.next.id + "/")
                return
        
        if add:
            question = question.next
        
        
        if not question.next:
            self.redirect("/end")
            return
      
      
        if question.id in ["1001", "1005"]:
            question = question.next
  
            
        #self.response.out.write("ok")   
        #self.response.out.write("ok")                
        
        self.redirect("/vote/" + question.next.id + "/")



    
    
def create(question = "", answers = [], multiple = False, additional = None):
        
    params = {
                'name': question,
                'multiple': multiple,
                'order': 0,
                'additional': additional,               
                'enabled': True
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
    
    
    
    
def edit(question_id = "", answers = []):
    
              
    new_question = models.Question.get_item(question_id)
    
    
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
  
    '''
    
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


    key = create( question = u"Соориентировал ли Вас продавец-консультант по действующим акциям? Предложил ли дополнительные скидки?",
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
            answers  = [u"Работу продавцов-консультантов", u"Работу охраны"],
            multiple = True)                
    
    
    '''
    
    
 
    key = create( question = u"Отметьте из каких источников информации Вы узнали о магазине Ист-Нова (или о действующих скидках)?",
            answers  = [u"ТВ", u"Радио", u"Интернет", u"Наружная реклама", u"Другое"],
            multiple = True)       
            

    
    edit(question_id = "1009", answers  = [u"Работу администратора торгового зала", u"Работу старшего продавца", u"Работу кассира", u"Работу сотрудника банка"])
        
     
     
    self.redirect('/')



app = webapp2.WSGIApplication([
  ('/', MainPage),
  ('/vote/(\d+)/', Vote),
  ('/city', City),
  ('/stat/(\d+)/', Stat),
  ('/create', Create),
  ('/order', Order),
  ('/end', End)
  
], debug=True)
