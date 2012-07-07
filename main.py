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

import cgi
import datetime
import webapp2

import jinja2
import os
import logging

import models

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


from google.appengine.ext import db
from google.appengine.api import users

class Greeting(db.Model):
    author = db.UserProperty()
    content = db.StringProperty(multiline=True)
    date = db.DateTimeProperty(auto_now_add=True)




class MainPage(webapp2.RequestHandler):
    def get(self):
        
        login_url = users.create_login_url(self.request.uri)
        logout_url = users.create_logout_url(self.request.uri)
        



        google_user = users.get_current_user()
        
        if not google_user:
            return self.redirect(login_url)
            
        user_id = google_user.user_id()
        user = models.User.get_item(user_id)
        if user is None:
            user = models.User(key_name=str(google_user.user_id()), id=str(google_user.user_id()),
                name=google_user.email())
            user.put()
            user = models.User.get_item(google_user.user_id())  
         
        
        all_questions = models.Question.all().fetch(100)
        
        last = None
        first = None
        
        for item in all_questions:

            item.answers = models.Answer.gql("WHERE question_id = :1", item).fetch(100)
            
            if last: 
                last.next = item.id
                item.prev =  last.id
            else:
                first = item.id
                
            last = item
        
        
         
        template_values = {            
            'login_url': login_url,
            'logout_url': logout_url,        
            'all_questions': all_questions,
            'first': first,    
        }    
            
        template = jinja_environment.get_template('templates/index.html')
        self.response.out.write(template.render(template_values))




class MainPage2(webapp2.RequestHandler):
  def get(self):
    self.response.out.write('<html><body>')

    greetings = db.GqlQuery("SELECT * "
                            "FROM Greeting "
                            "ORDER BY date DESC LIMIT 10")

    for greeting in greetings:
      if greeting.author:
        self.response.out.write('<b>%s</b> wrote:' % greeting.author.nickname())
      else:
        self.response.out.write('An anonymous person wrote:')
      self.response.out.write('<blockquote>%s</blockquote>' %
                              cgi.escape(greeting.content))


    self.response.out.write("""
          <form action="/sign" method="post">
            <div><textarea name="content" rows="3" cols="60"></textarea></div>
            <div><input type="submit" value="Sign Guestbook"></div>
          </form>
        </body>
      </html>""")


class Guestbook(webapp2.RequestHandler):
  def post(self):
    greeting = Greeting()

    if users.get_current_user():
      greeting.author = users.get_current_user()

    greeting.content = self.request.get('content')
    greeting.put()
    self.redirect('/')
    
    
    
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
  ('/sign', Guestbook),
  ('/create', Create)
], debug=True)
