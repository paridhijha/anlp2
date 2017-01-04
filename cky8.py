import sys,re
import nltk
from collections import defaultdict
import cfg_fix
from cfg_fix import parse_grammar, CFG
from pprint import pprint

# Since a lot of new comments have been added, some old comments have
# been removed to maintain the clarity and readability of the code

class CKY:
    # No change in this function as part of ans to Q8
    def __init__(self,grammar):
        self.verbose=False
        assert(isinstance(grammar,CFG))
        self.grammar=grammar
        self.buildIndices(grammar.productions())
    
    # No change in this function as part of ans to Q8
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

    # Function updated as part of ans to Q8
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
                # check if start_symbol is present in any of the labels in this cell
                if start_symbol == label.symbol:
                    is_present=True
        return is_present


    # Function updated as part of ans to Q8
    def unary_fill(self):
        for r in range(self.n-1):
            cell=self.matrix[r][r+1]
            word=self.words[r]
            # new variable label (instance of class Label) created
            # currently it doesnot have any top, nor any left or right backpointers since itself it is at
            # the bottom of the parsed tree (which will be constructed later), so last 2 parameters
            # left blank while creating this label instance.
            label=Label(word,r,r+1)
            
        # Instead of passing a word (a string) to addLabel, now a Label object is
        # passed to following 2 functions which has additional information
        # about cell row and col.
            cell.addLabel(label)
            cell.unary_update(label,self.unary,r,r+1)
            # Now the _labels is a list of instances of Label class
            # this list is a string, following operations are performed.
            if self.verbose:
                str_list=[]
                str=""
                for label in cell._labels:
                    isStr = type(label.symbol) is str
                    # Since label might contain a nltk.non terminal type, it has to
                    # be converted to string before adding to list
                    if not isStr:
                        str=label.symbol.__str__()
                    else:
                        str=label.symbol
                    str_list.append(str)
                    print "Unary branching rules at node (%s,%s): %s "%(r,r+1,' '.join(str_list))

    # No change in this function as part of ans to Q8
    def binary_scan(self):
        for span in xrange(2, self.n):
            for start in xrange(self.n-span):
                end = start + span
                for mid in xrange(start+1, end):
                    self.maybe_build(start, mid, end)
        print
    
    # Function updated as part of ans to Q8
    def maybe_build(self, start, mid, end):
        if self.verbose:
            print "Binary branching rules for %s--%s--%s:"%(start,mid,end),
        cell=self.matrix[start][end]
        # Instead of iterating over a list of strings, now the iteration is
        # over a list which stores instances of class Label as its values
        # So l1 and l2 are labels whose symbols are matched to the rhs of the binary rule
        for l1 in self.matrix[start][mid]._labels:
            for l2 in self.matrix[mid][end]._labels:
                if (l1.symbol,l2.symbol) in self.binary:
                    for l_symbol in self.binary[(l1.symbol,l2.symbol)]:
                        # new label created at start and end location with left and
                        # right backpointers as l1 and l2. This will help in backtracking
                        # to reach the symbols which were used from the binary rule list
                        # to create and add this new label
                        label = Label(l_symbol,start,end,l1,l2)
                        # is_present checks if a symbol is already present in the matrix
                        # i.e. another binary rule was previously used to reach the same
                        # non-terminal. If it is true, new label is not added to the
                        # matrix, since as part of Q8 only the one parse of the tree is
                        # required. Multiple parse tree implemented in cky9.py under Q9
                        # this check improves the running time of the parser too.
                        is_present = False
                        for l in self.matrix[start][end]._labels:
                            if l.symbol == l_symbol:
                                is_present=True
                        if not is_present:
                            cell.addLabel(label)
                            cell.unary_update(label,self.unary,start,end)
                        if self.verbose:
                            print " %s -> %s %s"%(l_symbol,l1.symbol,l2.symbol),
            if self.verbose:
                print

    # No change in this function as part of ans to Q8
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

    # Function added as part of ans to Q8
    # This is a recursive funtion which iterates the parsed tree as a PreOrder traversal
    # and returns the nodes travelled in form of a list of strings(of words and non-terminals)
    def create_tree(self,node,tree=[]):
        if node.is_parent:
                tree.append("(")
        symbol_str=""
        if type(node.symbol) is not str:
            symbol_str=node.symbol.__str__()
        else:
            symbol_str=node.symbol
        # Pre order, first visit the current node and print it (i.e. append it into tree list)
        tree.append(symbol_str)
        # Visit the left subtree by passing the left child to the same fn
        if  node.left:
            self.create_tree(node.left,tree)
        # Now visit the right subtree
        if node.right:
            self.create_tree(node.right,tree)
        if node.is_parent:
            tree.append(")")
        return tree

    # Function added as part of ans to Q8
    def first_tree(self):
        # the upper rightmost cell of matrix
        labels = self.matrix[0][self.n-1]._labels
        # The start symbol from nltk library S
        start_symbol = self.grammar.start()
        # index iterates over the labels list
        index=0
        # 2 possibilities when S is searched in labels list:
        #   1) There is no label with symbol S present - no complete parse tree found
        #   2) There is exactly one label with symbol S representating the one complete parsed tree
        # since the checks implemented in unary_update() and maybe_build ensures that only 1 non
        # terminal of same name is added to a list including top rightmost cell which can contain
        # atmost one label with symbol S
        not_found = True
        while (not_found):
            label = labels[index]
            # check to see that the type is a non terminal before comparison to S
            if type(label.symbol) is not str:
                if label.symbol == start_symbol:
                    # first S symbol found in this Cell
                    not_found = False
                    start_label = label
        # no tree found, return nltk tree with empty braces ()
        if not_found:
            return nltk.tree.Tree.fromstring("()")
        tree=[]
        if  start_label:
            # call the recursive fn create_tree which builds the tree from the matrix
            # with the root of the tree as S
            tree = self.create_tree(start_label,tree)
        # the string represenation of the tree is used to convert it into
        # nltk.tree.Tree object and this object is returned from the fn
        return nltk.tree.Tree.fromstring(' '.join(tree))



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

    # Function updated as part of ans to Q8
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
            # labels is now a list of label class. so labs[i].symbol is the string for a label instance
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

    # Function updated as part of ans to Q8
    def unary_update(self,label,unaries,row,col):
        if label.symbol in unaries:
            for symbol in unaries[label.symbol]:
                # is_present check whether the current label_symbol is already present in the
                # list of labels for this particular cell via a previous call to unary_update()
                is_present = False
                for l in self._labels:
                    if l.symbol == symbol:
                        is_present=True
                if not is_present:
                    # If a unary production is added as a new label, the old label is always added
                    # as the left backpointer of the new label
                    new_label = Label(symbol,row,col,label)
                    # This label instance called new_label has symbol as parent and has left backpointer as the
                    # previous label. Since we are later construct the tree going upwards as we find chaining
                    # unary rules like A->B B->C and so on, this information needs to be stored here so as to
                    # perform backtracking later.
                    self.addLabel(new_label)
                    #print "Unary Update- new node added at (",row,",",col,") is", new_node.symbol,"has child",node.symbol
                    self.unary_update(new_label,unaries,row,col)

# Class label updated as part of ans to Q8
class Label:
    def __init__(self,
                 # A symbol can be any of the 2 types nltk.grammar.Nonterminal or a terminal ie a string (a word or a
                 # punctuation in the given sentence)
                 symbol,
                 # Represents to which cell this label belongs to.
                 cell_row,
                 cell_col,
                 # As part of converting CKY recognizer to a parser using backtracking, we need to store additional
                 # information about the back pointers of this label as left and right which will store from which
                 # cells this current label was generated. So left and right represents 2 additional label instances.
                 left=None,
                 right=None,
                 ):
        
        self.symbol=symbol
        self.cell_row = cell_row
        self.cell_col = cell_col
        self.left = left
        self.right = right
    
        # This value is needed during tree construction to check when to begin a subtree by checking whether this
        # tree has a valid parent or not.
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


        
    
