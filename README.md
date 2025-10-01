## WiRiP – Rap Music Blog (Flask)
Dark themed rap blog with user roles, writer approvals, voting, and category‑based posts.

### Core Features
- Auth (users, writers (approval), admins)
- Categories: News, Album Review, Song Review, Discover New Artist
- Post approval workflow (admin)
- Upvote / downvote (one per user per post)
- Writer application (Join Crew)
- Placeholder Billboard feed

### Quick Start
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
python app.py
```
Visit http://localhost:5000

Default admin (change immediately): admin / admin123

### Environment (optional .env)
```
SECRET_KEY=change-me
DATABASE_URL=sqlite:///wirip.db
```

Switch DB (example PostgreSQL) in `app.py`:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@host:5432/wirip'
```

### Minimal Structure
```
app.py
templates/ (base, home, blogs, blog_detail, auth, admin)
static/css/style.css
static/js/main.js
```

### Production Notes
Use Gunicorn + Nginx (see deploy script). Set real SECRET_KEY. Enforce HTTPS. Change admin password.

### License
MIT

— WiRiP