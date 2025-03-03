import numpy as np
import pickle

def generate_template(minutiae):
    """Generates a compact template from the minutiae data."""
    template_data = []
    for x, y, type_ in minutiae:
        template_data.append((x, y, type_))

    template = pickle.dumps(template_data)
    return template
