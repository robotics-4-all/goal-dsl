from textx import metamodel_from_file
import jinja2
from goal_dsl.definitions import TEMPLATES_PATH
from goal_dsl.language import build_model


jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(TEMPLATES_PATH),
    trim_blocks=True,
    lstrip_blocks=True
)

template = jinja_env.get_template('model_2_plantuml.jinja')


def generate_diagram(model_path):
    """Fixed generator that handles all goal types"""
    model = build_model(model_path)

    for scenario in model.scenarios:
        diagram_puml = template.render(
            scenario=scenario
        )
        with open(f"{scenario.name}.puml", "w") as f:
            f.write(diagram_puml)
        print(f"Generated: {scenario.name}.puml")

if __name__ == "__main__":
    import sys
    generate_diagram(sys.argv[1])
