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
        # split and index the grammar
        print "inside init"
        self.buildIndices(grammar.productions())
    
    def buildIndices(self,productions):
        # Q3 Add comments throughout
        # Before the parsing begins, this fn is called to create and populate 2 lists each for binary and unary rules of grammar and to
        # check whether the grammar is in Chomsky Normal form or not.
        # Self variable here is an instance of class CKY and productions is a list of <> in the variable grammar for this self instance
        # Initialize a default dictionary where each value is a list. Assign it to the unary variable. This stores all unary rules of grammar.
        self.unary=defaultdict(list)
        # Another similar dictionary to store all binary rules.
        self.binary=defaultdict(list)
        # Iterate over all values stored in productions list. For each production value, do the following
        for production in productions:
            # Assign the rhs value of current production ( of form lhs->rhs) to a variable rhs
            rhs=production.rhs()
            # Do the same for lhs
            lhs=production.lhs()
            # Check whether this rule has alteast one constituent on rhs and not more than 2 on rhs (to conform to Chomsky Normal Form)
            # If this check fails, abort with an assertion error, else continue
            assert(len(rhs)>0 and len(rhs)<=2)
            # Check if rhs has only 1 constituent, that means this is a unary rule
            if len(rhs)==1:
                # Add this rule in the unary list with key = rhs and its value = lhs
                self.unary[rhs[0]].append(lhs)
            else:
                # If its not a unary, that means it can only be binary, so add to binary list.
                self.binary[rhs].append(lhs)

    def parse(self,tokens,verbose=False):
        # Q6 expand the comments here
        # This function takes a CKY instance self and list of tokens and creates a matrix
        # to store all the non terminals and terminals the parse will generate
        self.verbose=verbose
        self.words = tokens
        # n is the size of the matrix which is one greater than number of words
        self.n = len(self.words)+1
        self.matrix = []
        # We index by row, then column
        #  So Y below is 1,2 and Z is 0,3
        #    1   2   3  ...
        # 0  X   X   Z
        # 1      Y   X
        # 2          X
        # ...
        # the first scan is vertical, picking one row at a time so r ranges from 0 to n-1
        for r in range(self.n-1):
            # rows
            # for each row a list called row is created which will store all cells belonging
            # to this row and each such row will be attached to the parse matrix
            row=[]
            # for each row, a column is picked from 0 to n
            for c in range(self.n):
                # columns
                # this check is done for cells belonging to upper right part of matrix
                # when the matrix is divided by a diagonal starting from top left and ending at bottm right
                if c>r:
                    # This is one we care about, add a cell
                    # a new instance of Cell class is created and stored in the current list called row. This
                    # cell will represent the matrix[r][c] location
                    row.append(Cell())
                else:
                    # just a filler
                    # the cky parser ignores this part of the matrix, so no Cell classes need to be created.
                    row.append(None)
                # once a row has all the Cell objects created and attached with it for all the columns,this
                # row is attached to the matrix.
                self.matrix.append(row)
        # this unary_fill fn is called right after creating the matrix. it only goes over the cells which are
        # located along the diagonal (top left to bottom right). All these cells are starting points and will
        # only store the terminal ie the words of the sentence, with the first word at the top leftmost corner
        # of matrix and the last word at the bottom right. along with the terminals, this function will also
        # put the non-terminals which can be directly attached to terminals using the unary rules for this
        # grammar. this is done using an internal fn call to unary_update in a recursive manner.
        self.unary_fill()
        # once the digonal cells are populated, then binary_scan is called to go over the cells from bottom
        # left in upward and rightward manner one by one so as to find the non terminals corresponding to the
        # grammar to fill the current cell. Eventually all the cells will be visited during this scan and
        # some populated with the non terminals. this fn ends when it scans the top rightmost cell of matrix
        self.binary_scan()
        # returns true or false depending upon whether 'S' was found in the top rightmost corner of the
        # matrix or not which means whether a complete parse tree was created for this sentence or not.
        return self.grammar.start() in self.matrix[0][self.n-1].labels()


    def unary_fill(self):
        # Comments for Q4
        # Variable self passed to this fn is an instance of class CKY, has following variables for each instance
        # 1.matrix (for CKY chart parsing )
        # 2.words (a list of strings representing the sentence)
        # 3.unary ( a default dictionary of lists  to store all unary rules, indexed by rhs(key) and lhs(value)
        # 4.binary ( a default dictionary of lists to store all binary rules, indexed by rhs(key) and lhs(value)
        # This function is called from parse fn once the matrix is initialized and cells are created, appened to
        # corresponding rows and rows appended to the matrix.
        # The value of r ranges from 0 to n-1, going over all words of the sentence, one at a time and adding the word
        # in the 'label' of the corresponding cell
        for r in range(self.n-1):
            # get the cell from the diagonal of matrix for all values like (0,1),(1,2),(3,4)...till (n-1,n)
            cell=self.matrix[r][r+1]
            # get the word at location r i.e. the word in sentence one by one for r from 0 to n-1
            word=self.words[r]
            # add this word to the cell as a label value ( class cell has variable label)
            cell.addLabel(word)
            cell.unary_update(word,self.unary)
            # if verbose value is set to True, enables the tracing, by default this value is set to False
            if self.verbose:
                print "Unary branching rules at node (%s,%s):%s"%(r,r+1,cell.labels())

    def binary_scan(self):
        for span in xrange(2, self.n):
            for start in xrange(self.n-span):
                end = start + span
                for mid in xrange(start+1, end):
                    self.maybe_build(start, mid, end)

    def maybe_build(self, start, mid, end):
        # Q5 -- add comments
        # This fn is called multiple times from binary_scan fn for each value of index=mid from index=start till index=end of
        # each value of span (which ranges from 2 to n)
        # It does so to find all possible combinations from left row of the cell and bottom column of the same cell, such that
        # there is a combination of labels (s1 and s2) and there is a binary rule whose rhs = s1,s2.
        if self.verbose:
            print "Binary branching rules for %s--%s--%s:"%(start,mid,end),
            # Pick the cell from matrix, for which the labels will be updated by iterating on the left and bottom area of this cell in the matrix
            cell=self.matrix[start][end]
            # Now iterate over another cell to the left of original cell and assign all the symbols present in its labels list to s1,one at a time
            for s1 in self.matrix[start][mid].labels():
                # For each value of s1 symbol, iterate over another cell directly below the original cell and iterate over all the symbols
                # stored in this cell's labels list as s2, one at a time.
                for s2 in self.matrix[mid][end].labels():
                    # Now for each value of s1 and s2, check if there is a binary rule of format (X->s1,s2), if not do nothing and return
                    if (s1,s2) in self.binary:
                        # If such a binary rule is present (there can be more than one such rule), iterate over all such rules present in
                        # the binary list
                        for s in self.binary[(s1,s2)]:
                            # For each lhs corresponding to the matching value of s1,s2 (binary rule of form s->s1,s2), add this symbol s
                            # to the original cell in the matrix (ie index=start,end)
                            cell.addLabel(s)
                            # After adding this new label(s) to the labels list of the cell in the matrix, call the unary_update fn
                            # recursively with this value of s such that all the unaries get updated.
                            cell.unary_update(s,self.unary)
                            if self.verbose:
                                print " inside the loop %s -> %s %s"%(s, s1,s2),
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
        # Q4 Add comments throughout
        # Self variable is an instance of class Cell
        # Symbol here corresponds to the particular lhs(non terminal) of a rule or word of the sentence for which this operation is performed
        # unaries is the default dictionary (of class CKY), which has already been populated with all the unary rules
        # of the given grammar, indexed by rhs (as key) and having lhs as value
        # Check for the condition if the symbol(word) is present in one of the unary rules of the grammar.
        #If yes, proceed otherwise do nothing and return from this fn
        if symbol in unaries:
            # Now the symbol is present in the lhs of one of the unary rules, loop over all such unary rules
            # for each such rule which has lhs=symbol, parent(a string value) = the rhs of that rule
            for parent in unaries[symbol]:
                # Check if parent is already present in the list labels (labels is a list of 'label' class in the Cell instance self)
                # if already present, do nothing.
                if parent not in self._labels:
                    # If not present, add the parent (rhs of the rule) to the list of labels in this particular Cell
                    self.addLabel(parent)
                    # Call this same function recursively, with the rhs now passed as lhs, such that the chain of all rules
                    # of the form A->B , B->C , C->D (A being the terminal word, rest all non-terminals) gets stored in the
                    # _labels list of this cell.
                    self.unary_update(parent,unaries)

class Label:
    def __init__(self,
                 # Fill in here
                 ):
        pass # Replace as appropriate

# Add more methods as required
