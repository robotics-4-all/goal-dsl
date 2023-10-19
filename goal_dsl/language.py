from os.path import join
from textx import metamodel_from_file
import textx.scoping.providers as scoping_providers
from textx import language

from goal_dsl.definitions import THIS_DIR


def get_metamodel(debug=False):
    """
    """
    mm= metamodel_from_file(
        join(THIS_DIR, 'grammar', 'goal_dsl.tx'),
        global_repository=True,
        debug=debug
    )

    mm.register_scope_providers(
        {
            "*.*": scoping_providers.FQNImportURI(importAs=True),
        }
    )

    return mm


def build_model(model_fpath):
    mm = get_metamodel()
    model = mm.model_from_file(model_fpath)
    # print(model._tx_loaded_models)
    reg_models = mm._tx_model_repository.all_models.filename_to_model
    models = [val for _, val in reg_models.items() if val != model]
    return (model, models)


@language('goal_dsl', '*.goal')
def goaldsl_language():
    "Goal-driven CPS Behavior Verification language"
    return get_metamodel()
