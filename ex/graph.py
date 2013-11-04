from common import *
import networkx as nx

def RemoveDupEdges(edges, nNodes = None):
    '''remove duplicated undirected edges from edges
    '''

    if nNodes is None: nNodes = edges[:2].max() + 1

    code = (edges[:2].min(0) + 1)*nNodes + edges[:2].max(0)
    return edges[:, arguniqueInt(int(code))]

def RemoveSelfEdges(edges, nNodes = None):
    '''remove edges that are linking to a node itself.
    '''

    if nNodes is None: nNodes = edges[:2].max() + 1
    return edges[:, edges[0] != edges[1]]

def Edges2Graph(edges, weights = None, nNodes1=None, nNodes2=None):
    '''convert the set of edges into a graph
    '''

    if nNodes1 is None: nNodes1 = edges[0].max() + 1
    if nNodes2 is None: nNodes2 = edges[1].max() + 1

    if weights is None: weights = ones(edges.shape[1])

    return ssp.csr_matrix((weights, edges[:2]), (nNodes1, nNodes2))

def ToGraph(g, weighted = False, nNodes = None):
    '''convert a sparse matrix or edges to a networkx graph
    '''

    G = nx.Graph()
    if issparse(g):
        check(g.shape[0] == g.shape[1], 'wrong input graph')
        nNodes = g.shape[0]
        ii, jj = g.nonzero()
        G.add_nodes_from(range(nNodes))
        if weighted:
            G.add_weighted_edges_from(zip(ii, jj, g[(ii,jj)]))
        else:
            G.add_edges_from(zip(ii, jj))
    else:
        check(g.shape[0] in [2, 3], 'wrong edges')
        if nNodes is None: nNodes = g[:2].max() + 1
        G.add_nodes_from(range(nNodes))
        if weighted:
            G.add_weighted_edges_from(zip(g[0], g[1], g[2]))
        else:
            G.add_edges_from(zip(g[0], g[1]))

    return G
