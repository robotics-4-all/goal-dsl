from os.path import dirname, join
from textx import metamodel_from_file
import textx.scoping.providers as scoping_providers

this_dir = dirname(__file__)


def get_mm(debug=False, global_scope=True):
    """
    """
    mm= metamodel_from_file(
        join(this_dir, 'goal_dsl.tx'),
        global_repository=global_scope,
        debug=debug
    )

    mm.register_scope_providers(
        {
            "*.*": scoping_providers.FQNImportURI(
                importAs=True,
                # importURI_to_scope_name=importURI_to_scope_name
            )
        }
    )

    return mm


def build_model(model_fpath):
    mm = get_mm(global_scope=True)
    model = mm.model_from_file(model_fpath)
    # print(model._tx_loaded_models)
    reg_models = mm._tx_model_repository.all_models.filename_to_model
    models = [val for key, val in reg_models.items() if val != model]
    return (model, models)


def get_grammar(debug=False):
    with open(join(this_dir, 'thing_dsl.tx')) as f:
        return f.read()

