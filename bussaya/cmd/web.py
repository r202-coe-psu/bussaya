from livereload import Server

from bussaya import web


def main():
    options = web.get_program_options()
    app = web.create_app()
    app.debug = options.debug

    server = Server(app.wsgi_app)
    server.watch("bussaya/web")
    server.serve(
        debug=options.debug,
        host=options.host,
        port=int(options.port),
        restart_delay=2,
    )
