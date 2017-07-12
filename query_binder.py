from query import QueryNode
import requests


class Decorator:
    '''
    Parameterized function decorator for scalar binding.
    '''
    def __init__(self, field, url, http):
        self.field = field
        self.url = url
        self.http = http

    def decorate(self, f):
        def decorator(receiver):
            if self.field in receiver.values:
                return f(receiver)
            child = receiver.qroot._get_child(self.field)
            if child is None:
                child = receiver.qroot.add_child_node(QueryNode(self.field))
            receiver.qroot._query(self.http, self.url)
            receiver.values[self.field] = child.val
            return f(receiver)
        return decorator


def bind(field, url, http):
    d = Decorator(field, url, http)
    return d.decorate


def get_http():
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer {}'.\
        format('<your gh token here>')
    return session


class GHUser(QueryNode):
    '''
    Usage example class for GH user.
    '''
    def __init__(self, un):
        QueryNode.__init__(self, 'user')
        self.qroot = self.add_child_node(QueryNode('user')).\
            add_arg('login', un)
        self.values = dict()

    @bind(field='name', url='https://api.github.com/graphql', http=get_http())
    def get_name(self):
        return self.values['name']


user = GHUser('linus')
print user.get_name()
