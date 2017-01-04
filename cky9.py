import sys,re
import nltk
from collections import defaultdict
import cfg_fix
from cfg_fix import parse_grammar, CFG
from pprint import pprint

# Since a lot of new comments have been added, comments mentioned in cky8.py
# have been removed from this file and only the changes from cky8.py to cky9.py
# has been commented here to maintain the clarity and readability of the code

class CKY:
    def __init__(self,grammar):
        self.verbose=False
        assert(isinstance(grammar,CFG))
        self.grammar=grammar
        self.buildIndices(grammar.productions())
    
    def buildIndices(self,productions):
        self.unary=defaultdict(list)
        self.binary=defaultdict(list)
        for production in productions:
            rhs=production.rhs()
            lhs=production.lhs()
            assert(len(rhs)>0 and len(rhs)<=2)
            if len(rhs)==1:
                self.unary[rhs[0]].append(lhs)
            else:
                self.binary[rhs].append(lhs)

    def parse(self,tokens,verbose=False):
        self.verbose=verbose
        self.words = tokens
        self.n = len(self.words)+1
        self.matrix = []
        for r in range(self.n-1):
             row=[]
             for c in range(self.n):
                 if c>r:
                     row.append(Cell())
                 else:
                     row.append(None)
             self.matrix.append(row)
        self.unary_fill()
        self.binary_scan()
        start_symbol = self.grammar.start()
        is_present=False
        for label in self.matrix[0][self.n-1]._labels:
                if start_symbol == label.symbol:
                    is_present=True
        return is_present

    def unary_fill(self):
        for r in range(self.n-1):
            cell=self.matrix[r][r+1]
            word=self.words[r]
            label=Label(word,r,r+1)
            cell.addLabel(label)
            cell.unary_update(label,self.unary,r,r+1).
            if self.verbose:
                str_list=[]
                str=""
                for label in cell._labels:
                    isStr = type(label.symbol) is str
                    if not isStr:
                        str=label.symbol.__str__()
                    else:
                        str=label.symbol
                    str_list.append(str)
                    print "Unary branching rules at node (%s,%s): %s "%(r,r+1,' '.join(str_list))

    def binary_scan(self):
        for span in xrange(2, self.n):
            for start in xrange(self.n-span):
                end = start + span
                for mid in xrange(start+1, end):
                    self.maybe_build(start, mid, end)
        print

    # fn updated as part of Q9 by removing the check for binary rules
    def maybe_build(self, start, mid, end):
        if self.verbose:
            print "Binary branching rules for %s--%s--%s:"%(start,mid,end),
        cell=self.matrix[start][end]
        for l1 in self.matrix[start][mid]._labels:
            for l2 in self.matrix[mid][end]._labels:
                if (l1.symbol,l2.symbol) in self.binary:
                    for l_symbol in self.binary[(l1.symbol,l2.symbol)]:
                        label = Label(l_symbol,start,end,l1,l2)
                        # all the labels are added and no check is performed to see
                        # whether there is an already existing label in this cell
                        # this allows for multiple parses to be stores for each cell
                        # and finally allows multiple complete parse trees to be stored
                        # in top rightmost cell of the matrix with symbol S
                        cell.addLabel(label)
                        cell.unary_update(label,self.unary,start,end)
                        if self.verbose:
                            print " %s -> %s %s"%(l_symbol,l1.symbol,l2.symbol),
            if self.verbose:
                print

    def pprint(self,cell_width=8):
        row_max_height=[0]*(self.n)
        col_max_width=[0]*(self.n)
        print_matrix=[]
        for r in range(self.n-1):
             row=[]
             for c in range(r+1,self.n):
                 if c>r:
                     cf=self.matrix[r][c].str(cell_width)
                     nlines=len(cf)
                     if nlines>row_max_height[r]:
                         row_max_height[r]=nlines
                     if cf!=[]:
                         nchars=max(len(l) for l in cf)
                         if nchars>col_max_width[c]:
                             col_max_width[c]=nchars
                     row.append(cf)
             print_matrix.append(row)
        row_fmt='|'.join("%%%ss"%col_max_width[c] for c in range(1,self.n))
        row_index_len=len(str(self.n-2))
        row_index_fmt="%%%ss"%row_index_len
        row_div=(' '*(row_index_len+1))+(
            '+'.join(('-'*col_max_width[c]) for c in range(1,self.n)))
        print (' '*(row_index_len+1))+(' '.join(str(c).center(col_max_width[c])
                       for c in range(1,self.n)))
        for r in range(self.n-1):
            if r!=0:
                print row_div
            mrh=row_max_height[r]
            for l in range(mrh):
                print row_index_fmt%(str(r) if l==mrh/2 else ''),
                row_strs=['' for c in range(r)]
                row_strs+=[wtp(l,print_matrix[r][c],mrh) for c in range(self.n-(r+1))]
                print row_fmt%tuple(row_strs)

    def create_tree(self,node,tree=[]):
        if node.is_parent:
                tree.append("(")
        symbol_str=""
        if type(node.symbol) is not str:
            symbol_str=node.symbol.__str__()
        else:
            symbol_str=node.symbol
        tree.append(symbol_str)
        if  node.left:
            self.create_tree(node.left,tree)
        if node.right:
            self.create_tree(node.right,tree)
        if node.is_parent:
            tree.append(")")
        return tree

    # New fn added as part of ans to Q9
    def all_trees(self):
        # the upper rightmost cell of matrix
        labels = self.matrix[0][self.n-1]._labels
        # The start symbol from nltk library S
        start_symbol = self.grammar.start()
        # index iterates over the labels list
        index=0
        tree = nltk.tree.Tree.fromstring("()")
        tree_list=[]
        # 3 possibilities when S is searched in labels list:
        #   1) There is no label with symbol S present - no complete parse tree found
        #   2) There is exactly one label with symbol S representating the one complete parsed tree
        #   3) There is more that one labels with symbol S, which represents structural ambiguity
        #       (either attachment or co-ordination ambiguity) in the grammar.
        #   Code picks up all labels with symbol S and converts each into nltk.tree and
        #   adds to a list of trees which is returned by this function.
        not_found=True
        for label in labels:
            # check to see that the type is a non terminal before comparison to S
            if type(label.symbol) is not str:
                if label.symbol == start_symbol:
                    # S symbol found in this Cell and this label
                    not_found=False
                    start_label = label
                    tree = self.create_tree(start_label,[])
                    # the string represenation of the tree is used to convert it into
                    # nltk.tree.Tree object and this object is returned from the fn
                    tree_list.append(nltk.tree.Tree.fromstring(' '.join(tree)))
        # no tree found, return nltk tree with empty braces ()
        if not_found:
            return nltk.tree.Tree.fromstring("()")
        # tree_list is populated with a lsit of nltk.tree.Tree objects each of them containing
        # a completed parse tree for this sentence.
        return tree_list



def wtp(l,subrows,maxrows):
    offset=maxrows-len(subrows)
    if l>=offset:
        return subrows[l-offset]
    else:
        return ''

class Cell:
    def __init__(self):
        self._labels=[]

    def __str__(self):
        return self.str()

    def str(self,width=8):
        labs=self._labels
        n=len(labs)
        res=[]
        if n==0:
            return res
        i=0
        line=[]
        ll=-1
        while i<n:
            s=str(labs[i].symbol)
            m=len(s)
            if ll+m>width and ll!=-1:
                res.append(' '.join(line))
                line=[]
                ll=-1
            line.append(s)
            ll+=m+1
            i=i+1
        res.insert(0,' '.join(line))
        return res
    
    def addLabel(self,label):
        self._labels.append(label)

    def labels(self):
        return self._labels

    def unary_update(self,label,unaries,row,col):
        if label.symbol in unaries:
            for symbol in unaries[label.symbol]:
                is_present = False
                for l in self._labels:
                    if l.symbol == symbol:
                        is_present=True
                if not is_present:
                    new_label = Label(symbol,row,col,label)
                    self.addLabel(new_label)
                    self.unary_update(new_label,unaries,row,col)

class Label:
    def __init__(self,
                 symbol,
                 cell_row,
                 cell_col,
                 left=None,
                 right=None,
                 ):
        
        self.symbol=symbol
        self.cell_row = cell_row
        self.cell_col = cell_col
        self.left = left
        self.right = right

        if(left or right):
            self.is_parent = True
        else:
            self.is_parent = False

    def add_left(self,left):
        self.istop = True
        self.left = left

    def add_right(self,right):
        self.istop = True
        self.right = right


        
    
