from app import db, User, app
from werkzeug.security import generate_password_hash

# Wrap the code within the application context
with app.app_context():
    # Password to be hashed
    password = '1337'
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    
    # Create an admin user
    admin = User(username='admin', password_hash=hashed_password)
    
    # Add and commit to the database
    db.session.add(admin)
    db.session.commit()
    
    print("Admin user created successfully!")
