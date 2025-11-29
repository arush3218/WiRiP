"""
Database initialization script for production deployment
Run this to create all database tables
"""
from app import app, db, User, Category
from werkzeug.security import generate_password_hash

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✓ Database tables created")
        
        # Create default categories if they don't exist
        categories = ['News', 'Album Review', 'Song Review', 'Discover New Artist', 'Interview']
        for cat_name in categories:
            if not Category.query.filter_by(name=cat_name).first():
                category = Category(name=cat_name)
                db.session.add(category)
        db.session.commit()
        print("✓ Default categories created")
        
        # Create admin user if it doesn't exist
        admin_email = 'admin@wirip.com'
        if not User.query.filter_by(email=admin_email).first():
            admin = User(
                username='admin',
                email=admin_email,
                password_hash=generate_password_hash('admin123'),  # Change this password!
                is_admin=True,
                is_writer=True
            )
            db.session.add(admin)
            db.session.commit()
            print("✓ Admin user created (username: admin, password: admin123)")
            print("  ⚠️  IMPORTANT: Change the admin password after first login!")
        
        print("\n✅ Database initialization complete!")

if __name__ == '__main__':
    init_database()
