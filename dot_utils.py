#!/usr/bin/python
import re


# NODES

# node_dictionaries should contain 'name' and 'label' keys
def build_dot_nodes(node_dictionaries):
    template = "\"{}\" [\n\tlabel = \n{}];"

    results = []
    for dictionary in node_dictionaries:
        result = template.format(dictionary["name"], dictionary["label"])
        results.append(result)

    return results


# RELATIONSHIPS

def _build_edge_attributes(rtype, taillabel=None, label=None, headlabel=None, labeldistance=None):
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


def _build_relationship(depender, dependee, rtype,
                        taillabel=None, label=None, headlabel=None, labeldistance=None):
    edge_attributes = _build_edge_attributes(rtype, taillabel, label, headlabel, labeldistance)

    return "\"{}\" -> \"{}\" {}".format(depender, dependee, edge_attributes)


def _match_the_only_name(node_names, pattern):
    results = [name for name in node_names if re.search(pattern, name)]

    if not results:
        print "Error: No class full name matching pattern '{}': {}".format(pattern, node_names)
        return None

    elif len(results) > 1:
        print "Error: Several classes full name are matching pattern '{}': {}".format(pattern,
                                                                                      results)
        return None

    return results[0]


def build_relationships(args_list, node_names):
    results = []

    for args in args_list:
        if args.relationship_type:
            if not args.relationship_depender:
                args.relationship_depender = args.class_pattern

            depender_full_name = _match_the_only_name(node_names, args.relationship_depender)
            dependee_full_name = _match_the_only_name(node_names, args.relationship_dependee)
            if depender_full_name is None or dependee_full_name is None:
                print "Could not build relationships with args '{}'.".format(args)
                return None

            relationship = _build_relationship(depender_full_name,
                                               dependee_full_name,
                                               args.relationship_type,
                                               args.relationship_taillabel,
                                               args.relationship_label,
                                               args.relationship_headlabel,
                                               args.relationship_labeldistance)
            results.append(relationship)

    return results

# GRAPH


def build_graph(args_list, node_dictionaries):
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

    nodes = build_dot_nodes(node_dictionaries)
    node_names = [dictionary["name"] for dictionary in node_dictionaries]
    relationships = build_relationships(args_list, node_names)
    return template.format("\n".join(nodes), "\n".join(relationships))
