#!/usr/bin/python
from uml_utils import build_uml_class_content


# NODE

def build_dot_node(full_class_name, label):
    template = "\"{}\" [\n\tlabel = \n{}];"
    return template.format(full_class_name, label)


def build_classes_nodes(classes):
    result = []
    for c in classes:
        class_content = build_uml_class_content(c["full_name"], c["fields"], c["methods"])
        node = build_dot_node(c["full_name"], class_content)
        result.append(node)

    return result


# RELATIONSHIPS

def build_edge_attributes(rtype, taillabel=None, label=None, headlabel=None, labeldistance=None):
    relationships = {
        "association":
            '[style="solid", taillabel="{}", label="{}", headlabel="{}", '
            'arrowhead="vee", labeldistance="{}"]; // association',
        "dependency":
            '[style="dashed", taillabel="{}", label="{}", headlabel="{}", '
        'arrowhead="vee", labeldistance="{}"]; // dependency',
        "aggregation":
            '[style="solid", dir="both", taillabel="{}", arrowtail="odiamond", '
            'label="{}", headlabel="{}", arrowhead="vee", labeldistance="{}"]; // aggregation',
        "composition":
            '[style="solid", dir="both", taillabel="{}", arrowtail="diamond", '
            'label="{}", headlabel="{}", arrowhead="vee", labeldistance="{}"]; // composition',
        "inheritance":
            '[style="solid", arrowhead="onormal"]; // inheritance',
        "realization":
            '[style="dashed", arrowhead="onormal"]; // realization'
    }

    if not rtype in relationships:
        return None

    taillabel = taillabel if taillabel else ""
    label = label if label else ""
    headlabel = headlabel if headlabel else ""
    labeldistance = labeldistance if labeldistance else ""

    return relationships[rtype].format(taillabel, label, headlabel, labeldistance)


def build_relationship(depender, dependee, rtype,
                       taillabel=None, label=None, headlabel=None, labeldistance=None):
    edge_attributes = build_edge_attributes(rtype, taillabel, label, headlabel, labeldistance)

    return "\"{}\" -> \"{}\" {}".format(depender, dependee, edge_attributes)


def match_class_full_name(classes, pattern):
    results = []
    full_names = []
    for c in classes:
        full_names.append(c["full_name"])
        if re.search(pattern, c["full_name"]):
            results.append(c["full_name"])

    if not results:
        raise ValueError(
            "Error: No class full name matching pattern '{}': {}".format(pattern, full_names))
        return None
    elif len(results) > 1:
        raise ValueError("Error: Several classes full name are matching pattern '{}': {}".format(
            pattern, results))
        return None

    return results[0]


def build_relationships(args_list, classes):
    results = []

    for args in args_list:
        if args.relationship_type:
            if not args.relationship_depender:
                args.relationship_depender = args.class_pattern

            try:
                depender_full_name = match_class_full_name(classes, args.relationship_depender)
                dependee_full_name = match_class_full_name(classes, args.relationship_dependee)
            except ValueError as error:
                print(error)
                raise ValueError("Could not build relationships with args '{}'.".format(args))
                return None

            relationship = build_relationship(depender_full_name,
                                              dependee_full_name,
                                              args.relationship_type,
                                              args.relationship_taillabel,
                                              args.relationship_label,
                                              args.relationship_headlabel,
                                              args.relationship_labeldistance)
            results.append(relationship)

    return results

# GRAPH


def build_graph(args_list, classes):
    template = ('digraph "Class Diagram"\n'
                '{{\n'
                '\tbgcolor = transparent;\n'
                '\trankdir = LR;\n'
                '\tedge [fontname = Helvetica, fontsize = 10, labelfontname = Helvetica, '
                'labelfontsize = 10];\n'
                '\tnode [fontname = Helvetica, fontsize = 10, shape = none, margin = 0, '
                'style = filled, fillcolor = grey75, fontcolor = black ];\n'
                '\n'
                '{}\n'
                '\n'
                '{}\n'
                '}}')

    nodes = build_classes_nodes(classes)
    relationships = build_relationships(args_list, classes)
    return template.format("\n".join(nodes), "\n".join(relationships))
