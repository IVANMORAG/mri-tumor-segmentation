from flask import render_template, send_from_directory

def setup_view_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/static/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)