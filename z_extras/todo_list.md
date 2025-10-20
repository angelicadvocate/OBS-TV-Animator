
## TO DO LIST:

- Refactor current HTML examples as a scaffold for future use as an overlay. Overlay should contain the connected icon, request change, and handle screen refresh.
- Remove unnecessary files from repo that were used for testing original scaffolding.
- Use eventlet or gevent, etc and remove the 'allow_unsafe_werkzeug=True' from app.py in socketio.run(app, host='0.0.0.0', port=8080, debug=False, allow_unsafe_werkzeug=True)
