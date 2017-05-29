import requests


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

    def add_child_node(self, child):
        '''
        DOM-API.
        Adds the given child node to the child collection of this node.
        '''
        self.childes.append(child)
        return child

    def prune_childes(self, freez_set, deep=False):
        '''
        Prunes all the child node for the given node; but leave the child nodes
        that their names are in 'freez_set' += remove += removednode: node to
        be pruned.
            freez_set: names of the nodes to be left in the DOM.
            deep: True if state copying should be down deep, False indicates
                  shallow state copying.
            Return: a callable to restore the previous state.
            '''
        removed = filter(lambda n: n.name not in freez_set, self.childes)
        self.childes = filter(lambda n: n.name in freez_set, self.childes)

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
            child_node.bind(res[bind_name])
        return self


def query_node(node, http, url, on_query_error=None):
    # TODO: Remove.
    in_query = {'query': str(node)}
    res = http.post(url, json=in_query)
    if res.status_code != requests.codes.ok:
        # TODO: log this.
        print 'Error: {}'.format(res['errors'])
        return None
    dres = res.json()
    if 'errors' in dres:
        if on_query_error:
            on_query_error(dres['errors'], node)
        return None
    return node.bind(dres)


def usage_example():
    query = QueryNode('query')
    linus = query.add_child_node(QueryNode('user')).\
        add_arg('login', 'torvalds')
    linus.add_child_node(QueryNode('id'))
    linus.add_child_node(QueryNode('email'))
    linus.add_child_node(QueryNode('avatar')).add_arg('size', 20)
    query_node(query, requests.Session(), 'https://api.github.com/graphql')
