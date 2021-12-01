from graph_parser import ProgParser
import matplotlib.pyplot as plt
import networkx as nx


def split_by_semicolon(input_string, v):
    in_split = input_string.split(";")
    temp = in_split[2]
    if len(in_split) > 3:
        for i in range(3, len(in_split)):
            temp += in_split[i]

    return {
        str(v) + 'a': in_split[0],
        str(v) + 'b': in_split[1],
        str(v) + 'c': temp
    }


def draw_graph(nodes, edges, back_edges, title=None, filename=None):
    """
    Graph the CFG with the current nodes and edges
    Use this only after calling ControlFlowGraph.parse()
    """
    dg = nx.DiGraph()

    dg.add_nodes_from(nodes)  # Add nodes to graph
    dg.add_edges_from(edges, color='b')  # Add edges to graph
    dg.add_edges_from(back_edges, color='r')

    # Get graph positions using Graphviz
    #pos = nx.nx_agraph.graphviz_layout(dg)
    pos = nx.nx_agraph.graphviz_layout(dg, prog="dot")

    # draw straight edges
    nx.draw_networkx_labels(dg, pos)
    nx.draw_networkx_edges(dg, pos, edgelist=edges, edge_color='r', arrows=True)
    # draw curve edges
    nx.draw_networkx_edges(dg, pos, edgelist=back_edges,
                           connectionstyle=f"arc3, rad =1.5",
                           edge_color='r', arrows=True)

    if title:
        plt.title(title)

    if filename:
        plt.savefig(filename, format="PNG")

    plt.show()


class Graph:
    def __init__(self):
        self.graph = {}
        self.nodes = []
        self.edges = []
        self.back_edges = []
        self.curr_idx = 1
        self.max_visited = 1

        # keep track of if else statement
        self.if_statement = []  # keep track of closest logical
        self.if_root = []
        self.idx_end_if = []
        self.hashmap_if = {}

        # keep track of while loops
        self.while_loop = []
        self.idx_end_loop = []

        # keep track of do while loops
        self.doloop = []
        self.idx_end_doloop = []

        # hashmap to keep track of for loops
        self.hash_for_loop = {}
        self.forloop = []
        self.idx_end_forloop = []

        self.mapping = {}
        self.list_input = []

    def find_end_index(self, i):
        idx = i
        stack = ['{']
        idx += 1
        while len(stack) > 0:
            print("LOOKING INTO---", idx)
            if '}' in self.list_input[idx][1]:
                stack.pop()
            elif '{' in self.list_input[idx][1]:
                stack.append('{')
            idx += 1
        return idx - 1

    def build_graph(self, list_input):  # List that each line of the list is a line of the code.
        i = 0
        self.list_input = [(i, list_input[i]) for i in range(len(list_input))]
        for k in range(1, len(list_input) + 1):
            self.mapping[k] = ""

        self.graph[1] = [-1]
        print(self.list_input)
        while i < len(list_input):
            line = list_input[i]
            print("Current line ---", line)
            if '}' in line:
                print("------1--------")
                self.end_logical(i)
                if i + 1 < len(list_input):
                    if i in self.idx_end_doloop:
                        self.mapping[self.curr_idx] += self.list_input[i + 1][1]
                        i += 1

            elif 'if' in line:
                print("------2a-------")
                self.build_if_else(i)

            elif 'else if' in line:
                print("------2b-------")
                self.build_if_else(i)

            elif 'else' in line:
                print("------2c-------")
                self.build_if_else(i)

            elif 'while' in line:
                print("------3-------")
                self.build_while(i, 'while')

            elif 'do' in line:
                print("------4-------")
                self.build_while(i, 'do')

            elif 'for' in line:
                print("------5-------")
                self.build_for(i)

            else:
                print("------6--------")
                self.build_assignment(i)

            i += 1
            print(self.mapping)
            print(self.graph)
            print("WHILE---", self.idx_end_loop)
            print("DO---", self.idx_end_doloop)
            print("FOR---", self.idx_end_forloop)

        for key, value in self.graph.items():
            temp = []
            for v in value:
                if v != -1:
                    if v in self.graph and v not in temp:
                        temp.append(v)
            self.graph[key] = temp

        # clean up and connect all nodes with edges
        for key, value in self.graph.items():
            if self.mapping[key] == '}':
                if key + 1 in self.mapping and key - 1 in self.mapping:
                    if self.mapping[key - 1] == '}' and '}' in self.mapping[key + 1]:
                        if key not in self.graph[key - 1]:
                            self.graph[key - 1].append(key)

        for key, value in self.graph.items():
            if type(key) == str:
                temp = ''.join(key[:-1])
            else:
                temp = key
            for v in value:
                if type(v) == str:
                    tempv = ''.join(v[:-1])
                else:
                    tempv = v
                if int(temp) <= int(tempv):
                    self.edges.append((key, v))
                elif int(temp) > int(tempv):
                    self.back_edges.append((key, v))
        # take care of nodes
        for k in self.graph.keys():
            if len(self.graph[k]) != 0:
                self.nodes.append(k)
        tempe = []
        tempbe = []
        for e in self.edges:
            if e[0] != e[1]:
                tempe.append(e)

        for be in self.back_edges:
            if be[0] != be[1]:
                tempbe.append(be)
        self.edges = tempe
        self.back_edges = tempbe

    def end_if_helper(self, flag):
        if len(self.if_statement) > 0:
            t = self.if_statement[-1]
            self.hashmap_if[t] = [self.max_visited]
            if flag == 'else if' or flag == 'else':  # just ending if statement and it gets to else if
                ir = self.if_root.pop()
                self.graph[ir].append(self.max_visited + 1)
            else:  # ending else statement
                temp = []
                while len(self.if_statement) > 0:
                    popidx = self.if_statement.pop()
                    if popidx in self.hashmap_if:
                        for p in self.hashmap_if[popidx]:
                            self.graph[p] = [self.max_visited]
                    else:
                        if popidx not in temp:
                            temp.append(popidx)
                self.if_statement = temp
                self.graph[self.max_visited].append(self.max_visited + 1)
                self.graph[self.max_visited + 1] = [-1]

    def end_while_helper(self):
        if len(self.while_loop) > 0:
            t = self.while_loop.pop()
            print("END WHILE---", t)
            self.graph[self.max_visited].append(t)
            self.graph[t].append(self.max_visited + 1)
            self.graph[self.max_visited + 1] = [-1]

    def end_doloop_helper(self):
        if len(self.doloop) > 0:
            t = self.doloop.pop()
            self.graph[self.max_visited].append(t)
            self.graph[self.max_visited].append(self.max_visited + 1)
            self.graph[self.max_visited + 1] = [-1]

    def end_forloop_helper(self):
        if len(self.forloop) > 0:
            t = self.forloop.pop()
            value = self.hash_for_loop[t][0]
            self.graph[value] = [t]
            self.graph[self.max_visited - 1] = [value]
            self.graph[t].append(self.max_visited)

    def end_logical(self, i):
        self.curr_idx += 1
        self.mapping[self.curr_idx] += self.list_input[i][1]
        self.graph[self.curr_idx] = [-1]
        self.max_visited = self.curr_idx
        if i in self.idx_end_if:
            if i + 1 < len(self.list_input):
                if 'else if' in self.list_input[i + 1][1]:
                    self.end_if_helper('else if')
                elif 'else' in self.list_input[i + 1][1]:
                    self.end_if_helper('else')
                else:
                    self.end_if_helper('end')
            else:
                self.end_if_helper('end')

        elif i in self.idx_end_loop:
            self.end_while_helper()

        elif i in self.idx_end_doloop:
            self.end_doloop_helper()

        elif i in self.idx_end_forloop:
            self.end_forloop_helper()

    def build_assignment(self, i):
        self.mapping[self.curr_idx] += self.list_input[i][1]
        self.graph[self.curr_idx] = [self.curr_idx + 1]

    def build_if_else(self, i):
        print("GRAPH before IF ----", self.graph, self.list_input[i - 1])
        if i > 1 and 'for' in self.list_input[i - 1][1]:
            self.curr_idx -= 1
            if str(self.curr_idx - 1) + 'b' in self.graph:
                self.graph[str(self.curr_idx - 1) + 'b'].pop()
                self.graph[str(self.curr_idx - 1) + 'b'].append(self.curr_idx)
        self.curr_idx += 1
        self.mapping[self.curr_idx] += self.list_input[i][1]
        self.graph[self.curr_idx] = [-1]
        print("CURRENT ----", self.curr_idx)
        self.graph[self.max_visited].append(self.curr_idx)
        self.graph[self.curr_idx].append(self.curr_idx + 1)
        self.idx_end_if.append(self.find_end_index(i))
        if 'if' in self.list_input[i][1]:
            self.if_statement.append(self.curr_idx + 1)
            self.if_root.append(self.curr_idx)
        else:
            self.if_statement.append(self.curr_idx)
        self.max_visited = self.curr_idx

    def build_while(self, i, statement):
        print("GRAPH before WHILE DO ----", self.list_input[i - 1], 'for' in self.list_input[i - 1][1], i)
        self.curr_idx += 1
        if i >= 1 and 'for' in self.list_input[i - 1][1]:
            self.curr_idx -= 1
            if str(self.curr_idx - 1) + 'b' in self.graph:
                self.graph[str(self.curr_idx - 1) + 'b'].pop()
                self.graph[str(self.curr_idx - 1) + 'b'].append(self.curr_idx)
        self.mapping[self.curr_idx] += self.list_input[i][1]
        self.graph[self.curr_idx] = [self.curr_idx + 1]
        if statement == 'while':
            self.idx_end_loop.append(self.find_end_index(i))
            # input in hashmap
            self.while_loop.append(self.curr_idx)
        else:
            self.idx_end_doloop.append(self.find_end_index(i))
            # input in logical
            self.doloop.append(self.curr_idx)
        """
        self.curr_idx += 1
        self.graph[self.curr_idx] = [-1]
        """
        self.max_visited = self.curr_idx

    def build_for(self, i):
        self.curr_idx += 1
        self.mapping[self.curr_idx] += self.list_input[i][1]
        self.idx_end_forloop.append(self.find_end_index(i))
        for_semicolon = split_by_semicolon(self.list_input[i][1], self.curr_idx)
        for fs in for_semicolon:
            self.mapping[fs] = for_semicolon[fs]
        condition = str(self.curr_idx) + 'b'
        statement = str(self.curr_idx) + 'c'
        temp = self.graph[self.curr_idx - 1]
        self.graph[self.curr_idx - 1] = [t for t in temp if t != self.curr_idx]
        self.graph[self.curr_idx - 1].append(condition)
        self.graph[statement] = [-1]
        self.graph[condition] = [-1]
        self.hash_for_loop[condition] = [statement]

        self.forloop.append(condition)
        self.curr_idx += 1
        self.graph[condition] = [self.curr_idx + 1]
        self.graph[self.curr_idx] = [-1]
        self.max_visited = self.curr_idx


if __name__ == "__main__":
    test_path = "testing.docx"
    pp = ProgParser(test_path)
    l = pp.get_all_programs()['Program 14:']

    gr = Graph()
    gr.build_graph(l)
    print(gr.list_input)
    print("NODES ----", gr.nodes)
    print("EDGES ----", gr.edges)
    print("BACK_EDGES ----", gr.back_edges)
    print("MAPPING ---", gr.mapping)
    print("GRAPH ---", gr.graph)
    draw_graph(gr.nodes, gr.edges, gr.back_edges)
