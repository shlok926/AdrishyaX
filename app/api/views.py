from flask import Blueprint, render_template

views_bp = Blueprint('views', __name__)

@views_bp.route('/')
def serve_index():
    return render_template('encode.html')

@views_bp.route('/decode')
def serve_decode():
    return render_template('decode.html')

@views_bp.route('/batch')
def serve_batch():
    return render_template('batch.html')

@views_bp.route('/keys')
def serve_keys():
    return render_template('keys.html')

@views_bp.route('/audit')
def serve_audit():
    return render_template('audit.html')
