from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
import requests
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///wirip.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Custom Jinja2 filter for line breaks
@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convert newlines to HTML line breaks"""
    if not text:
        return text
    return text.replace('\n', '<br>\n')

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_writer = db.Column(db.Boolean, default=False)
    writer_request_pending = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    posts = db.relationship('Post', backref='author', lazy=True)
    votes = db.relationship('Vote', backref='user', lazy=True)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    posts = db.relationship('Post', backref='category', lazy=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.String(300))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    date_published = db.Column(db.DateTime)
    is_approved = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    votes = db.relationship('Vote', backref='post', lazy=True, cascade='all, delete-orphan')
    
    @property
    def upvotes(self):
        return Vote.query.filter_by(post_id=self.id, is_upvote=True).count()
    
    @property
    def downvotes(self):
        return Vote.query.filter_by(post_id=self.id, is_upvote=False).count()
    
    @property
    def score(self):
        return self.upvotes - self.downvotes

class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    is_upvote = db.Column(db.Boolean, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)

# Admin required decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Writer required decorator
def writer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not (current_user.is_writer or current_user.is_admin):
            flash('You need writer privileges to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    # Get approved and published posts
    posts = Post.query.filter_by(is_approved=True, is_published=True).order_by(Post.date_published.desc()).limit(10).all()
    
    # Get Billboard articles (mock data for now)
    billboard_articles = get_billboard_articles()
    
    return render_template('home.html', posts=posts, billboard_articles=billboard_articles)

@app.route('/blogs')
def blogs():
    category_filter = request.args.get('category')
    sort_by = request.args.get('sort', 'date')
    
    query = Post.query.filter_by(is_approved=True, is_published=True)
    
    if category_filter:
        query = query.join(Category).filter(Category.name == category_filter)
    
    if sort_by == 'popularity':
        # Sort by score (upvotes - downvotes)
        posts = sorted(query.all(), key=lambda x: x.score, reverse=True)
    else:
        posts = query.order_by(Post.date_published.desc()).all()
    
    categories = Category.query.all()
    return render_template('blogs.html', posts=posts, categories=categories, 
                         current_category=category_filter, current_sort=sort_by)

@app.route('/blog/<int:post_id>')
def blog_detail(post_id):
    post = Post.query.get_or_404(post_id)
    if not post.is_approved or not post.is_published:
        flash('Blog post not found.', 'error')
        return redirect(url_for('home'))
    
    user_vote = None
    if current_user.is_authenticated:
        user_vote = Vote.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    return render_template('blog_detail.html', post=post, user_vote=user_vote)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@app.route('/profile')
@login_required
def profile():
    user_posts = Post.query.filter_by(author_id=current_user.id).order_by(Post.date_created.desc()).all()
    return render_template('profile.html', user_posts=user_posts)

@app.route('/join-crew')
def join_crew():
    return render_template('join_crew.html')

@app.route('/request-writer', methods=['POST'])
@login_required
def request_writer():
    if current_user.is_writer:
        flash('You are already a writer!', 'info')
        return redirect(url_for('profile'))
    
    if current_user.writer_request_pending:
        flash('Your writer request is already pending approval.', 'info')
        return redirect(url_for('profile'))
    
    current_user.writer_request_pending = True
    db.session.commit()
    
    flash('Your writer request has been submitted and is pending approval.', 'success')
    return redirect(url_for('profile'))

@app.route('/create-post', methods=['GET', 'POST'])
@writer_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        summary = request.form['summary']
        category_id = request.form['category_id']
        
        post = Post(
            title=title,
            content=content,
            summary=summary,
            author_id=current_user.id,
            category_id=category_id
        )
        db.session.add(post)
        db.session.commit()
        
        flash('Your post has been submitted for review.', 'success')
        return redirect(url_for('profile'))
    
    categories = Category.query.all()
    return render_template('create_post.html', categories=categories)

@app.route('/vote', methods=['POST'])
@login_required
def vote():
    post_id = request.json.get('post_id')
    is_upvote = request.json.get('is_upvote')
    
    # Check if user already voted on this post
    existing_vote = Vote.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_vote:
        if existing_vote.is_upvote == is_upvote:
            # Remove vote if clicking the same vote again
            db.session.delete(existing_vote)
        else:
            # Change vote
            existing_vote.is_upvote = is_upvote
    else:
        # Create new vote
        vote = Vote(user_id=current_user.id, post_id=post_id, is_upvote=is_upvote)
        db.session.add(vote)
    
    db.session.commit()
    
    # Return updated vote counts
    post = Post.query.get(post_id)
    return jsonify({
        'upvotes': post.upvotes,
        'downvotes': post.downvotes,
        'score': post.score
    })

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    pending_posts = Post.query.filter_by(is_approved=False).order_by(Post.date_created.desc()).all()
    writer_requests = User.query.filter_by(writer_request_pending=True).all()
    stats = {
        'total_users': User.query.count(),
        'total_posts': Post.query.filter_by(is_approved=True, is_published=True).count(),
        'pending_posts': len(pending_posts),
        'writer_requests': len(writer_requests)
    }
    return render_template('admin/dashboard.html', pending_posts=pending_posts, 
                         writer_requests=writer_requests, stats=stats)

@app.route('/admin/approve-post/<int:post_id>')
@admin_required
def approve_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.is_approved = True
    post.is_published = True
    post.date_published = datetime.utcnow()
    db.session.commit()
    
    flash(f'Post "{post.title}" has been approved and published.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject-post/<int:post_id>')
@admin_required
def reject_post(post_id):
    post = Post.query.get_or_404(post_id)
    db.session.delete(post)
    db.session.commit()
    
    flash('Post has been rejected and deleted.', 'info')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/approve-writer/<int:user_id>')
@admin_required
def approve_writer(user_id):
    user = User.query.get_or_404(user_id)
    user.is_writer = True
    user.writer_request_pending = False
    db.session.commit()
    
    flash(f'{user.username} has been approved as a writer.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject-writer/<int:user_id>')
@admin_required
def reject_writer(user_id):
    user = User.query.get_or_404(user_id)
    user.writer_request_pending = False
    db.session.commit()
    
    flash(f'{user.username}\'s writer request has been rejected.', 'info')
    return redirect(url_for('admin_dashboard'))

# Helper function to get Billboard articles (mock for now)
def get_billboard_articles():
    # In a real implementation, you would fetch from Billboard's API or RSS feed
    return [
        {
            'title': 'Top Rap Songs This Week',
            'summary': 'Billboard\'s latest rap chart featuring the hottest tracks...',
            'url': '#',
            'date': 'October 1, 2025'
        },
        {
            'title': 'Drake\'s New Album Breaks Records',
            'summary': 'The latest release from Drake has shattered streaming records...',
            'url': '#',
            'date': 'September 30, 2025'
        },
        {
            'title': 'Emerging Rap Artists to Watch',
            'summary': 'Discover the next generation of rap talent making waves...',
            'url': '#',
            'date': 'September 29, 2025'
        }
    ]

# Initialize database
def init_db():
    with app.app_context():
        db.create_all()
        
        # Create default categories
        if not Category.query.first():
            categories = ['News', 'Album Review', 'Song Review', 'Discover New Artist']
            for cat_name in categories:
                category = Category(name=cat_name)
                db.session.add(category)
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@wirip.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True,
                is_writer=True
            )
            db.session.add(admin)
            
            db.session.commit()
            print("Database initialized with default data!")

if __name__ == '__main__':
    print("🎵 Initializing WiRiP Blog...")
    init_db()
    print("🚀 Starting WiRiP Blog server...")
    print("📍 Access your blog at: http://localhost:5000")
    print("👤 Default admin login: admin / admin123")
    print("⚠️  Remember to change the admin password!")
    app.run(debug=True, host='0.0.0.0', port=5000)