# Copyright 2009 Google Inc.
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

import logging

from google.appengine.api import memcache
from google.appengine.ext import db



class CustomModel(db.Model):
    
    id = db.StringProperty(required=True)    
    created  = db.DateTimeProperty(auto_now_add=True)
    
    @classmethod
    def get_item(self, item):        

        if item is None:
            return None
        
        key_name = self.__name__ + "_" + str(item)        
        value = self.get_by_key_name(key_name)
                 
                
        if value is not None:
            return value
        else:
            value = self.gql("WHERE id = :1", str(item)).get()
            #logging.info("Value: %s\t%s",value, item)
            
            if value is None:
                logging.warning("Error get DB item: %s", key_name)
                return None
        
            return value           
            
            
    @classmethod 
    def create(self, params):
        key_name = self.__name__ + "_last"
        
        if memcache.get(key = key_name):
            value = memcache.incr(key = key_name)
            
        else:
            last = self.all().order('-created').get()
            try:#if last.id:
                value = int(last.id) + 1
                logging.warning("Memcache Counter from DataBase for: %s\t%s", key_name, value)
            except:#else:
                value = 1001
                logging.error("Memcache Counter from DataBase for: %s\t%s", key_name, value)
            if not memcache.set(key = key_name, value = value, time = 0):#CACHE_EXPIRES):
                logging.error("Memcache set failed.")
            
            
        key_name = self.__name__ + "_" + str(value)            
            
        params["id"] = str(value)
        params["key_name"] = key_name
        
        new_ref = self(**params)
        new_ref.put()
        return new_ref  

               
            
class User(CustomModel):

    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=False)
    access_token = db.StringProperty(required=False)
    
                
                           
class Question(CustomModel):
    
    name = db.StringProperty(required=False)
    
    multiple = db.BooleanProperty(required=True)
    order = db.IntegerProperty(required=True)
    
    
    is_additional = db.BooleanProperty(required=False) 
    additional = db.SelfReferenceProperty(collection_name='question_additional', required=False)
    
    prev = db.SelfReferenceProperty(collection_name='question_prev', required=False)
    next = db.SelfReferenceProperty(collection_name='question_next', required=False)


class Answer(CustomModel):
    
    name = db.StringProperty(required=False)
    question_id = db.ReferenceProperty(Question, collection_name='question_answers', required=True)
    
    order = db.IntegerProperty(required=True)
    
    
class Vote(CustomModel):
        
    question_id = db.ReferenceProperty(Question, collection_name='question_votes', required=True)
    answer_id   = db.ReferenceProperty(Answer,   collection_name='answer_votes', required=True) 
    
    user_id  = db.ReferenceProperty(User, collection_name='user_votes', required=True)
    
                


    
