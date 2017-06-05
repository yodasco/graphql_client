import requests
import functools


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

    def _list_query(self, list_name):
        '''
        Queries for the next bulk of the list with the given name.
        Other then that, the state stays the same.
        '''
        # Prune all child nodes, but followers (reduce traffic).
        restore = self.prune_childes(retain={list_name})
        self.query_call()
        # Finally, restore other state elements.
        restore()

    def _list_gen(self, list_name, key):
        '''
        Returns a generator for the list with the given name.
        list_name: Name of the list to be iterated.
        key: Name of the key in each item.
        '''
        list_node = self._get_child(list_name)
        while list_node.has_current():
            cur = list_node.current()
            # Yield current item.
            yield cur[key]
            # Iteration advance.
            list_query = functools.partial(self._list_query, list_name)
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
        that their names are in 'freez_set' += remove += removednode: node to
        be pruned.
            freez_set: names of the nodes to be left in the DOM.
            deep: True if state copying should be down deep, False indicates
                  shallow state copying.
            Return: a callable to restore the previous state.
            '''
        removed = filter(lambda n: n.name not in retain, self.childes)
        self.childes = filter(lambda n: n.name in retain, self.childes)

        def _restore():
            self.childes += removed
        return _restore

    def set_query_call(self, query_call):
        '''
        Sets the query callable to be used by the node if needed.
        '''
        self.query_call = query_call

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
        if 'errors' in res:
            print 'Error: {}'.format(res['errors'])
        else:
            print 'Error, code {}'.format(res.status_code)
        return None
    dres = res.json()
    if 'errors' in dres:
        if on_query_error:
            on_query_error(dres['errors'], node)
        return None
    return node.bind(dres)


class GraphqlQuery(QueryNode):
    def __init__(self):
        QueryNode.__init__(self, 'query')
        self.bind_name = 'data'


def create_query(auth, qnode, url, on_error=None):
    '''
    Creates a callable object that queries that binds the given 'qnode'
    with data returned from the graphql query.
    '''
    http = requests.Session()
    http.headers['Authorization'] = 'Bearer {}'.format(auth)
    root_node = GraphqlQuery()
    root_node.add_child_node(qnode)
    query_invcation = functools.partial(query_node,
                                        root_node,
                                        http,
                                        url,
                                        on_error)
    qnode.set_query_call(query_invcation)
    return query_invcation


def usage_example():
    query = QueryNode('query')
    linus = query.add_child_node(QueryNode('user')).\
        add_arg('login', 'torvalds')
    linus.add_child_node(QueryNode('id'))
    linus.add_child_node(QueryNode('email'))
    linus.add_child_node(QueryNode('avatar')).add_arg('size', 20)
    pwd = open('pwd.txt', 'r')
    query = create_query(pwd.readline().strip(), linus,
                         'https://api.github.com/graphql')
    query()
    pwd.close()


if __name__ == '__main__':
    usage_example()
