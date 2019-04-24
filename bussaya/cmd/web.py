import bussaya

def main():
    options = bussaya.get_program_options()
    app = bussaya.create_app()

    app.run(
        debug=options.debug,
        host=options.host,
        port=int(options.port)
    )
