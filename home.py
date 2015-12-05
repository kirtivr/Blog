import webapp2
import os
import jinja2
import random
import re
import urllib2
import logging
from google.appengine.ext import ndb

permalinks=[];
posts=None
post_ancestor_key="12345"
user_ancestor_key="12567"
def newpost_key(post_ancestor_key):
    return ndb.Key('Blog',post_ancestor_key)

def newuser_key(user_ancestor_key):
    return ndb.Key('User',user_ancestor_key)

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    pointer=User.query(ancestor=newuser_key(user_ancestor_key))
    results=pointer.fetch(projection=[User.username])
    username_already_exists=False
    for result in results:
        if result.username==username:
            username_already_exists=True
    return username and USER_RE.match(username) and not username_already_exists
        
PASS_RE = re.compile(r"^.{3,20}$")
def valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE  = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)

def verify_user_pass(username,password):
    pointer=User.query(User.username==username,ancestor=newuser_key(user_ancestor_key))
    results=pointer.fetch(1)
    if results[0].password==password:
        return True
    else:    
        return False

class User(ndb.Model):
    username=ndb.StringProperty(required=True)
    password=ndb.StringProperty(required=True)
    email=ndb.StringProperty()


class Blog(ndb.Model):
    subject = ndb.StringProperty(required = True)
    content = ndb.TextProperty(required = True)
    permalink=ndb.IntegerProperty(required = True)
    created = ndb.DateTimeProperty(auto_now_add = True)

# class GiveStyle(Handler):
#     def get(self):
#         self.

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)
    def render_str(self,template_dir, template, **params):
        template_dir=os.path.join(os.path.dirname(__file__),template_dir)
        jinja_env=jinja2.Environment(loader= jinja2.FileSystemLoader(template_dir), autoescape=True)
        t = jinja_env.get_template(template)
        return t.render(params)
    def render(self,template_dir, template, **kw):
        self.write(self.render_str(template_dir,template, **kw))
    

class MainPage(Handler):
    def get(self):
       # logging.debug("testing if logging works")
        self.write('Hello Udacity!')
   

class BlogPage(Handler):
    def get(self):
        permalink=self.request.get('permalink');
        if permalink:
            blog_query=Blog.query(ancestor=newpost_key(post_ancestor_key)).order(-Blog.created)
            blogposts=blog_query.fetch(10)
            for post in blogposts:
                if permalink==str(post.permalink):
                    self.render(os.path.join("templates","blog"),"postshow.html",subject=post.subject,content=post.content,permalink=post.permalink,created=post.created)
                    break;
        else:
            blog_query=Blog.query(ancestor=newpost_key(post_ancestor_key)).order(-Blog.created)
            posts=blog_query.fetch(10)
            self.render(os.path.join("templates","blog"),"blog1.html",posts=posts);

class NewPost(Handler):
    
    def get(self):
        self.render(os.path.join("templates","blog"),"newpost.html");
    def post(self):
        subject=self.request.get("subject");
        content=self.request.get("content");

        if subject and content:
            permalink=0;    
            while 1:
                permalink=self.get_random();
                if permalink not in permalinks :
                    permalinks.append(permalink)
                    b=Blog(parent=(newpost_key(post_ancestor_key)));
                    b.subject=subject;
                    b.content=content;
                    b.permalink=permalink;
                    b.put();
                    break;
                if permalinks.length ==9999:
                    self.write("Cannot post new entries as permalink range is exhausted. Contact the admin about increasing this range")
                    break;
            plink_param=urllib.urlencode({'permalink':permalink});
            self.redirect('/blog?'+plink_param)
        else:
            self.render(os.path.join("templates","blog","newpost"),"newpost.html",subject=subject,content=content)
    def get_random(self):
        return random.randrange(1,9999);

class SignUp(Handler):
    def get(self):
        self.render(os.path.join("templates","blog","signup"),"signup-form.html")
    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username,
                      email = email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That wasn't a valid password."
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True


        if not have_error:
            self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % str(username))
            new_user=User(parent=(newuser_key(user_ancestor_key)))
            new_user.username=username
            new_user.password=password
            if email:
                new_user.email=email
            else:
                new_user.email="anonymous@somerussianwebsite.ru"
            new_user.put()
            self.redirect('/blog/welcome')
        else:
            self.render(os.path.join("templates","blog","signup"),"signup-form.html",**params)

class Login(Handler):
    def get(self):
        self.render(os.path.join("templates","blog"),"login.html")
    def post(self):
        username=self.request.get('username')
        password=self.request.get('password')
        if verify_user_pass(username,password):
            self.response.headers.add_header('Set-Cookie', 'name=%s; Path=/' % str(username))
            self.redirect('/blog/welcome')
        else:
            params=dict(invalid_login="Invalid login")
            self.render(os.path.join("templates","blog"),"login.html",**params)

class Logout(Handler):
    def get(self):
        user=self.request.cookies.get('name')
        self.response.headers.add_header('Set-Cookie', 'name=; Path=/')
        self.redirect('/blog/signup')




        

        




class Welcome(Handler):
    def get(self):
        username=self.request.cookies.get('name')
        if username:
            self.render(os.path.join("templates","blog"),"welcome.html",username=username)
        else:
            self.render(os.path.join("templates","blog","signup"),"signup-form.html")


app = webapp2.WSGIApplication([(r'/', MainPage),(r'/blog',BlogPage),(r'/blog?permalink=[0-9]+',BlogPage),
                                (r'/blog/newpost.*',NewPost),(r'/blog/signup',SignUp),(r'/blog/welcome',Welcome),(r'/blog/login',Login),(r'/blog/logout',Logout)], debug=True)