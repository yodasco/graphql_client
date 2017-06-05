# GraphQL Client.

## Synopsis
Ease the access to GraphQL APIs.

## Motivation
Easy to use, strongly-typed clinet API for GraphQL.

## Code Example
```python
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
    # 'linus' is now binded.
    pwd.close()
```

## Installation
`pip install graphql_client`

## Licence
TBD
