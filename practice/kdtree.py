from ex import *
from spatial import *

class LeafNode:
    def __init__(self, idx, data, parent):
        self.idx=idx
        self.data=data
        self.parent=parent

    def __str__(self):
        return "(Leaf, Points={0}, Parent={1})".format(self.idx,self.parent)

class InnerNode:
    def __init__(self, splitter, left_child=None, right_child=None, parent=None):
        self.splitter=splitter
        
        self.left_child=left_child
        self.right_child=right_child
        self.parent=parent

    def __str__(self):
        return "(Splitter={0}, Left={1}, Right={2}, Parent={3})".format(
            self.splitter, self.left_child, self.right_child, self.parent)

class KDTree:
    '''KDTree. this is a static implementation and does not support
    dynamic insertion and deletion.
    '''


    def __init__(self, data=None, leaf_size=10):
        '''constructor. set the tree's leaf_size. if data is not None,
        then the tree is constructed here.
        '''

        self.leaf_size=leaf_size

        if data is not None: self.Build(data, leaf_size)

    def Split(self, idx, data, axis):
        '''split a node's data along axis. return the splitter and the
        data for left and right children.
        '''

        n=len(idx)
        sidx=argsort(data[:, axis])
        idx=idx[sidx]
        data=data[sidx, :]
    
        return ((axis, data[n/2, axis]), # splitter
                (idx[:n/2], data[:n/2, :]), # left node
                (idx[n/2:], data[n/2:, :]) # right node
                )

    def Build(self, data, leaf_size=None):
        '''construct a kd-tree. data is the spatial coordinates of
        points. one row per point. non-recursive.
        '''

        if leaf_size is not None: self.leaf_size=leaf_size
        
        n, dim=data.shape
        self.n=n
        self.dim=dim

        log.debug('Build a kd-tree for {0:e} points with dim={1} and leaf_size={2}'.format(n, dim, self.leaf_size))

        # create the root
        idx=arange(n)
        splitter, left, right=self.Split(idx, data, 0)
        root=InnerNode(splitter)

        tree=[]
        tree.append(root)

        stack=[]
        stack.append((left[0], left[1], 1, 0, -1))
        stack.append((right[0], right[1], 1, 0, 1))

        # build the tree non-recursively
        while len(stack) > 0:
            idx, data, depth, parent, side=stack.pop()
            n=data.shape[0]
            node_id=len(tree)

            if side < 0: tree[parent].left_child=node_id
            else: tree[parent].right_child=node_id

            if n <= self.leaf_size:
                tree.append(LeafNode(idx.copy(), data.copy(), parent))
            else:
                splitter, left, right=self.Split(idx, data, depth % dim)
                tree.append(InnerNode(splitter, parent=parent))

                stack.append((left[0],left[1],depth+1,node_id,-1))
                stack.append((right[0],right[1],depth+1,node_id,1))

        self.tree=tree

        # add the bounding boxes
        self.AddAttribute(AttributeBB())

    def __str__(self):
        ss=[n.__str__() for n in self.tree]
        return '\n'.join(ss)

    def getNode(self, i):
        return self.tree[i]

    def nNode(self):
        return len(self.tree)

    def __iter__(self):
        return self.tree

    def AddAttribute(self, att):
        '''add a attribute for node. this process should be able to be
        done recursively.

        att: the class that appendthe attribute. it should contain a
        method SetStat(node, children_nodes). SetStat() set attribute
        for each node. for leaves children_nodes will be None. an
        example of att is AttributeBB.
        '''

        log.debug('Adding attribute {0}'.format(att))

        tree=self.tree
        for i in range(self.nNode()-1, -1, -1):
            node=tree[i]
            if isinstance(node, LeafNode):
                att.SetAttribute(node)
            else:
                att.SetAttribute(node, (tree[node.left_child],
                                        tree[node.right_child]))

    def QueryKNN(self, point, K):
        '''search for the KNN of point in this tree. 

        return a matrix [idx of knn; distances]
        '''

        # result
        knn=zeros((2, K)) # [idx; dist]
        knn[:]=inf

        # use a stack to realize 
        stack=[self.tree[0]]
        nodes_accessed=1
        leaves_accessed=0
        while len(stack) > 0:
            node=stack.pop()

            if isinstance(node, LeafNode):
                leaves_accessed += 1

                dist2 = ((node.data - point)**2).sum(1)
                sidx = argsort(dist2)[:min(K, dist2.size)]
                
                # if sth in this leaf is better than current
                if dist2[sidx[0]] < knn[1, -1]:
                    # get the actual data index
                    tnn = vstack((node.idx[sidx], dist2[sidx]))
                    # merge and update the top list
                    knn=hstack((knn, tnn))
                    sidx=argsort(knn[1, :])
                    knn=knn[:, sidx[:K]]
            else:
                nodes_accessed += 1

                if Intersects_SphereBox((point, knn[1, -1]),
                                        node.left_bb):
                    stack.append(self.tree[node.left_child])
                if Intersects_SphereBox((point, knn[1, -1]),
                                        node.right_bb):
                    stack.append(self.tree[node.right_child])

                # adjust the order for faster pruning
                if leaves_accessed == 0 and point[node.splitter[0]] < node.splitter[1]:
                    stack[-2], stack[-1] = stack[-1], stack[-2]

        log.debug('{0} leaves and {1} nodes accessed out of {2}'.format(leaves_accessed, nodes_accessed, self.nNode()))

        knn[1]=sqrt(knn[1])
        return knn

    def QuerySphere(self, s):
        '''search all the points within sphere s

        return a matrix [idx of knn; distances]
        '''

        result=[]

        stack=[self.tree[0]]
        nodes_accessed = 1
        leaves_accessed = 0
        while len(stack) > 0:
            node=stack.pop()

            if isinstance(node, LeafNode):
                leaves_accessed += 1

                idx, dist = Inside_Sphere(node.data, s)
                result.append(vstack((node.idx[idx], dist)))
            else:
                nodes_accessed += 1

                if Intersects_SphereBox(s, node.left_bb):
                    stack.append(self.tree[node.left_child])
                if Intersects_SphereBox(s, node.right_bb):
                    stack.append(self.tree[node.right_child])

        log.debug('{0} leaves and {1} nodes accessed out of {2}'.format(leaves_accessed, nodes_accessed, self.nNode()))

        result = hstack(result)
        result[1] = sqrt(result[1])
        return result

    def QueryBox(self, b):
        result=[]

        stack=[self.tree[0]]
        nodes_accessed = 1
        leaves_accessed = 0
        while len(stack) > 0:
            node=stack.pop()

            if isinstance(node, LeafNode):
                leaves_accessed += 1

                idx, dist=Inside_Box(node.data, b)
                result.append(vstack((node.idx[idx], dist)))
            else:
                nodes_accessed += 1

                if Intersects_BoxBox(b, node.left_bb):
                    stack.append(self.tree[node.left_child])
                if Intersects_BoxBox(b, node.right_bb):
                    stack.append(self.tree[node.right_child])

        log.debug('{0} leaves and {1} nodes accessed out of {2}'.format(leaves_accessed, nodes_accessed, self.nNode()))

        result = hstack(result)
        result[1] = sqrt(result[1])
        return result

class AttributeBB:
    '''a class that provide minimum bounding box for each node in
    kdtree.
    '''

    def SetAttribute(self, node, children=None):
        if children is None:
            node.bb = BB(node.data)
        else:
            bbs=[n.bb for n in children]
            node.bb=MergeBB(bbs)

            node.left_bb=bbs[0]
            node.right_bb=bbs[1]
            for n in children: del n.bb

if __name__=='__main__':

    InitLog()

    gridsize=50
    X, Y=MeshGrid(range(gridsize), range(gridsize))
    leaf_size=10

    data=hstack((col(X), col(Y))).astype(float32)
    tree=KDTree(data, leaf_size)

    test(tree.getNode(0).bb == arr([[0.,0],[gridsize - 1,gridsize - 1]]), 'KDTree with Bounding box')

    test(tree.QueryKNN(arr([1., 1]), 5)[1][1:] == 1, 'QueryKNN')

    center=arr([1, 1.])
    test(tree.QuerySphere((center,1.1)).shape[1] == 5, 'QueryRegion circle')
    test(tree.QuerySphere((center,0.9)).shape[1] == 1, 'QueryRegion circle')
    test(tree.QueryBox(center + arr([[-1.1, -1.1],[1.1, 1.1]])).shape[1] == 9, 'QueryRegion box')
    test(tree.QueryBox(center + arr([[-0.9, -1.1],[0.9, 1.1]])).shape[1] == 3, 'QueryRegion box')
