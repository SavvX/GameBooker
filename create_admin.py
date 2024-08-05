from app import db, User, app

# Wrap the code within the application context
with app.app_context():
    admin = User(username='admin', password='secret')
    db.session.add(admin)
    db.session.commit()
    print("Admin user created successfully!")
