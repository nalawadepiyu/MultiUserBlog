import os
import jinja2
import re
import webapp2
from string import letters
from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__),'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
autoescape = True)

def render_str(template , **params):
    t = jinja_env.get_template(template)
    return t.render(params)

class BlogHandler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

class MainPage(BlogHandler):
    def get(self):
        self.write('Hello Udacity!')

def blog_key(name = 'default'):
    return db.Key.from_path('blogs',name)

class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add =True)
    last_modified = db.DateTimeProperty(auto_now_add = True)

    def render(self):
        self._render_text = self.content.replace('\n','<br>')
        return render_str("post.html",p = self)

class BlogFront(BlogHandler):
    def  get(self):
        posts = Post.all().order('-created')
        self.render("front.html",posts = posts)

class PostPage(BlogHandler):
    def get(self , post_id):
        key = db.Key.from_path('Post',int(post_id) ,parent = blog_key())
        post = db.get(key)

        if not post:
            self.error(404)
            return

        self.render("permalink.html", post = post)

class NewPost(BlogHandler):
    def get(self):
        self.render("newpost.html")

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        if subject and content:
            p = Post(parent = blog_key(), subject = subject ,content = content)
            p.put()
            self.redirect('/blog/%s' %str(p.key().id()))
        else:
            error = "subject and content please!"
            self.render("newpost.html" ,subject=subject ,content = content ,error=error)







USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
def valid_username(username):
    return username and USER_RE.match(username)

PASS_RE = re.compile(r"^.{3,20}$")
def  valid_password(password):
    return password and PASS_RE.match(password)

EMAIL_RE = re.compile(r'^[\S]+@[\S]+\.[\S]+$')
def valid_email(email):
    return not email or EMAIL_RE.match(email)



class Signup(BlogHandler):
    def get(self):
        self.render("signup-form.html")

    def post(self):
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username = username ,email = email)

        if not valid_username(username):
            params['error_username'] = "That is not a valid username. "
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That is not a valid password. "
            have_error = True
        elif password != verify:
            params['error_verify'] = "Your passwords did not match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That is not a valid email. "
            have_error = True

        if have_error:
            self.render('signup-form.html' , **params)
        else:
            self.redirect('/welcome?username='+ username)


class Welcome(BlogHandler):
    def get(self):
        username = self.request.get('username')
        if valid_username(username):
            self.render('welcome.html' ,username = username)
        else:
            self.redirect('/signup')


app = webapp2.WSGIApplication([
    ('/',MainPage),
    ('/signup',Signup),
    ('/welcome' ,Welcome),
    ('/blog/?' ,BlogFront),
    ('/blog/([ 0-9]+)', PostPage),
    ('/blog/newpost',NewPost)],
debug = True)
