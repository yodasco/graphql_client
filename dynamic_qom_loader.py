'''
Dyanmic Query Object Module (QOM) loader.
'''
import imp
from query import QueryNode
from gh_list import GithubList


def load_qom(query_root, qom_path):
    '''
    Loads the given query object module path into the given query root.
    '''
    qom = imp.load_source('qom_directive', qom_path)
    for itm in qom.query:
        key = itm[0]
        if len(itm) == 1:
            # Simple object.
            query_root.add_child_node(QueryNode(key))
            continue
        if len(itm) == 2:
            val = itm[1]
            if isinstance(val, dict):
                parent = query_root.add_child_node(QueryNode(key))
                for pname, pval in val.items():
                    parent.add_arg(pname, pval)
                continue
            if isinstance(val, list):
                list_node = query_root.add_child_node(GithubList(key))
                for itm in val:
                    list_node.add_child_node(QueryNode(itm))
                continue
            raise Exception('Illegal QOM value type.')
        raise Exception('Illegal QOM record arity.')
