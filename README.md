# GraphQL Client.

## Synopsis
Ease the access to GraphQL APIs.

## Motivation
Easy to use, strongly-typed clinet API for GraphQL.

## Code Example
query = QueryNode('query')
linus = query.add_child_node(QueryNode('user')).\
    add_arg('login', 'torvalds')
linus.add_child_node(QueryNode('id'))
linus.add_child_node(QueryNode('email'))
linus.add_child_node(QueryNode('avatar')).add_arg('size', 20)
session = requests.Session()
session.headers['Authorization'] = 'Bearer <Your Github AUTH>'
query_node(query, session, 'https://api.github.com/graphql')

## Installation
TBD

## Licence
TBD
