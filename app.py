from flask import Flask, url_for
from models import db, User
from routes import bp_routes
import os
from werkzeug.middleware.proxy_fix import ProxyFix
from prefix_middleware import PrefixMiddleware

# Check if running behind proxy - force to True for testing
behind_proxy = True
prefix = '/calculators' if behind_proxy else ''
print(f"Using URL prefix: '{prefix}'")

# Initialize Flask app
app = Flask(__name__, 
           static_url_path='/static',  # Simplified static URL path
           static_folder='static')

# Configure app to work behind a proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Direct route handler for static files with the prefix
@app.route('/calculators/static/<path:filename>')
def custom_static(filename):
    print(f"Custom static file request handler: {filename}")
    return app.send_static_file(filename)

# Flask configuration
app.config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'your_secret_key'),
    SERVER_NAME=None,  # Important: avoid SERVER_NAME issues
    SQLALCHEMY_DATABASE_URI=os.getenv('DATABASE_URL', 'sqlite:///calculators.db'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    APPLICATION_ROOT=prefix,
    MAX_CONTENT_LENGTH=100 * 1024 * 1024  # 100MB max upload
)

# Initialize database
db.init_app(app)

# Register blueprints
app.register_blueprint(bp_routes)

# Apply prefix middleware
app.wsgi_app = PrefixMiddleware(app.wsgi_app, app=app, prefix=prefix)
print(f"Applied PrefixMiddleware with prefix: {prefix}")

# Static URLs should work either way (with or without prefix)
app.static_url_path = '/static'
print(f"Static folder: {app.static_folder}")
print(f"Static URL path: {app.static_url_path}")

# Test URL generation
with app.test_request_context():
    print(f"URL for static file: {url_for('static', filename='common.css')}")
    print(f"URL for main route: {url_for('routes.main')}")

if __name__ == '__main__':
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
    
    # Print directories to help debug static file loading
    print("Current directory:", os.getcwd())
    if os.path.exists('./static'):
        print("Static directory exists")
        print("Static directory contents:", os.listdir('./static'))
    else:
        print("Static directory not found!")
        
    app.run(host='0.0.0.0', port=80, debug=True)

