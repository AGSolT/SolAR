import pprint, configparser, os, json, re, copy, logging
import numpy as np
from evm_cfg_builder.cfg import CFG
from operator import itemgetter, attrgetter

class CompactNode():
    """
    A node in a control-dependency-graph.
    Properties:
        - node_id: An id of the node, consisting of the method name and a number that increases the deeper in a method the node is.
        - start_pc: The pc of first Opcode in the CompactNode.
        - end_pc: The pc of the last Opcode in the CompactNode.
        - basic_blocks: The list of basic_blocks that are in the CompactNode.
        - inc_node_ids: The node_id's of CompactNodes that have edges leading into this node.
        - outg_node_ids: The node_id's of CompactNodes that are connected to this Node through outgoing Edges.
        - predicate: The predicate in this node that is controlling any Edges leaving from it in the CDG.
        - semi: The semidominator, used for the Lengauer-Tarjan algorithm.
        - bucket: The set of nodes for which this node is the semidominator
        - dom: The immediate dominator of this node.
        - ancestor: one of the ancestors of the vertex, used for the Lengauer-Tarjan algorithm
    """
    node_id     = ("", 0)
    start_pc    = 0
    end_pc      = 0
    basic_blocks   = []
    inc_node_ids   = []
    outg_node_ids  = []
    predicate      = None
    semi           = 0
    bucket         = set()
    dom            = None
    ancestor       = None
    label          = None

    def __init__(self, _node_id, _start_pc, _end_pc, _basic_blocks, _inc_node_ids, _outg_node_ids, _predicate=None, _semi=0, _bucket=set(), _dom=None):
        self.node_id = _node_id
        self.start_pc = _start_pc
        self.end_pc = _end_pc
        self.basic_blocks = _basic_blocks
        self.inc_node_ids = _inc_node_ids
        self.outg_node_ids = _outg_node_ids
        self.predicate = _predicate
        self.semi = _semi
        self.bucket = set()
        self.dom = _dom
        self.ancestor = None
        self.label = 0

    def show_CompactNode(self, log=False):
        """
        Prints all the information of the CompactNode.
        """
        info = "Node_id: {}".format(self.node_id) + "\n\tstart_pc: {}".format(self.start_pc) + "\n\tend_pc: {}".format(self.end_pc) + "\n\tincoming node ids: {}".format(self.inc_node_ids) + "\n\toutgoing node ids: {}".format(self.outg_node_ids)
        if log:
            logging.info(info)
        else:
            print(info)

class CompactEdge():
    """
    An edge in a control-dependency-graph
    Properties:
        - startNode_id: The Node_id of the starting point of the edge.
        - endNode_id: The Node_id of the end point of the edge.
        - predicate: The predicate object that controls whether this edge is traversed or not.
    """
    startNode_id    = None
    endNode_id      = None
    predicate       = None

    def __init__(self, _startNode_id, _endNode_id, _predicate):
        self.startNode_id = _startNode_id
        self.endNode_id = _endNode_id
        self.predicate = _predicate

    def __eq__(self, other):
        return ((self.startNode_id == other.startNode_id) & (self.endNode_id == other.endNode_id))

    def __hash__(self):
        return hash((self.startNode_id, self.endNode_id))

    def show_CompactEdge(self, log=False):
        """
        Shows all information of the Edge.
        """
        if self.predicate is None:
            info = "Edge from {}, to {} ".format(self.startNode_id, self.endNode_id)
        else:
            info = "Edge from {}, to {} with predicate {}".format(self.startNode_id, self.endNode_id, self.predicate.eval)
        if log:
            logging.info(info)
        else:
            print(info)

class Predicate():
    """
    A predicate that controls Edges in a control-flow-graph.
    Properties:
        - eval: The string corresponding to the Opcode of the predicate.
        - pc: The pc of the predicate in the deployed bytecode.
        - node_id: The node_id of the CompactNode in which the predicate can be found.
    """
    eval    = ""
    pc      = 0
    node_id = None

    def __init__(self, _eval, _pc, _node_id):
        self.eval = _eval
        self.pc = _pc
        self.node_id = _node_id

    def show_Predicate(self, verbose=True):
        info = "Predicate with eval: {}, at pc: {} and node_id: {}".format(self.eval, self.pc, self.node_id)
        if(verbose):
            print(info)
        else:
            return info

class CDG():
    """
    A control-dependency-graph object created using the evm_cfg_builder tool.
    Properties:
        - name: The name of the corresponding Smart Contract.
        - CompactNodes: A list of all the CompactNodes in the CDG.
        - CompactEdges: A list of all the CompactEdges in the CDG.
        - StartNodes: The CompactNodes that are the start of a method.
        - vertex: An ordered list of vertices used for the Lengauer-Tarjan algorithm.
        - n: A global counter used for the Lengauer-Tarjan algorithm
    """
    name = ""
    CompactNodes = []
    CompactEdges  = []
    StartNodes  = []
    vertex = []
    n = 0
    def __init__(self, _name, _bytecode, _predicates):
        """
        Creates a control-dependency-graph by going through all the methods in the smart contract and extracing their (start-)nodes and edges.
        Inputs:
            - _name: The name of the smart contract under investigation
            - _bytecode: The deployed bytecode of the smart contract under investigation.
            - _predicates: The relevant Opcodes for the predicates that control branches.
        """
        cfg = CFG(_bytecode)
        N = []
        bbs = cfg.basic_blocks
        s = []
        simple_E = []
        payableMethodNames = []
        for method in cfg.functions:
            N_old = N
            node_ctr = 0
            N, method_sEdges = self.Compactify_method(method, node_ctr, bbs, [], N, [])
            simple_E = simple_E + method_sEdges

            #Check if the method is payable
            if 'payable' in method.attributes:
                payableMethodNames.append(method.name)

        N = self.Add_incoming_outgoing_node_ids(N, simple_E)
        E, s = self.Find_Compact_Edges_StartPoints(N, _predicates)
        N, E = self.Payable_Check(N, E, payableMethodNames)

        self.name = _name
        self.CompactNodes = N
        self.CompactEdges = E
        self.StartNodes = s
        self.vertex = [None] * len(self.CompactNodes)
        self.n = 0

    def Payable_Check(self, cNodes, cEdges, _payableMethodNames):
        # TODO: This function should only be applied when the function is not payable, otherwise the nodes are all relevant and none should be removedb
        """
        During compilation of Solidity code, extra nodes are created that check whether arguments are valid and if data is stored properly, these are not of interest to our control-dependency-graph and can be safely removed.
        Inputs:
            - cNodes: the compact nodes of the compactified CFG.
            - cEdges: the compact edges of the compactified CFG.
        Outputs:
            - relNodes: the relevant compact nodes.
            - relEdges: the relevant compact edges.
        """
        mergeNodes = set()
        irrelNodes = set()
        for cNode in cNodes:
            # This check removes the extra reverts that result from nonpayable functions
            if (cNode.basic_blocks[-1].instructions[-1].name == "REVERT") & (cNode.node_id[0] != '_dispatcher') & (cNode.node_id[0] !=
            '_fallback') & (cNode.node_id[0] not in _payableMethodNames):
                assert len(cNode.outg_node_ids) == 0, "Node {} ends with a REVERT OpCode but also has outgoing nodes?!".format(cNode.node_id)
                isExtraNode = False
                for incNode in [iNode for iNode in cNodes if iNode.node_id in cNode.inc_node_ids]:
                    if incNode.node_id[1]==1:
                        if len(cNode.inc_node_ids)>1:
                            for inc_to_extra_Node in [iNode for iNode in cNodes if iNode.node_id in cNode.inc_node_ids]:
                                inc_to_extra_Node.outg_node_ids.remove(cNode.node_id)
                        else:
                            incNode.outg_node_ids.remove(cNode.node_id)
                        irrelNodes = irrelNodes.union(set([cNode]))
                        isExtraNode = True
                if isExtraNode:
                    cNodes, pNodes, newMergeNodes, newIrrelNodes = self.getMergeNodes(cNodes, set([pNode for pNode in cNodes if pNode.node_id in cNode.inc_node_ids]), set(), set())
                    mergeNodes = mergeNodes.union(newMergeNodes)
                    irrelNodes = irrelNodes.union(newIrrelNodes)

        relNodes = list(set(cNodes)-irrelNodes)
        relNode_ids = [relNode.node_id for relNode in relNodes]
        relEdges = [cEdge for cEdge in cEdges if (cEdge.endNode_id in relNode_ids) | (cEdge.startNode_id in relNode_ids)]
        mergeNodeids = sorted([mNode.node_id for mNode in mergeNodes], key=itemgetter(0,1), reverse=True)
        mergenodeList = sorted(list(mergeNodes), key=attrgetter('node_id'), reverse=True)

        for mergeNode in mergenodeList:
            assert len(mergeNode.outg_node_ids) == 1, "After removing a REVERT-ing node, it's parent node has {} outgoing nodes".format(len(mergeNode.outg_node_ids))
            nextNode = [nNode for nNode in cNodes if nNode.node_id in mergeNode.outg_node_ids][0]
            assert len(nextNode.inc_node_ids) == 1, "After removing a REVERT-ing node the other child of it's parent still had {} incoming nodes".format(len(nextNode.inc_node_ids))

            mergeNode.end_pc = nextNode.end_pc
            mergeNode.basic_blocks = mergeNode.basic_blocks + nextNode.basic_blocks
            mergeNode.outg_node_ids = nextNode.outg_node_ids

            relEdges = [relEdge for relEdge in relEdges if relEdge.startNode_id != mergeNode.node_id]

            for relEdge in relEdges:
                if (relEdge.startNode_id == nextNode.node_id) & (relEdge.startNode_id[0] !='_dispatcher'):
                    relEdge.startNode_id = mergeNode.node_id

            relNodes = [relNode for relNode in relNodes if (relNode.node_id != mergeNode.node_id) & (relNode.node_id != nextNode.node_id)]
            for relNode in relNodes:
                if nextNode.node_id in relNode.inc_node_ids:
                    relNode.inc_node_ids.remove(nextNode.node_id)
                    relNode.inc_node_ids = relNode.inc_node_ids + [mergeNode.node_id]
            relNodes = relNodes + [mergeNode]

        return relNodes, relEdges

    def getMergeNodes(self, _cNodes, _pNodes, _mergeNodes, _irrelNodes):
        """
        The mergenodes are those nodes who have exactly two children: one child is relevant and the other child will be part of a single branch that leads to REVERT and is therefore irrelevant.
        This function looks at all the parents of child that is part of a single branch that leads to a REVERT and checks whether they are mergenodes, or if they are irrelevant in which case their parents might be mergenodes
        At the same time, this function removes childNodes from the mergedNodes and in doing so updates cNodes.
        Inputs:
            _cNodes: the current list of compactNodes
            _pNodes: the current list of parent Nodes that are potentially mergenodes
            _mergeNodes: the currently identified mergenodes
            _irrelNodes: the currently identified irrelevant nodes
        Outputs:
            see Inputs
        """
        if not bool(_pNodes):
            # If _pNodes is the emptyset
            return _cNodes, set(), _mergeNodes, _irrelNodes
        pNode = _pNodes.pop()
        if len(pNode.outg_node_ids)>1:
            # The parent node has multiple children after removing the irrelevant child
            return self.getMergeNodes(_cNodes, _pNodes, _mergeNodes, _irrelNodes)
        elif len(pNode.outg_node_ids)>0:
            # The parent has exactly 1 child after removing the irrelevant child, therefore it could potentially be merged
            assert len(pNode.outg_node_ids) == 1, "After removing a REVERT-ing node, it's parent node has {} outgoing nodes".format(len(pNode.outg_node_ids))
            nextNode = [nNode for nNode in _cNodes if nNode.node_id in pNode.outg_node_ids][0]
            if len(nextNode.inc_node_ids) > 1:
                # The parents only child has multiple parents, no merging is needed.
                return self.getMergeNodes(_cNodes, _pNodes, _mergeNodes, _irrelNodes, _irrelNodes)
            else:
                # The parent's only child has only one parent: they should be merged
                return self.getMergeNodes(_cNodes, _pNodes, set([pNode]).union(_mergeNodes), _irrelNodes)
        else:
            # The parent has 0 children after removing the irrelevant child: it is itself irrelevant
            irrelNodes = _irrelNodes.union(set([pNode]))
            nextpNodes = [npNode for npNode in _cNodes if npNode.node_id in pNode.outg_node_ids]
            for nextpNode in nextpNodes:
                nextpNode.outg_node_ids.remove(pNode.node_id)
            pNodes = _pNodes.union(set(nextpNodes))
            return self.getMergeNodes(_cNodes, pNodes, _mergeNodes, irrelNodes)

    def Compactify_method(self, method, node_ctr, bbs, rbbs, compactNodes, simple_edges):
        """
        Extracts the compactified nodes and a first version of the edges between them in a recursive manner for a given method.
        Inputs:
            - method: A function object of the control-flow-graph
            - node_ctr: Counts the number of nodes in this method and gives them a unique id.
            - bbs: The basic blocks of the control-flow-graph that have not yet been added to a CompactNode.
            - rbbs: The basic blocks of the control-flow-graph that have been removed from bbs because they have been added to a CompactNode
            - compactNodes: A list of the CompactNodes that have been created for this method.
            - simple_edges: A list of edges identified by a starting CompactNode_id and the start_pc's of the next basic_block
        Outputs:
            - compactNodes: A list of all the CompactNodes in this method.
            - simple_edges: A list of edges with starting point denoted by the corresponding CompactNode_id and end point denoted by the start_pc of the corresponding basic_block.
        """
        sb, bbs, rbbs, found = self.Find_Starting_Node(method, bbs, rbbs)
        node_ctr += 1
        if found == False:
            assert(len(rbbs)==len(method.basic_blocks)), "No starting blocks were found but there are stil basic blocks that should be added to the control-dependency-graph!"
            return compactNodes, simple_edges
        else:
            start_pc = sb.start.pc
            bbs, rbbs, end_pc, basic_blocks, outg_node_startpcs = self.Compactify_Basic_Blocks(method, sb, bbs, rbbs, [])
            node_id = (method.name, node_ctr)
            simple_edges = simple_edges + [(node_id, outg_node_startpcs)]
            compactNodes = compactNodes + [CompactNode(node_id, start_pc, end_pc, basic_blocks, [], [])]
            return self.Compactify_method(method, node_ctr, bbs, rbbs, compactNodes, simple_edges)

    def Find_Starting_Node(self, method, bbs, rbbs):
        """
        Finds the next basic_block that can be reached by any of the CompactNodes that have already been created within the method. Or returns None, if no such basic_block can be found.
        Inputs:
            - method: A function object of the control-flow-graph
            - node_ctr: Counts the number of nodes in this method and gives them a unique id.
            - bbs: The basic blocks of the control-flow-graph that have not yet been added to a CompactNode of any method.
            - rbbs: The basic blocks that have been removed from bbs and cannot be added to any other CompactNode anymore.
        Outputs:
            - bb: The basic block that will be the start of the next CompactNode
            - bbs: The basic blocks that have not yet been added to any CompactNode of any method and can be put into the CompactNode under creation.
            - rbbs: The basic blocks that have been removed from bbs and cannot be added to any other CompactNode anymore afte this function has run.
        """
        for i, bb in enumerate(method.basic_blocks):
            illegal_inc_bbs = [x for x in method.basic_blocks if x not in rbbs]
            bb_not_removed = not bb in rbbs
            bb_is_reachable = not all([x in illegal_inc_bbs for x in bb.incoming_basic_blocks(method.key)])
            bb_has_no_incoming_blocks = len(bb.incoming_basic_blocks(method.key)) == 0
            if bb_not_removed & (bb_is_reachable | bb_has_no_incoming_blocks):
                bbs.remove(bb)
                rbbs = rbbs + [bb]
                return bb, bbs, rbbs, True
        return None, bbs, rbbs, False

    def Compactify_Basic_Blocks(self, method, cb, bbs, rbbs, Cbbs):
        """
        Identifies all basic_blocks that should form a CompactNode together.
        Inputs:
            - method: A function object of the control-flow-graph
            - cb: The most recent basic_block that should be added to the CompactNode.
            - bbs: The basic blocks of the control-flow-graph that have not yet been added to a CompactNode.
            - rbbs: The basic blocks of the control-flow-graph that have been removed from bbs because they have been added to a CompactNode.
            - Cbbs: A list of all the basic_blocks that should be added to this CompactNode.
        Outputs:
            - bbs: The basic blocks that have not yet been added to any CompactNode and cannot be put into the CompactNode under creation.
            - rbbs: The basic blocks that have been removed from bbs and cannot be added to any other CompactNode anymore.
            - end_pc: The last pc of the newly formed CompactNode.
            - Cbbs: The basic blocks that are a part of this CompactNode.
            - outg_bb_startpcs: The start_pc's of all the basic blocks that are connected by an edge to the end of the CompactNode.
        """
        if len(cb.outgoing_basic_blocks(method.key))!=1:
            end_pc = cb.end.pc
            Cbbs = Cbbs + [cb]
            outg_bb_startpcs = [bb.start.pc for bb in cb.outgoing_basic_blocks(method.key)]
            return bbs, rbbs, end_pc, Cbbs, outg_bb_startpcs
        else:
            nbb = cb.outgoing_basic_blocks(method.key)[0]
            if len(nbb.incoming_basic_blocks(method.key))>1:
                end_pc = cb.end.pc
                Cbbs = Cbbs + [cb]
                outg_bb_startpcs = [bb.start.pc for bb in cb.outgoing_basic_blocks(method.key)]
                return bbs, rbbs, end_pc, Cbbs, outg_bb_startpcs
            else:
                new_bbs = bbs.copy()
                new_bbs.remove(nbb)
                rbbs = rbbs + [nbb]
                Cbbs = Cbbs + [cb]
                return self.Compactify_Basic_Blocks(method, nbb, new_bbs, rbbs, Cbbs)

    def Add_incoming_outgoing_node_ids(self, compactNodes, simple_edges):
        """
        After all the CompactNodes have been identified, the correct incoming- and outgoing_node_ids can be added to the CompactNodes
        Inputs:
            - compactNodes: the list of all the CompactNodes in this control-dependency-graph
            - simple_edges: A list of edges identified by a starting CompactNode_id and the start_pc's of the next basic_block.
        Outputs:
            - compactNodes: the CompactNodes in this control-flow-graph with updated incoming- and outgoing_node_ids.
        """
        for sEdges in simple_edges:
            for sEdge in sEdges[1]:
                startNode = next((cNode for cNode in compactNodes if cNode.node_id == sEdges[0]), None)
                endNode = next((cNode for cNode in compactNodes if cNode.start_pc == sEdge), None)
                startNode.outg_node_ids.append(endNode.node_id)
                endNode.inc_node_ids.append(startNode.node_id)
        return compactNodes

    def Find_Compact_Edges_StartPoints(self, cNodes, predicates):
        """
        Goes through all the CompactNodes in the control-dependency-graph and identifies the corresponding CompactEdges.
        Inputs:
            - cNodes: The CompactNodes of the control-dependency-graph
            - predicates: The relevant Opcodes for the predicates that control branches.
        Outputs:
            - E: The CompactEdges of the control-dependency-graph
            - s: The startNodes of the control-dependency-graph
        """
        E = []
        s = set()

        for cNode in cNodes:
            for outg_node_id in cNode.outg_node_ids:
                inc_node_id = cNode.node_id
                E = E + [CompactEdge(inc_node_id, outg_node_id, None)]
                if len(cNode.inc_node_ids) == 0:
                    s.add(cNode)

        return E, s

    def Find_Predicate(self, bb, predicates):
        """
        Finds the predicate that controls whether a certain edge is traversed or not by looking at the Opcodes in the last basic_block executed before the Edge could be traveled.
        Inputs:
            - bb: The last basic_block in the node that starts the edge.
            - predicates: The relevant Opcodes for the predicates that control branches.
        Outputs:
            - eval: A string describing the predicate that controls whether the Edge is traversed or not.
            - pc: The pc where the eval is present in the deployed bytecode.
        TODO: This method might not always work and warrents more investigation. Specifically a problem might be that a boolean b_1 is already on the stack when a new Opcode is executed that pushes another boolean b_2 onto the stack and the booleans could then be switched. This is definitely not the case for the contracts that I tested on but could still be relevant.
        """
        # First we look from front to back for a valid Predicate
        for i, inst in enumerate(bb.instructions):
            if inst.name in predicates:
                eval = inst.name
                pc = inst.pc
                return eval, pc
        # Then we look backwards for ISZERO
        for i, inst in reversed(list(enumerate(bb.instructions))):
            if inst.name == "ISZERO":
                eval = inst.name
                pc = inst.pc
                return eval, pc
        # If neither are found the predicate is NONE
        eval = "NONE"
        pc = bb.start.pc
        return eval, pc

    def LT(self, predicates):
        # Create the spanning Tree using Depth-First-Search
        self.DFS(next(sNode for sNode in self.StartNodes))
        self.n -=1

        # While creating the CDG a we keep track of a forest which is initialised here. This is the equivalen of LINK.
        forestEdges = set()

        # Find semidominators and initialise immediate dominators
        for i in range(self.n, 0, -1):
            w = self.vertex[i]
            w.label = i
            # Finding semidominators
            for v_id in w.inc_node_ids:
                v = next((compactNode for compactNode in self.CompactNodes if compactNode.node_id == v_id), None)
                assert v is not None, "No Node was found from the list of incoming nodes!"
                u = self.EVAL(v)
                if u.semi<w.semi:
                    w.semi = u.semi

            # Add w to the bucket of its semidominator
            self.vertex[w.semi].bucket.add(w)
            newEdge = next((cEdge for cEdge in self.CompactEdges if (cEdge.startNode_id == w.parent.node_id) & (cEdge.endNode_id == w.node_id)), None)
            assert newEdge is not None, "No Edge was found between a node and its parent!" # Maybe a new Edge should be created here instead. I wouldn't be surprised if this would start yielding errors.
            forestEdges.add(newEdge)
            w.ancestor = w.parent
            w.label = i

            # Initialise immediate dominators
            parent_bucket = w.parent.bucket.copy()
            for v in parent_bucket:
                w.parent.bucket.remove(v)
                u = self.EVAL(v)

                if u.semi<v.semi:
                    v.dom = u
                else:
                    v.dom = w.parent

        # Finally find immediate dominators not found in previous step
        for w in self.vertex[1:]:
            if w.dom != self.vertex[w.semi]:
                w.dom = w.dom.dom
            # The outgoing_node_ids will be set later on.
            w.outg_node_ids = []
            # Set the predicates of each node
            e, pc = self.Find_Predicate(w.basic_blocks[-1], predicates)
            predicate = Predicate(e, pc, w.node_id)
            w.predicate = predicate

        # Do the same for the root node
        self.vertex[0].dom = None
        self.vertex[0].outg_node_ids = []
        e, pc = self.Find_Predicate(self.vertex[0].basic_blocks[-1], predicates)
        predicate = Predicate(e, pc, self.vertex[0].node_id)
        self.vertex[0].predicate = predicate

        # The incoming and outgoing node_ids can be set by using the dom_ids, the edges go from each node to their dominator
        Edges = []
        for i in range(self.n, 0, -1):
            self.vertex[i].inc_node_ids = [self.vertex[i].dom.node_id]
            self.vertex[i].outg_node_ids = [cNode.node_id for cNode in self.vertex if cNode.dom == self.vertex[i]]
            assert self.vertex[i].dom is not None, "There is a non-root node without an immediate dominator!"
            Edges = Edges + [CompactEdge(self.vertex[i].dom.node_id, self.vertex[i].node_id, self.vertex[i].dom.predicate)]

        self.vertex[0].outg_node_ids = [cNode.node_id for cNode in self.vertex if cNode.dom == self.vertex[0]]

        # The Compactnodes are now equal to self.vertex
        assert len(self.CompactNodes) == len(self.vertex), "There is a different number of nodes in self.CompactNodes ({}) than in vertex ({})".format(len(self.compactNodes), len(self.vertex))
        self.CompactNodes = self.vertex

        # The CompactNodes are equal to the edges from the forest
        self.CompactEdges = Edges

    def DFS(self, v):
        """
        Depth-First Search
        inputs:
            -
        """
        v.semi = self.n
        self.vertex[self.n] = v
        self.n+=1
        for w_id in v.outg_node_ids:
            w = next((compactNode for compactNode in self.CompactNodes if compactNode.node_id == w_id), None)
            if w is None:
                v.show_CompactNode()
            assert w is not None, "No child node was found!"
            if w.semi == 0:
                w.parent = v
                self.DFS(w)
                assert v.node_id in w.inc_node_ids, "Something went wrong with the Incoming Node ids!"

    def EVAL(self, _v,):
        if _v.ancestor is None:
            return _v
        else:
            self.COMPRESS(_v)
            return self.vertex[_v.label]

    def COMPRESS(self, _v):
        if _v.ancestor.ancestor is not None:
            self.COMPRESS(_v.ancestor)
            if self.vertex[_v.ancestor.label].semi<self.vertex[_v.label].semi:
                _v.label = _v.ancestor.label
            _v.ancestor = _v.ancestor.ancestor

    def Show_CDG(self, log=False):
        if log:
            logging.info("Nodes:")
            for cNode in self.CompactNodes:
                cNode.show_CompactNode(True)
            logging.info("Edges:")
            for cEdge in self.CompactEdges:
                cEdge.show_CompactEdge(True)
        else:
            print("Nodes:")
            for cNode in self.CompactNodes:
                cNode.show_CompactNode()
            print("Edges:")
            for cEdge in self.CompactEdges:
                cEdge.show_CompactEdge()
