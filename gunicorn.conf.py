import os

bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"
workers = 2
threads = 4
worker_class = 'sync'
timeout = 120
preload_app = True