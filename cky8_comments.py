import sys,re
import nltk
from collections import defaultdict
import cfg_fix
from cfg_fix import parse_grammar, CFG
from pprint import pprint

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
        return self.grammar.start() in self.matrix[0][self.n-1].labels()

    def unary_fill(self):
        for r in range(self.n-1):
            cell=self.matrix[r][r+1]
            word=self.words[r]
            cell.addLabel(word)
            cell.unary_update(word,self.unary)
            if self.verbose:
                print "Unary branching rules at node (%s,%s):%s"%(r,r+1,cell.labels())

    def binary_scan(self):
        for span in xrange(2, self.n):
            for start in xrange(self.n-span):
                end = start + span
                for mid in xrange(start+1, end):
                    self.maybe_build(start, mid, end)

    def maybe_build(self, start, mid, end):
        if self.verbose:
            print "Binary branching rules for %s--%s--%s:"%(start,mid,end),
        cell=self.matrix[start][end]
        for s1 in self.matrix[start][mid].labels():
            for s2 in self.matrix[mid][end].labels():
                if (s1,s2) in self.binary:
                    for s in self.binary[(s1,s2)]:
                        cell.addLabel(s)
                        cell.unary_update(s,self.unary)
                        if self.verbose:
                            print " %s -> %s %s"%(s, s1,s2),
        if self.verbose:
            print 

    def pprint(self,cell_width=8):
        '''Try to print matrix in a nicely lined-up way'''
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
                 
def wtp(l,subrows,maxrows):
    '''figure out what row or filler from within a cell
    to print so that the printed cell fills from
    the bottom.  l will be in range(mrh)'''
    offset=maxrows-len(subrows)
    if l>=offset:
        return subrows[l-offset]
    else:
        return ''

class Cell:
    '''A cell in a CKY matrix'''
    def __init__(self):
        self._labels=[]

    def __str__(self):
        return self.str()

    def str(self,width=8):
        '''Try to format labels in a rectangule,
        aiming for max-width as given, but only
        breaking between labels'''
        labs=self.labels()
        n=len(labs)
        res=[]
        if n==0:
            return res
        i=0
        line=[]
        ll=-1
        while i<n:
            s=str(labs[i])
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

    def unary_update(self,symbol,unaries):
        if symbol in unaries:
            for parent in unaries[symbol]:
                if parent not in self._labels:
                    self.addLabel(parent)
                    self.unary_update(parent,unaries)

class Label:
    # Q8 Modify label class
    # To store how this label was added, so that it can be later backtracked
    # when tree is being built, we need to store the following information
    # 1. Was this label added by a unary rule in the same cell?
    # 2. Was this label added by a unary rule from 2 different cells, once cell being empty
    # 3. Was this label added by a binary rule from 2 different cell,
    # one to the left and 1 from the bottom of original cell
    # To store the information such that all 3 cases above are taken into account
    # We need a flag to know whether its 1 cell or 2 cells which will be accessing i.e.
    #  when tree is constructed whether this node has 1 or 2 child
    # We also need to know the location of these 1 or 2 cells
    # Once the cell (ie the child node) is known, we need to know which label inside
    # that cell this label came from (since the label is a list)
    # Once the cell and its label location is known, it becomes the new node and
    # this new node can be recursively backtracked until all leaves of the
    # tree are found.
    def __init__(self,
                 nodeStr,
                 row,
                 col,
                 leftChild=None,
                 rightChild=None
                 ):
        self.nodeStr=nodeStr
        self.rowPosition = row
        self.colPosition = col
        self.leftChild = leftChild
        self.rightChild = rightChild

    def 

    
        
    
