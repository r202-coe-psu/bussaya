import datetime
import pathlib
import importlib
import logging

logger = logging.getLogger(__name__)


def add_date_url(url):
    now = datetime.datetime.now()
    return f'{url}?date={now.strftime("%Y%m%d")}'


GRADE_COLORS = {
    "A": ("#38bdf8", "#ffffff"),
    "B+": ("#22c55e", "#ffffff"),
    "B": ("#bbf7d0", "#14532d"),
    "C+": ("#facc15", "#713f12"),
    "C": ("#fef08a", "#713f12"),
    "D+": ("#fb923c", "#ffffff"),
    "D": ("#fed7aa", "#7c2d12"),
    "E": ("#ef4444", "#ffffff"),
}
GRADE_COLOR_DEFAULT = ("#d1d5db", "#374151")


def grade_style(grade):
    bg, fg = GRADE_COLORS.get(grade, GRADE_COLOR_DEFAULT)
    return f"background-color: {bg}; color: {fg};"


def get_subblueprints(directory):
    blueprints = []

    package = directory.parts[len(pathlib.Path.cwd().parts) :]
    parent_module = None
    try:
        parrent_view = directory.with_name("__init__.py")
        pymod_file = f"{'.'.join(package)}"
        pymod = importlib.import_module(pymod_file)

        if "module" in dir(pymod):
            parent_module = pymod.module
            blueprints.append(parent_module)
    except Exception as e:
        logger.exception(e)
        return blueprints

    subblueprints = []
    for module in directory.iterdir():

        if "__" == module.name[:2]:
            continue

        if module.match("*.py"):
            try:
                pymod_file = f"{'.'.join(package)}.{module.stem}"
                pymod = importlib.import_module(pymod_file)

                if "module" in dir(pymod):
                    subblueprints.append(pymod.module)
            except Exception as e:
                logger.exception(e)

        elif module.is_dir():
            subblueprints.extend(get_subblueprints(module))

    for module in subblueprints:
        if parent_module:
            parent_module.register_blueprint(module)
        else:
            blueprints.append(module)

    return blueprints


def register_blueprint(app):
    app.add_template_filter(add_date_url)
    app.add_template_filter(grade_style)
    parent = pathlib.Path(__file__).parent
    blueprints = get_subblueprints(parent)

    for blueprint in blueprints:
        app.register_blueprint(blueprint)
