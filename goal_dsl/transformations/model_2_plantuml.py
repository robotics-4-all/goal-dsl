from textx import metamodel_from_file
from jinja2 import Template
from goal_dsl.language import build_model

def generate_diagram(model_path):
    """Fixed generator that handles all goal types"""
    model = build_model(model_path)

    template = Template("""@startebnf
(* {{ scenario.name }} *)
Goals =
    {% for weighted_goal in scenario.goals -%}
    {{ "( " }}
        "{{ weighted_goal.goal.name }}:"{% if weighted_goal.goal.__class__.__name__ == "GoalRepeater" %},
            {{ weighted_goal.goal.times }} *
            [ "{{ weighted_goal.goal.goal.name }}:"{% for subgoal in weighted_goal.goal.goal.goals %},
                "{{ subgoal.goal.name }}{% if subgoal.goal.timeConstraints %} ({{ subgoal.goal.timeConstraints[0].time }}s){% endif %}"
            {% endfor %} ]
        {% elif weighted_goal.goal.__class__.__name__ == "ComplexGoal" %},
            "strategy: {{ weighted_goal.goal.algorithm }}",
            [ "subgoals:"{% for sub_goal in weighted_goal.goal.goals %},
                "{{ sub_goal.goal.name }}{% if sub_goal.weight %} (weight={{ sub_goal.weight }}){% endif %}"
            {% endfor %} ]
        {% endif %}
    {{ " )" }}{% if not loop.last %} |{% endif %}
    {% endfor %};
Fatals =
    {% for fatal in scenario.fatals -%}
    {{ "( " }}
        "{{ fatal.name }}"
    {{ " )" }}{% if not loop.last %} |{% endif %}
    {% endfor %};
@endebnf""")

    for scenario in model.scenarios:
        with open(f"{scenario.name}.puml", "w") as f:
            f.write(template.render(scenario=scenario))
        print(f"Generated: {scenario.name}.puml")

if __name__ == "__main__":
    import sys
    generate_diagram(sys.argv[1])
