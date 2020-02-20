"""A class that represents all the relevant non-changing properties of a \
smart contract."""

import numpy as np
import logging


class SmartContract():
    """
    A class that represents all the relevant non-changing properties of a \
    smart contract.

    Properties:
        - contractName:     The name of the smart contract.
        - methods:          A list of all methods in the smart contract.
        - CDG:              The control-dependency-graph of the smart contract.
        - approach_levels:  A matrix containg the approach levels between any
                            two nodes. The index of the matrix contains the
                            maximum approach level for that edge.
    """

    contractName = ""
    methods = []
    CDG = None
    approach_levels = None

    def __init__(self, contract_json, _cdg, _ignorefunctionNames):
        """Initialise a smart contract."""
        self.contractName = contract_json['contractName']
        methods = []
        for method in contract_json['abi']:
            if method['type'] == 'function':
                fullName = method['name'] + "("
                for i, inputvar in enumerate(method["inputs"]):
                    if i > 0:
                        fullName = fullName + ","
                    fullName = fullName + inputvar["type"]
                fullName = fullName + ")"
                if fullName not in _ignorefunctionNames:
                    methods = methods + [method]
            elif method['type'] == 'constructor':
                # The constructor is always the first method in the list.
                methods = [method] + methods

        # Check if there is a constructor now
        found = False
        for i, poss_method in enumerate(methods):
            if poss_method['type'] == 'constructor':
                # A modern smart contract with a constructor.
                methods.insert(0, methods.pop(i))
                found = True
                break
            elif poss_method['name'] == contract_json['contractName']:
                # An old fashioned smart contract,
                # we rename stuff to constructor.
                poss_method['name'] = 'constructor'
                assert poss_method['type'] == 'constructor', \
                    "A function was found with the same name as the contract \
                    but without the constructor type, instead it has type: \
                    {}".format(poss_method['type'])
                methods.insert(0, methods.pop(i))
                found = True
                break

        if not found:
            # A smart contract without constructor,
            # we create an artificial constructor.
            logging.info("No constructor was found, "
                         "inserting an empty constructor")
            methods.insert(0, {
                "inputs": [],
                "payable": False,
                "stateMutability": "nonpayable",
                "type": "constructor"
            })

        self.methods = methods
        self.CDG = _cdg
        cEdges = _cdg.CompactEdges

        # The approach levels: the approach level for the j-th edge
        # to the i-th edge is stored in app_lvls[i][j].
        # The trace contains the maximal approach level
        # (i.e. the approach level from the start of the corresponding method.)
        app_lvls = np.zeros(shape=(len(cEdges), len(cEdges)))
        rootNode_id = next(sNode.node_id for sNode in _cdg.StartNodes)
        for i, cEdge1 in enumerate(cEdges):
            startNode = next(cNode for cNode in _cdg.CompactNodes if
                             cNode.node_id == cEdge1.startNode_id)
            queue = [(startNode, 0)]
            # if cEdge1.startNode_id[0] != "_dispatcher":
            #     queue = [(startNode, 0) for startNode in
            #              _cdg.CompactNodes if (cEdge1.startNode_id[0], 1) in
            #              startNode.outg_node_ids]
            # else:
            #     queue = [(startNode, 1) for startNode in
            #              _cdg.CompactNodes if startNode.node_id ==
            #              (cEdge1.startNode_id[0], 1)]
            assert len(queue) == 1, \
                "There should be precisely one starting node, instead "\
                f"we found {len(queue)}."
            traversed = [cNode[0].node_id for cNode in queue]

            max_al = self.max_approach_level(
                queue, _cdg.CompactNodes, traversed, rootNode_id)

            app_lvls[i][i] = max_al
            for j, cEdge2 in enumerate(cEdges):
                if i == j:
                    pass
                else:
                    startNode = next(
                        (cNode for cNode in _cdg.CompactNodes if
                         cNode.node_id == cEdge2.endNode_id), None)
                    queue = [(startNode, 0)]
                    traversed = [cNode[0].node_id for cNode in queue]
                    al = self.approach_level(queue, _cdg.CompactNodes,
                                             cEdge1, traversed, max_al)
                    app_lvls[j][i] = al
        self.approach_levels = app_lvls

    def max_approach_level(self, queue, cNodes, traversed, _rootNode_id):
        """
        Find the maximum approach level of a single node (i.e, the number \
        of nodes between it and the root node).

        Arguments:
            - queue:            A queue consisting of all the next nodes to
                                visit.
            - cNodes:           A list of all the CompactNodes in the
                                control-dependency-graph.
            - traversed:        A list of nodes that have already been
                                traversed by the depth-first algorithm.
        Outputs:
            - max_al:           The maximum approach level of the first
                                traversed node.
        """
        assert len(queue) != 0, "When finding the maximum approach level "\
            "the queue can never be 0."
        curNode, depth = queue.pop(0)
        assert curNode.node_id in traversed, \
            "A node is has been popped from the queue but it is not "
        "registered as traversed: node with id: {}".format(curNode.node_id)

        if curNode.node_id == _rootNode_id:
            # Max approach level is depth.
            return depth
        else:
            parentNodes = [cNode for cNode in cNodes if
                           (cNode.node_id not in traversed) &
                           (cNode.node_id in curNode.inc_node_ids)]
            traversed = traversed + [cNode.node_id for cNode in parentNodes]
            queue = queue + [(parentNode, depth + 1) for
                             parentNode in parentNodes]
            return self.max_approach_level(
                queue, cNodes, traversed, _rootNode_id)

    def approach_level(self, queue, cNodes, goal, traversed, max_al=None):
        """
        Find either the maximum approach level of a single node (i.e. the \
        approach level from the start of a function or the approach level \
        from one edge to another) using a breadth-first search algorithm.

        Arguments:
            - queue:            A queue consisting of all the next nodes to
                                visit.
            - cNodes:           A list of all the CompactNodes in the
                                control-dependency-graph.
            - goal:             The edge that we're calculating the approach
                                level for.
            - traversed:        A list of nodes that have already been
                                traversed by the depth-first algorithm.
            - max_al:           The maximum approach level of the goal,
                                (i.e. the approach level from the start of a
                                function or the approach level from one edge to
                                another).
        Outputs:
            - max_al/depth+1:   The approach level of the goal.
        """
        if len(queue) == 0:
            assert max_al is not None, \
                "End of the queue was reached but no maximum approach level " \
                "was passed!"
            return max_al

        curNode, depth = queue.pop(0)
        assert curNode.node_id in traversed, \
            "A node is being investigated but it is not registered " \
            "as traversed: node with id: {}".format(curNode.node_id)
        if max_al is not None:
            if depth >= max_al:
                # We don't need to go deeper than the maximum approach_level
                return max_al

        if curNode.node_id == goal.startNode_id:
            # The goal can be reached at this depth
            return depth
        else:
            childNodes = [cNode for cNode in cNodes if
                          (cNode.node_id not in traversed) &
                          (cNode.node_id in curNode.outg_node_ids)]
            traversed = traversed + [cNode.node_id for cNode in childNodes]
            queue = queue + [(childNode, depth + 1) for
                             childNode in childNodes]
            return self.approach_level(queue, cNodes, goal, traversed, max_al)
