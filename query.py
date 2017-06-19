import requests
import functools
from requests import exceptions


class GhGraphQLError(Exception):
    def __init__(self, http_res):
        err_msg = http_res['errors']
        Exception.__init__(self, err_msg)


class QueryNode:
    '''
    Represents a GraphQL Query node.
    '''
    def __init__(self, name):
        # Node name.
        self.name = name
        self.bind_name = name
        # Node Arguments.
        self.args = dict()
        # Node childes.
        self.childes = list()

    # Protected util.
    def _format_arg(self, arg_name, arg_val):
        '''
        Internal-Utility.
        Returns a graphql string query for the given argument name and value.
        '''
        return '{}:{}'.format(arg_name, arg_val)

    def _query(self, http, url):
        root = GraphqlQuery()
        root.add_child_node(self)
        in_query = {'query': str(root)}
        res = http.post(url, json=in_query)
        if res.status_code != requests.codes.ok:
            raise exceptions.RequestException(
                {'response': res, 'request': in_query})
        json = res.json()
        if 'errors' in json:
            return res
        root.bind(json)
        return res

    def _get_child(self, name):
        '''
        Internal-Utility.
        Returns a query child node with the given name.
        '''
        for child_node in self.childes:
            if child_node.name == name:
                return child_node
        return None

    # DOM API.
    def add_arg(self, argname, arg_value):
        '''
        DOM-API.
        Adds an argument for this query node.
        '''
        ty = type(arg_value)
        if ty is str or ty is unicode:
            arg_value = '"{}"'.format(arg_value)
        elif ty is bool:
            arg_value = str(arg_value).lower()
        self.args[argname] = arg_value
        return self

    def _list_query(self, list_name, http, url):
        '''
        Queries for the next bulk of the list with the given name.
        Other then that, the state stays the same.
        '''
        list_child = self._get_child(list_name)
        if list_child.is_binded:
            return
        # Prune all child nodes, but followers (reduce traffic).
        restore = self.prune_childes(retain={list_name})
        self._query(http, url)
        # Finally, restore other state elements.
        restore()

    def _list_gen(self, list_name, key, http, url):
        '''
        Returns a generator for the list with the given name.
        list_name: Name of the list to be iterated.
        key: Name of the key in each item.
        '''
        list_node = self._get_child(list_name)
        list_node.reset()
        while list_node.has_current():
            cur = list_node.current()
            # Yield current item.
            yield None if cur is None else cur[key]
            # Iteration advance.
            list_query = functools.partial(self._list_query, list_name, http,
                                           url)
            list_node.next(list_query)

    def add_child_node(self, child):
        '''
        DOM-API.
        Adds the given child node to the child collection of this node.
        '''
        self.childes.append(child)
        return child

    def prune_childes(self, retain, deep=False):
        '''
        Prunes all the child node for the given node; but leave the child nodes
        that their names are in 'retain' += remove += removednode: node to
        be pruned.
            retain: names of the nodes to be left in the DOM.
            deep: True if state copying should be down deep, False indicates
                  shallow state copying.
            Return: a callable to restore the previous state.
            '''
        removed = filter(lambda n: n.name not in retain, self.childes)
        self.childes = filter(lambda n: n.name in retain, self.childes)

        def _restore():
            self.childes += removed
        return _restore

    def __str__(self):
        '''
        Returns a graphql query representation for this node.
        '''
        s = self.name
        if self.args:
            args_format = '('
            args = self.args.items()
            for idx, (arg_name, arg_val) in enumerate(args):
                if idx == 0:
                    args_format += self._format_arg(arg_name, arg_val)
                    continue
                args_format += ', {}'.format(self._format_arg(
                    arg_name,
                    arg_val))
            args_format += ') '
            s += args_format
        if not self.childes:
            return s if s.endswith(' ') else s + ' '
        s += '{ '
        for child_node in self.childes:
            s += str(child_node)
        s += '} '
        return s

    def bind(self, res):
        '''
        Binds relevant data from the given data dictionary (res) to this node.
        '''
        if not self.childes:
            # Leaf binding.
            self.val = res[self.bind_name]
            return self

        bind_name = self.bind_name
        if bind_name not in res:
            raise(Exception(
                  "Bind error: field '{}' could not be found in {}".
                  format(bind_name, res)))
        for child_node in self.childes:
            if bind_name not in res:
                raise Exception('Internal error, {} not found in {}'.
                                format(bind_name, res))
            child_node.bind(res[bind_name])
        return self


class GraphqlQuery(QueryNode):
    def __init__(self):
        QueryNode.__init__(self, 'query')
        self.bind_name = 'data'


def usage_example():
    query = QueryNode('query')
    linus = query.add_child_node(QueryNode('user')).\
        add_arg('login', 'torvalds')
    linus.add_child_node(QueryNode('id'))
    linus.add_child_node(QueryNode('email'))
    linus.add_child_node(QueryNode('avatarUrl')).add_arg('size', 20)
    pwd = open('pwd.txt', 'r')
    http = requests.Session()
    http.headers['Authorization'] = \
        'Bearer 7556acd462db83839be375fa29717ba597c56fc0'
    linus._query(http, 'https://api.github.com/graphql')
    print 'Linuse\'s Avatar is: {}'.format(linus._get_child('avatarUrl').val)
    pwd.close()


if __name__ == '__main__':
    usage_example()
