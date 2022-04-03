"""Loader function for templates."""
import importlib.resources

ENCODING = 'utf-8'


def load_html(resource: str, is_complete_path: bool = False) -> str:
    """Load the template either from the package resources or an external path."""
    if is_complete_path:
        with open(resource, 'rt', encoding=ENCODING) as handle:
            return handle.read()
    else:
        with importlib.resources.path(__package__, resource) as html_template_path:
            with open(html_template_path, 'rt', encoding=ENCODING) as handle:
                return handle.read()
