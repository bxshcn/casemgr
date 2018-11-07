from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors
from ..models import Permission


@main.app_context_processor
def inject_permissions():
    # dict(**kwargs) -> new dictionary initialized with the name=value pairs
    #    in the keyword argument list.  For example:  dict(one=1, two=2)
    return dict(Permission=Permission)