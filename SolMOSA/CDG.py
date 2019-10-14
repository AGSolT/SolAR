import pprint, configparser, os, json, re, copy, logging
import numpy as np
from evm_cfg_builder.cfg import CFG

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
    """
    node_id     = ("", 0)
    start_pc    = 0
    end_pc      = 0
    basic_blocks   = []
    inc_node_ids   = []
    outg_node_ids  = []

    def __init__(self, _node_id, _start_pc, _end_pc, _basic_blocks, _inc_node_ids, _outg_node_ids):
        self.node_id = _node_id
        self.start_pc = _start_pc
        self.end_pc = _end_pc
        self.basic_blocks = _basic_blocks
        self.inc_node_ids = _inc_node_ids
        self.outg_node_ids = _outg_node_ids

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

class CDG():
    """
    A control-dependency-graph object created using the evm_cfg_builder tool.
    Properties:
        - name: The name of the corresponding Smart Contract.
        - CompactNodes: A list of all the CompactNodes in the CDG.
        - CompactEdges: A list of all the CompactEdges in the CDG.
        - StartNodes: The CompactNodes that are the start of a method.
    """
    name = ""
    CompactNodes = []
    CompactEdges  = []
    StartNodes  = []

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
        s = []
        simple_E = []
        for method in cfg.functions:
            node_ctr = 0
            N, method_sEdges = self.Compactify_method(method, node_ctr, cfg.basic_blocks, [], N, [])
            simple_E = simple_E + method_sEdges
        N = self.Add_incoming_outgoing_node_ids(N, simple_E)
        E, s = self.Find_Compact_Edges_StartPoints(N, _predicates)
        N, E = self.Select_Relevant(N, E)
        E = list(self.CFG_to_CDG(N, E))
        self.name = _name
        self.CompactNodes = N
        self.CompactEdges = E
        self.StartNodes = s

    def Select_Relevant(self, cNodes, cEdges):
        """
        During compilation of Solidity code, extra nodes are created that check whether arguments are valid and if data is stored properly, these are not of interest to our control-dependency-graph and can be safely removed.
        Inputs:
            - cNodes: the compact nodes of the compactified CFG.
            - cEdges: the compact edges of the compactified CFG.
        Outputs:
            - relNodes: the relevant compact nodes.
            - relEdges: the relevant compact edges.
        """
        mergeNodes = []
        relNodes = []
        for cNode in cNodes:
            if (cNode.basic_blocks[-1].instructions[-1].name == "REVERT") & (cNode.node_id[0] != '_dispatcher') & (cNode.node_id[0] !=
            '_fallback'):
                for incNode in [iNode for iNode in cNodes if iNode.node_id in cNode.inc_node_ids]:
                    incNode.outg_node_ids.remove(cNode.node_id)
                    mergeNodes = mergeNodes + [incNode]
            else:
                relNodes = relNodes + [cNode]
        relEdges = [cEdge for cEdge in cEdges if cEdge.endNode_id in [cNode.node_id for cNode in relNodes]]

        for mergeNode in list(reversed(mergeNodes)):
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

    def CFG_to_CDG(self, cNodes, cEdges):
        """
        Converts a Compactified CFG to a CDG
        Inputs:
            - cNodes: The nodes of the compactified CFG
            - cEdges: The edges of the compactified CFG
        Outputs:
            - CDG_Edges: The edges of the CDG
        """
        sNode = next((cNode for cNode in cNodes if cNode.node_id == ("_dispatcher", 1)), None)
        # sNode = The first Node that has a branch. What to do if there are no branches?
        CDG_Edges = self.Find_Control_Dependencies(sNode, None, cNodes, cEdges, set(), sNode.node_id)
        return CDG_Edges

    def Find_Control_Dependencies(self, curNode, firstChild, cNodes, cEdges, CDG_Edges, startNode_id):
        """
        Recursively finds the control dependencies in the CFG and creates edges accordingly.
        Inputs:
            - curNode: the current node whose control dependency is being found.
            - prev_Node: the last node whose control dependency was being found.
            - cNodes: The nodes of the CFG.
            - CDG_Edges: The current set of CDG edges.
            - startNode_id: The node dominating the current node.
        Outputs:
            - CDG_Edges: The edges of the CDG.
        """
        if len(curNode.outg_node_ids) == 0:
            predicate = next((cEdge.predicate for cEdge in cEdges if (cEdge.startNode_id == startNode_id) & (cEdge.endNode_id == firstChild.node_id)), None)
            new_Edge = CompactEdge(startNode_id, curNode.node_id, predicate)
            return CDG_Edges.union({new_Edge})
        elif len(curNode.outg_node_ids) > 1:
            assert len(curNode.outg_node_ids) == 2, "A Node exists with more than 2 outgoing nodes: {}".format(curNode.node_id)
            child1 = next((cNode for cNode in cNodes if (cNode.node_id) == curNode.outg_node_ids[0]), None)
            child2 = next((cNode for cNode in cNodes if (cNode.node_id) == curNode.outg_node_ids[1]), None)
            if curNode.node_id == startNode_id:
                return CDG_Edges.union(self.Find_Control_Dependencies(child1, child1, cNodes, cEdges, CDG_Edges, curNode.node_id), self.Find_Control_Dependencies(child2, child2, cNodes, cEdges, CDG_Edges, curNode.node_id))
            else:
                predicate = next((cEdge.predicate for cEdge in cEdges if (cEdge.startNode_id == startNode_id) & (cEdge.endNode_id == firstChild.node_id)), None)
                new_Edge = CompactEdge(startNode_id, curNode.node_id, predicate)
                return CDG_Edges.union({new_Edge}, self.Find_Control_Dependencies(curNode, child1, cNodes, cEdges, CDG_Edges, curNode.node_id), self.Find_Control_Dependencies(curNode, child2, cNodes, cEdges, CDG_Edges, curNode.node_id))
        else:
            child = next((cNode for cNode in cNodes if cNode.node_id in curNode.outg_node_ids), None)
            assert child is not None, "There should be a child node here!"
            predicate = next((cEdge.predicate for cEdge in cEdges if (cEdge.startNode_id == startNode_id) & (cEdge.endNode_id == firstChild.node_id)), None)
            new_Edge = CompactEdge(startNode_id, curNode.node_id, predicate)
            return CDG_Edges.union({new_Edge}, self.Find_Control_Dependencies(child, firstChild, cNodes, cEdges, CDG_Edges, startNode_id))

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
            - bbs: The basic blocks of the control-flow-graph that have not yet been added to a CompactNode.
        Outputs:
            - bb: The basic block that will be the start of the next CompactNode
            - bbs: The basic blocks that have not yet been added to any CompactNode and cannot be put into the CompactNode under creation.
            - rbbs: The basic blocks that have been removed from bbs and cannot be added to any other CompactNode anymore.
        """
        for i, bb in enumerate(method.basic_blocks):
            illegal_inc_bbs = [x for x in method.basic_blocks if x not in rbbs]
            if (not bb in rbbs) & (not any([x in illegal_inc_bbs for x in bb.incoming_basic_blocks(method.key)])):
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
                eval, pc = self.Find_Predicate(cNode.basic_blocks[-1], predicates)
                predicate = Predicate(eval, pc, cNode.node_id)
                E = E + [CompactEdge(inc_node_id, outg_node_id, predicate)]
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
        for i, inst in enumerate(bb.instructions):
            if inst.name in predicates:
                eval = inst.name
                pc = inst.pc
                return eval, pc
        for i, inst in reversed(list(enumerate(bb.instructions))):
            if inst.name == "ISZERO":
                eval = inst.name
                pc = inst.pc
                return eval, pc
        eval = "NONE"
        pc = bb.start.pc
        return eval, pc

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
