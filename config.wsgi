"""
Gunicorn WSGI server configuration.
"""
bind = "0.0.0.0:10000"
workers = 4
accesslog = "-"
errorlog = "-"
