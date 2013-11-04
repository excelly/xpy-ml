class Node:
    data=None
    next=None

    def __init__(self, d = None, n = None):
        self.data = d
        self.next = n
    
# a linked list with head node
def insert_head(head, node):
    node.next = head
    return node

def insert_tail(head, node):
    if head is None:
        head = node
    else:
        p = head
        while p.next is not None:
            p = p.next
        p.next = node
        node.next = None
    return head

def print_chain(head):
    p = head
    if p is None:
        print('empty list')
    else:
        while p is not None:
            print(p.data)
            p = p.next

def search_chain(head, target):
    p = None
    c = head
    while c is not None:
        if c.data == target:
            print('node found: {0}'.format(c.data))
            return (c, p)
        else:
            p = c
            c = c.next
    print('"{0}" not found'.format(target))
    return None

def delete_node(head, target):
    found = search_chain(head, target)
    if found is not None:
        c, p = found
        if c == head: # head
            head = head.next
        else:
            p.next = c.next
    return head

def main():
    chain = insert_tail(None, Node('a'))
    chain = insert_head(chain, Node('b'))
    chain = insert_tail(chain, Node('c'))
    print_chain(chain)

    search_chain(chain, 'a')
    search_chain(chain, 'd')

    chain = delete_node(chain, 'a')
    chain = delete_node(chain, 'd')
    print_chain(chain)
    chain = delete_node(chain, 'b')
    print_chain(chain)
    chain = delete_node(chain, 'c')
    print_chain(chain)

if __name__ == "__main__":
    main()
