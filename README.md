# GraphQL Client.

## Synopsis
Ease the access to GraphQL APIs.

## Motivation
Easy to use, strongly-typed clinet API for GraphQL.

## Code Example
```python
from query import QueryNode
from query_binder import bind

def get_http():
    session = requests.Session()
    session.headers['Authorization'] = 'Bearer {}'.\
        format('<gh token>')
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
