# WiRiP Architecture & Deployment Guide

Complete technical documentation explaining how WiRiP works, its architecture, and deployment process.

---

## Table of Contents
1. [Project Overview](#project-overview)
2. [Application Architecture](#application-architecture)
3. [Code Structure & Flow](#code-structure--flow)
4. [Database Design](#database-design)
5. [Authentication System](#authentication-system)
6. [Routing & Views](#routing--views)
7. [Frontend Architecture](#frontend-architecture)
8. [Deployment Architecture](#deployment-architecture)
9. [Production Stack](#production-stack)
10. [Security Implementation](#security-implementation)

---

## Project Overview

**WiRiP** (What is Right in Politics) is a Flask-based blog platform for political discourse where users can:
- Create and publish blog posts
- Categorize content (Politics, Economy, Social Issues, etc.)
- Vote on posts (upvote/downvote)
- Comment and engage with content
- Manage user profiles with avatars

**Tech Stack:**
- **Backend:** Flask 2.3.3 (Python web framework)
- **Database:** SQLite (development) / PostgreSQL (production-ready)
- **ORM:** SQLAlchemy (database abstraction)
- **Authentication:** Flask-Login (session management)
- **Frontend:** Bootstrap 5, Jinja2 templates
- **Production Server:** Gunicorn (WSGI) + Nginx (reverse proxy)

---

## Application Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      User's Browser                     │
│              (HTML/CSS/JavaScript/Bootstrap)            │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/HTTPS
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Port 80/443)                  │
│         - Serves static files (CSS, JS, images)         │
│         - Reverse proxy to Gunicorn                     │
│         - SSL termination (if HTTPS enabled)            │
└────────────────────────┬────────────────────────────────┘
                         │ Unix Socket
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Gunicorn WSGI Server (3 workers)           │
│         - Handles concurrent requests                   │
│         - Manages Flask app instances                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   Flask Application                     │
│  ┌──────────────────────────────────────────────────┐   │
│  │           app.py (Main Application)              │   │
│  │  - Route definitions (@app.route)                │   │
│  │  - Request/Response handling                     │   │
│  │  - Template rendering (Jinja2)                   │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────┴───────────────────────────────┐   │
│  │         Flask-Login (Session Manager)            │   │
│  │  - current_user object                           │   │
│  │  - @login_required decorator                     │   │
│  │  - Session cookies                               │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────┴───────────────────────────────┐   │
│  │       Flask-SQLAlchemy (ORM Layer)               │   │
│  │  - Models: User, Post, Category, Vote            │   │
│  │  - Query builder                                 │   │
│  │  - Relationship management                       │   │
│  └──────────────────┬───────────────────────────────┘   │
└────────────────────┬┴───────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│              SQLite Database (wirip.db)                 │
│  - users table                                          │
│  - posts table                                          │
│  - categories table                                     │
│  - votes table                                          │
└─────────────────────────────────────────────────────────┘
```

---

## Code Structure & Flow

### Project Directory Structure

```
WiRiP/
├── app.py                 # Main application file (routes, models, logic)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (SECRET_KEY, DATABASE_URL)
├── wirip.db              # SQLite database file (created at runtime)
│
├── static/               # Static assets (served by Nginx in production)
│   ├── css/
│   │   └── style.css     # Custom styles (dark theme, pink accents)
│   ├── js/
│   │   └── main.js       # Client-side JavaScript (vote handling, etc.)
│   ├── images/           # User avatars, logos
│   └── logo.png          # WiRiP logo
│
└── templates/            # Jinja2 HTML templates
    ├── base.html         # Master template (navbar, footer, scripts)
    ├── home.html         # Homepage (hero section, featured posts)
    ├── login.html        # Login form
    ├── register.html     # User registration
    ├── create_post.html  # Blog post editor
    ├── post.html         # Single post view (with comments)
    ├── profile.html      # User profile & settings
    ├── category.html     # Posts filtered by category
    └── admin.html        # Admin dashboard
```

---

## Database Design

### Entity Relationship Diagram

```
┌─────────────────┐          ┌──────────────────┐
│      User       │          │    Category      │
├─────────────────┤          ├──────────────────┤
│ id (PK)         │          │ id (PK)          │
│ username        │          │ name             │
│ email           │          │ slug             │
│ password_hash   │          │ description      │
│ is_admin        │          └──────────────────┘
│ avatar          │                   │
│ bio             │                   │
│ created_at      │                   │
└────────┬────────┘                   │
         │                            │
         │ 1                          │
         │                            │
         │ N                          │ 1
         │                            │
         │                            │
┌────────┴────────┐                   │
│      Post       │                   │
├─────────────────┤                   │
│ id (PK)         │                   │
│ title           │                   │
│ slug            │                   │
│ content         │                   │
│ author_id (FK)  │───────────────────┘
│ category_id (FK)│
│ featured_image  │
│ upvotes         │
│ downvotes       │
│ views           │
│ created_at      │
│ updated_at      │
└────────┬────────┘
         │
         │ 1
         │
         │ N
         │
┌────────┴────────┐
│      Vote       │
├─────────────────┤
│ id (PK)         │
│ user_id (FK)    │
│ post_id (FK)    │
│ vote_type       │ (1 = upvote, -1 = downvote)
│ created_at      │
└─────────────────┘
```

### Table Definitions (SQLAlchemy Models)

#### User Model
```python
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    avatar = db.Column(db.String(255), default='default-avatar.png')
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    posts = db.relationship('Post', backref='author', lazy=True)
    votes = db.relationship('Vote', backref='user', lazy=True)
```

**Key Features:**
- `UserMixin`: Provides Flask-Login required methods (`is_authenticated`, `get_id()`)
- `password_hash`: Werkzeug hashed password (never stores plain text)
- `is_admin`: Boolean flag for admin privileges
- **Relationships:** One user → many posts, one user → many votes

#### Post Model
```python
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    featured_image = db.Column(db.String(255))
    upvotes = db.Column(db.Integer, default=0)
    downvotes = db.Column(db.Integer, default=0)
    views = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    votes = db.relationship('Vote', backref='post', lazy=True, cascade='all, delete-orphan')
```

**Key Features:**
- `slug`: URL-friendly version of title (e.g., "my-post-title")
- `upvotes/downvotes`: Cached vote counts (for performance)
- `cascade='all, delete-orphan'`: Delete all votes when post is deleted
- **Foreign Keys:** Links to User (author) and Category

#### Category Model
```python
class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    slug = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    posts = db.relationship('Post', backref='category', lazy=True)
```

**Default Categories:**
- Politics, Economy, Social Issues, Environment, Technology, International

#### Vote Model
```python
class Vote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    vote_type = db.Column(db.Integer, nullable=False)  # 1 or -1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Composite unique constraint (one vote per user per post)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)
```

**Key Features:**
- `vote_type`: 1 (upvote) or -1 (downvote)
- **Unique Constraint:** User can only vote once per post (can change vote)

---

## Authentication System

### How Flask-Login Works

```
┌──────────────────────────────────────────────────────────┐
│                    User Login Flow                       │
└──────────────────────────────────────────────────────────┘

1. User submits login form (username + password)
                    ↓
2. Flask receives POST /login
                    ↓
3. Query User table: User.query.filter_by(username=...).first()
                    ↓
4. Verify password: check_password_hash(user.password_hash, form_password)
                    ↓
5. If valid: login_user(user, remember=True)
                    ↓
6. Flask-Login creates session cookie (encrypted with SECRET_KEY)
                    ↓
7. Browser stores cookie, sends with every request
                    ↓
8. Flask-Login loads user from session: current_user object available
```

### Key Code Components

#### User Loader (Required by Flask-Login)
```python
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
```
- Called on every request to load user from session
- Returns `current_user` object (accessible in routes & templates)

#### Login Route
```python
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)  # Create session
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'danger')
    
    return render_template('login.html')
```

#### Protected Routes
```python
@app.route('/create_post')
@login_required  # Decorator: redirects to login if not authenticated
def create_post():
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    # Only admins can create posts
    return render_template('create_post.html')
```

#### Password Hashing (Security)
```python
from werkzeug.security import generate_password_hash, check_password_hash

# On registration:
password_hash = generate_password_hash('user_password', method='pbkdf2:sha256')

# On login:
is_valid = check_password_hash(stored_hash, submitted_password)
```

---

## Routing & Views

### Route Map

| Route | Method | Auth | Description |
|-------|--------|------|-------------|
| `/` | GET | No | Homepage (featured posts, recent posts) |
| `/login` | GET, POST | No | Login form |
| `/register` | GET, POST | No | User registration |
| `/logout` | GET | Yes | Logout (clear session) |
| `/post/<slug>` | GET | No | Single post view |
| `/category/<slug>` | GET | No | Posts by category |
| `/create_post` | GET, POST | Admin | Create new blog post |
| `/edit_post/<id>` | GET, POST | Admin | Edit existing post |
| `/delete_post/<id>` | POST | Admin | Delete post |
| `/profile` | GET, POST | Yes | User profile & settings |
| `/vote/<post_id>/<vote_type>` | POST | Yes | Upvote/downvote post (AJAX) |
| `/admin` | GET | Admin | Admin dashboard (stats, manage posts) |

### Request-Response Flow Example

**Example: Creating a New Post**

```
1. User (admin) navigates to /create_post
                    ↓
2. Browser sends: GET /create_post
                    ↓
3. Flask checks: @login_required → is user logged in?
                    ↓
4. Flask checks: current_user.is_admin → is user admin?
                    ↓
5. Flask renders: create_post.html template
                    ↓
6. User fills form (title, content, category, image)
                    ↓
7. Browser sends: POST /create_post (form data)
                    ↓
8. Flask receives POST data:
   - title = request.form.get('title')
   - content = request.form.get('content')
   - category_id = request.form.get('category')
   - image = request.files.get('featured_image')
                    ↓
9. Flask processes:
   - Generate slug: slugify(title) → "my-blog-post"
   - Save image: image.save('static/images/post_123.jpg')
   - Create Post object:
     post = Post(
         title=title,
         slug=slug,
         content=content,
         author_id=current_user.id,
         category_id=category_id,
         featured_image='post_123.jpg'
     )
                    ↓
10. Flask saves to DB:
    db.session.add(post)
    db.session.commit()
                    ↓
11. Flask redirects: redirect(url_for('post', slug=slug))
                    ↓
12. Browser navigates to /post/my-blog-post
                    ↓
13. New post is now live!
```

---

## Frontend Architecture

### Template Inheritance (Jinja2)

```
base.html (Master Template)
├── navbar (logo, links, user menu)
├── flash messages (alerts)
├── {% block content %} ← Child templates inject here
└── footer (copyright, social links)

Child Templates extend base.html:
- home.html extends base → adds hero section + post grid
- post.html extends base → adds single post content + comments
- profile.html extends base → adds user info + edit form
```

**Example: base.html Structure**
```html
<!DOCTYPE html>
<html>
<head>
    <title>{% block title %}WiRiP{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <!-- Navbar -->
    <nav class="navbar">
        <a href="{{ url_for('home') }}">
            <img src="{{ url_for('static', filename='logo.png') }}" alt="Logo">
        </a>
        {% if current_user.is_authenticated %}
            <a href="{{ url_for('profile') }}">Profile</a>
            <a href="{{ url_for('logout') }}">Logout</a>
        {% else %}
            <a href="{{ url_for('login') }}">Login</a>
        {% endif %}
    </nav>
    
    <!-- Flash Messages -->
    {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
            <div class="alert alert-{{ category }}">{{ message }}</div>
        {% endfor %}
    {% endwith %}
    
    <!-- Child Content -->
    {% block content %}{% endblock %}
    
    <!-- Footer -->
    <footer>&copy; 2025 WiRiP</footer>
    
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
```

### Dynamic Data in Templates

**Example: home.html**
```html
{% extends 'base.html' %}

{% block content %}
<div class="hero">
    <img src="{{ url_for('static', filename='logo.png') }}" class="home-logo">
    <h1>What is Right in Politics</h1>
</div>

<div class="posts-grid">
    {% for post in posts %}
    <div class="post-card">
        <img src="{{ url_for('static', filename='images/' ~ post.featured_image) }}">
        <h3><a href="{{ url_for('post', slug=post.slug) }}">{{ post.title }}</a></h3>
        <p>{{ post.content[:150] }}...</p>
        <div class="meta">
            <span>{{ post.author.username }}</span>
            <span>{{ post.upvotes - post.downvotes }} votes</span>
        </div>
    </div>
    {% endfor %}
</div>
{% endblock %}
```

**Flask passes data to template:**
```python
@app.route('/')
def home():
    posts = Post.query.order_by(Post.created_at.desc()).limit(10).all()
    return render_template('home.html', posts=posts)
```

### AJAX Vote System

**Client-Side (JavaScript):**
```javascript
function vote(postId, voteType) {
    fetch(`/vote/${postId}/${voteType}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        // Update vote count in UI
        document.getElementById(`votes-${postId}`).textContent = data.net_votes;
    });
}
```

**Server-Side (Flask):**
```python
@app.route('/vote/<int:post_id>/<int:vote_type>', methods=['POST'])
@login_required
def vote(post_id, vote_type):
    # Check if user already voted
    existing_vote = Vote.query.filter_by(user_id=current_user.id, post_id=post_id).first()
    
    if existing_vote:
        # Update vote
        existing_vote.vote_type = vote_type
    else:
        # Create new vote
        new_vote = Vote(user_id=current_user.id, post_id=post_id, vote_type=vote_type)
        db.session.add(new_vote)
    
    db.session.commit()
    
    # Recalculate vote counts
    post = Post.query.get(post_id)
    upvotes = Vote.query.filter_by(post_id=post_id, vote_type=1).count()
    downvotes = Vote.query.filter_by(post_id=post_id, vote_type=-1).count()
    
    post.upvotes = upvotes
    post.downvotes = downvotes
    db.session.commit()
    
    return jsonify({'net_votes': upvotes - downvotes})
```

---

## Deployment Architecture

### Production Environment on AWS EC2

```
┌────────────────────────────────────────────────────────────┐
│                     AWS EC2 Instance                       │
│                    (Ubuntu 22.04 LTS)                      │
│                      t2.micro (Free Tier)                  │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │              Nginx (Port 80/443)                 │     │
│  │  - Listens on public IP (50.17.157.218:80)      │     │
│  │  - Serves /static/ files directly               │     │
│  │  - Proxies dynamic requests to Gunicorn         │     │
│  └────────────┬─────────────────────────────────────┘     │
│               │ Unix Socket: /opt/wirip/wirip.sock        │
│               ↓                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │        Gunicorn (systemd service)                │     │
│  │  - 3 worker processes                            │     │
│  │  - Binds to Unix socket (not TCP port)          │     │
│  │  - Auto-restarts on failure                      │     │
│  │  - Managed by systemd (wirip.service)           │     │
│  └────────────┬─────────────────────────────────────┘     │
│               │                                            │
│               ↓                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │          Flask Application                       │     │
│  │  - Location: /opt/wirip/                        │     │
│  │  - Entry point: app.py                           │     │
│  │  - Environment: .env file                        │     │
│  │  - User: ubuntu                                  │     │
│  └────────────┬─────────────────────────────────────┘     │
│               │                                            │
│               ↓                                            │
│  ┌──────────────────────────────────────────────────┐     │
│  │         SQLite Database                          │     │
│  │  - File: /opt/wirip/wirip.db                    │     │
│  │  - Permissions: 644 (ubuntu:ubuntu)              │     │
│  └──────────────────────────────────────────────────┘     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Why This Architecture?

**Nginx (Reverse Proxy):**
- **Static File Serving:** Nginx is optimized for serving CSS/JS/images (faster than Flask)
- **Load Balancing:** Can distribute requests across multiple Gunicorn workers
- **SSL Termination:** Handles HTTPS certificates (Certbot integration)
- **Security:** Hides internal application structure, adds rate limiting

**Gunicorn (WSGI Server):**
- **Concurrency:** Multiple workers handle simultaneous requests (Flask dev server = 1 request at a time)
- **Stability:** Production-grade, handles long-running requests, timeouts
- **Process Management:** Auto-restarts workers if they crash
- **Unix Socket:** Faster than TCP for local communication (Nginx ↔ Gunicorn)

**Systemd Service:**
- **Auto-Start:** App starts automatically on server boot
- **Auto-Restart:** Restarts on crashes (Restart=on-failure)
- **Logging:** Centralized logs via `journalctl`
- **Environment Variables:** Loads `.env` file securely

---

## Production Stack

### 1. Systemd Service Configuration

**File:** `/etc/systemd/system/wirip.service`

```ini
[Unit]
Description=WiRiP Gunicorn Service
After=network.target  # Start after network is available

[Service]
User=ubuntu           # Run as ubuntu user (not root)
Group=www-data        # Nginx group for file permissions
WorkingDirectory=/opt/wirip
EnvironmentFile=/opt/wirip/.env  # Load environment variables
ExecStart=/usr/local/bin/gunicorn --workers 3 --bind unix:/opt/wirip/wirip.sock app:app
Restart=on-failure    # Auto-restart if crashes
RestartSec=5s         # Wait 5 seconds before restart

[Install]
WantedBy=multi-user.target  # Enable on system startup
```

**Key Parameters:**
- `--workers 3`: Runs 3 Gunicorn processes (recommended: 2-4 × CPU cores)
- `--bind unix:/opt/wirip/wirip.sock`: Creates Unix socket for Nginx communication
- `app:app`: Module name (app.py) : Flask app variable (app = Flask(__name__))

**Management Commands:**
```bash
sudo systemctl start wirip      # Start service
sudo systemctl stop wirip       # Stop service
sudo systemctl restart wirip    # Restart (after code changes)
sudo systemctl status wirip     # Check status
sudo systemctl enable wirip     # Enable auto-start on boot
sudo journalctl -u wirip -f     # View live logs
```

### 2. Nginx Configuration

**File:** `/etc/nginx/sites-available/wirip`

```nginx
server {
    listen 80;                 # Listen on HTTP port
    server_name _;             # Accept all hostnames (use domain in production)

    # Serve static files directly (bypass Flask)
    location /static/ {
        alias /opt/wirip/static/;
        expires 30d;           # Cache for 30 days
        add_header Cache-Control "public, immutable";
    }

    # Proxy all other requests to Gunicorn
    location / {
        proxy_pass http://unix:/opt/wirip/wirip.sock;  # Connect to Unix socket
        proxy_set_header Host $host;                    # Preserve original Host header
        proxy_set_header X-Real-IP $remote_addr;        # Client's real IP
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;  # Proxy chain
        proxy_set_header X-Forwarded-Proto $scheme;     # http or https
    }
}
```

**How It Works:**
1. User requests `http://50.17.157.218/static/css/style.css`
   - Nginx matches `/static/` location
   - Serves file directly from `/opt/wirip/static/css/style.css`
   - **No Flask/Gunicorn involvement** (faster!)

2. User requests `http://50.17.157.218/post/my-article`
   - Nginx matches `/` location (catch-all)
   - Forwards request to Gunicorn via Unix socket
   - Gunicorn runs Flask app → returns HTML
   - Nginx sends HTML back to user

**Enabling Site:**
```bash
sudo ln -s /etc/nginx/sites-available/wirip /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default  # Remove default site
sudo nginx -t                              # Test configuration
sudo systemctl restart nginx               # Apply changes
```

### 3. Environment Variables (.env)

**File:** `/opt/wirip/.env`

```env
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=a3f8d9c2e1b7a6f5d4c3b2a1098765432109876543210987654321098765

# Database
DATABASE_URL=sqlite:///wirip.db
```

**How Flask Loads It (app.py):**
```python
from dotenv import load_dotenv
import os

load_dotenv()  # Reads .env file

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback-dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///wirip.db')
```

**Why Environment Variables?**
- **Security:** Keeps secrets out of code (never commit to Git)
- **Flexibility:** Easy to change config without code changes
- **Per-Environment:** Different .env for dev/staging/production

---

## Security Implementation

### 1. Secret Key Management

**Purpose:** Flask uses SECRET_KEY to sign session cookies (prevents tampering)

**Generation (Cryptographically Secure):**
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**Bad Practice (Never Do This):**
```python
app.config['SECRET_KEY'] = 'my-password-123'  # Predictable, insecure
```

**Good Practice:**
```python
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')  # From .env file
```

### 2. Password Security

**Hashing Algorithm:** PBKDF2-SHA256 (via Werkzeug)

**Registration Flow:**
```python
from werkzeug.security import generate_password_hash

password = request.form.get('password')
hashed = generate_password_hash(password, method='pbkdf2:sha256')

user = User(username=username, password_hash=hashed)
db.session.add(user)
db.session.commit()
```

**Login Verification:**
```python
from werkzeug.security import check_password_hash

user = User.query.filter_by(username=username).first()
if check_password_hash(user.password_hash, submitted_password):
    login_user(user)  # Success
```

**Why Hashing?**
- Even if database is stolen, passwords are unreadable
- One-way function (can't reverse hash to get password)
- Salted (same password = different hashes for different users)

### 3. SQL Injection Prevention

**Vulnerable Code (Never Do This):**
```python
# BAD: User input directly in SQL query
username = request.form.get('username')
query = f"SELECT * FROM users WHERE username = '{username}'"
db.execute(query)
# Attacker can inject: username = "admin' OR '1'='1"
```

**Safe Code (SQLAlchemy ORM):**
```python
# GOOD: ORM automatically escapes inputs
username = request.form.get('username')
user = User.query.filter_by(username=username).first()
# SQLAlchemy parameterizes query: SELECT * FROM users WHERE username = ?
```

### 4. CSRF Protection (Cross-Site Request Forgery)

**Flask-WTF Integration (if using forms):**
```python
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect(app)

# In template:
<form method="POST">
    {{ form.csrf_token }}  <!-- Auto-generated token -->
    <input type="text" name="username">
    <button type="submit">Submit</button>
</form>
```

### 5. Session Security

**Flask Session Configuration:**
```python
app.config['SESSION_COOKIE_HTTPONLY'] = True   # Prevent JavaScript access
app.config['SESSION_COOKIE_SECURE'] = True     # HTTPS only (production)
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # 7-day sessions
```

### 6. File Upload Security

**Secure File Handling:**
```python
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
@login_required
def upload():
    file = request.files.get('image')
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)  # Sanitize filename
        filepath = os.path.join('static/images', filename)
        file.save(filepath)
        return jsonify({'success': True})
    
    return jsonify({'error': 'Invalid file'}), 400
```

### 7. Admin Access Control

**Route Protection:**
```python
@app.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Admin access required', 'danger')
        return redirect(url_for('home'))
    
    # Admin-only functionality
    return render_template('admin.html')
```

**Template-Level Protection:**
```html
{% if current_user.is_authenticated and current_user.is_admin %}
    <a href="{{ url_for('create_post') }}">Create Post</a>
{% endif %}
```

---

## Deployment Process Step-by-Step

### Phase 1: Infrastructure Setup

**1. Launch EC2 Instance**
- Ubuntu 22.04 LTS (free tier eligible)
- t2.micro (1 vCPU, 1 GB RAM)
- Security Group: Allow SSH (22), HTTP (80)
- Generate/download SSH key pair

**2. Connect to Server**
```bash
ssh -i your-key.pem ubuntu@50.17.157.218
```

**3. Install System Dependencies**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip git nginx
```

### Phase 2: Application Deployment

**4. Clone Repository**
```bash
cd /opt
sudo git clone https://github.com/arush3218/wirip.git
sudo chown -R ubuntu:ubuntu wirip
cd wirip
```

**5. Install Python Dependencies**
```bash
sudo pip3 install -r requirements.txt
sudo pip3 install gunicorn
```

**6. Configure Environment**
```bash
# Generate secret key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Create .env file
nano .env
```

Paste:
```env
FLASK_ENV=production
SECRET_KEY=<generated-key>
DATABASE_URL=sqlite:///wirip.db
```

**7. Initialize Database**
```bash
python3 app.py
```

Output:
```
Database initialized with default data!
 * Admin user created: admin / admin123
 * 6 categories created
```

### Phase 3: Production Services

**8. Create Systemd Service**
```bash
sudo nano /etc/systemd/system/wirip.service
```

Paste configuration (see section above), then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wirip
sudo systemctl start wirip
sudo systemctl status wirip  # Should show "active (running)"
```

**9. Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/wirip
```

Paste configuration (see section above), then:
```bash
sudo ln -s /etc/nginx/sites-available/wirip /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t  # Test configuration
sudo systemctl restart nginx
```

**10. Test Deployment**
- Open browser: `http://50.17.157.218`
- Should see WiRiP homepage with logo
- Test login: `admin` / `admin123`
- Create a test post
- Verify voting works

### Phase 4: Maintenance & Updates

**Deploy Code Updates:**
```bash
cd /opt/wirip
git pull
sudo pip3 install -r requirements.txt --upgrade
sudo systemctl restart wirip
```

**Monitor Logs:**
```bash
# Application logs
sudo journalctl -u wirip -f

# Nginx access logs
sudo tail -f /var/log/nginx/access.log

# Nginx error logs
sudo tail -f /var/log/nginx/error.log
```

**Database Backup:**
```bash
cp /opt/wirip/wirip.db /opt/wirip/backups/wirip_$(date +%Y%m%d).db
```

---

## Performance Optimization

### 1. Static File Caching

Nginx serves static files with 30-day cache headers:
```nginx
location /static/ {
    alias /opt/wirip/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

**Result:** Browser caches CSS/JS/images for 30 days (faster page loads)

### 2. Database Query Optimization

**Eager Loading (Avoid N+1 Queries):**
```python
# BAD: Triggers separate query for each post's author
posts = Post.query.all()
for post in posts:
    print(post.author.username)  # N+1 queries!

# GOOD: Load authors in single query
posts = Post.query.options(db.joinedload(Post.author)).all()
for post in posts:
    print(post.author.username)  # Already loaded!
```

### 3. Gunicorn Worker Tuning

**Formula:** `workers = (2 × CPU_cores) + 1`

For t2.micro (1 vCPU):
```bash
--workers 3  # (2 × 1) + 1 = 3
```

For larger instances:
```bash
# t2.medium (2 vCPUs)
--workers 5  # (2 × 2) + 1 = 5
```

### 4. Connection Pooling (PostgreSQL)

If migrating to PostgreSQL:
```python
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,        # Max connections
    'pool_recycle': 3600,   # Recycle after 1 hour
    'pool_pre_ping': True   # Test connection before use
}
```

---

## Troubleshooting Common Issues

### Issue 1: 502 Bad Gateway (Nginx)

**Cause:** Nginx can't connect to Gunicorn

**Solutions:**
```bash
# Check Gunicorn is running
sudo systemctl status wirip

# Check socket file exists
ls -la /opt/wirip/wirip.sock

# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Restart services
sudo systemctl restart wirip
sudo systemctl restart nginx
```

### Issue 2: Database Locked Error

**Cause:** SQLite doesn't handle concurrent writes well

**Solutions:**
1. **Short-term:** Reduce Gunicorn workers to 1
2. **Long-term:** Migrate to PostgreSQL (AWS RDS)

### Issue 3: Static Files 404

**Cause:** Incorrect file paths or permissions

**Solutions:**
```bash
# Check file exists
ls -la /opt/wirip/static/css/style.css

# Fix permissions
sudo chown -R ubuntu:www-data /opt/wirip/static
sudo chmod -R 755 /opt/wirip/static

# Check Nginx configuration
sudo nginx -t
```

### Issue 4: Session Not Persisting

**Cause:** SECRET_KEY not set or changing

**Solutions:**
```bash
# Verify .env file exists
cat /opt/wirip/.env

# Check Flask loaded it
sudo journalctl -u wirip -n 50 | grep SECRET_KEY

# Restart service
sudo systemctl restart wirip
```

---

## Scaling Considerations

### Horizontal Scaling

**Current:** Single EC2 instance (vertical scaling limited to instance size)

**Next Steps:**
1. **Load Balancer:** AWS ELB distributes traffic across multiple EC2 instances
2. **Shared Database:** Migrate SQLite → PostgreSQL RDS (shared by all instances)
3. **Session Store:** Use Redis for sessions (instead of Flask's encrypted cookies)
4. **Static Files:** Use S3 + CloudFront CDN (offload from EC2)

### Vertical Scaling

**Upgrade Instance:**
```
t2.micro (1 vCPU, 1 GB RAM) → t2.small (1 vCPU, 2 GB RAM)
→ t2.medium (2 vCPU, 4 GB RAM) → t2.large (2 vCPU, 8 GB RAM)
```

**Adjust Gunicorn Workers:**
```bash
# Edit systemd service
sudo nano /etc/systemd/system/wirip.service

# Change --workers based on CPU count
ExecStart=/usr/local/bin/gunicorn --workers 5 ...

sudo systemctl daemon-reload
sudo systemctl restart wirip
```

---

## Monitoring & Logging

### Application Logs

```bash
# View latest 50 lines
sudo journalctl -u wirip -n 50

# Follow live logs
sudo journalctl -u wirip -f

# Filter by time
sudo journalctl -u wirip --since "1 hour ago"
```

### Nginx Logs

```bash
# Access logs (successful requests)
sudo tail -f /var/log/nginx/access.log

# Error logs (failed requests, proxy errors)
sudo tail -f /var/log/nginx/error.log
```

### System Monitoring

```bash
# CPU, memory, disk usage
htop

# Disk space
df -h

# Network connections
netstat -tulpn | grep :80
```

### Optional: CloudWatch Integration

AWS CloudWatch can collect logs and metrics:
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure to send logs to CloudWatch
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

---

## Production Checklist

Before going live:

- [ ] Change admin password from default `admin123`
- [ ] Set strong SECRET_KEY in .env (min 32 characters)
- [ ] Enable HTTPS with Certbot/Let's Encrypt
- [ ] Restrict SSH to your IP in Security Group
- [ ] Set up automated backups (database, .env)
- [ ] Configure log rotation (`logrotate`)
- [ ] Enable CloudWatch monitoring (optional)
- [ ] Test error pages (404, 500)
- [ ] Set up domain name (Route 53 or external registrar)
- [ ] Implement rate limiting (Nginx or Flask-Limiter)
- [ ] Add CSRF protection (Flask-WTF)
- [ ] Review file upload restrictions
- [ ] Test mobile responsiveness
- [ ] Set up staging environment (optional)
- [ ] Document deployment process (you're reading it!)

---

## Additional Resources

**Official Documentation:**
- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://www.sqlalchemy.org/
- Gunicorn: https://gunicorn.org/
- Nginx: https://nginx.org/en/docs/
- AWS EC2: https://docs.aws.amazon.com/ec2/

**Tutorials:**
- Flask Mega-Tutorial: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world
- Deploying Flask Apps: https://www.digitalocean.com/community/tutorials/how-to-serve-flask-applications-with-gunicorn-and-nginx-on-ubuntu-22-04

**Security:**
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Flask Security Best Practices: https://flask.palletsprojects.com/en/2.3.x/security/

---

**Congratulations! You now understand the complete WiRiP architecture and deployment process.** 🎉
