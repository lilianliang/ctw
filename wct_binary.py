from StringIO import StringIO
import numpy as np

from kt import compute_kt_table


class WCTBinary(object):
    """
    Binary weighted context tree.
    """
    MAX_NODES = 2000000
    NO_CHILD = -1  # so we can store children indices in an int array

    def __init__(self, depth):
        self.depth = depth
        self.kt_table = compute_kt_table(depth, depth)
        self.arr_a = np.zeros(self.MAX_NODES, dtype=np.int)
        self.arr_b = np.zeros(self.MAX_NODES, dtype=np.int)
        self.arr_pe = np.zeros(self.MAX_NODES)
        self.arr_pw = np.zeros(self.MAX_NODES)
        self.arr_0c = np.zeros(self.MAX_NODES, dtype=np.int)
        self.arr_1c = np.zeros(self.MAX_NODES, dtype=np.int)
        self.next_id = 0
        self.root_id = self._create_leaf()

    def get_a(self, node_id, default):
        if node_id == self.NO_CHILD:
            return default
        else:
            return self.arr_a[node_id]

    def get_b(self, node_id, default):
        if node_id == self.NO_CHILD:
            return default
        else:
            return self.arr_b[node_id]

    def get_pw(self, node_id, default):
        if node_id == self.NO_CHILD:
            return default
        else:
            return self.arr_pw[node_id]

    def __str__(self):
        stream = StringIO()
        self._print_rec(self.root_id, "", stream)
        return stream.getvalue()

    def _print_rec(self, node_id, path, stream):
        """
        Recursively print tree.
        """
        if self.arr_1c[node_id] != self.NO_CHILD:
            self._print_rec(self.arr_1c[node_id], "1" + path, stream)
        if self.arr_0c[node_id] != self.NO_CHILD:
            self._print_rec(self.arr_0c[node_id], "0" + path, stream)
        print >>stream, "{}{}: a={} b={} pe={} pw={}".format(
            " " * (self.depth - len(path)), path,
            self.arr_a[node_id], self.arr_b[node_id],
            self.arr_pe[node_id], self.arr_pw[node_id])

    def update(self, context, next_bit):
        assert len(context) == self.depth
        self._update_rec(self.root_id, context, next_bit)

    def _update_rec(self, node_id, context, next_bit):
        """
        Update tree upon seeing next_bit after the given context.
        """
        # Recursively update the appropriate child.
        if not context:
            # Leaf.
            assert self.arr_0c[node_id] == self.NO_CHILD
            assert self.arr_1c[node_id] == self.NO_CHILD
        else:
            # Non-leaf.
            bit = context.pop()
            child_id = self._get_or_create_child(node_id, bit)
            self._update_rec(child_id, context, next_bit)

        # Now update this node.
        assert next_bit in (0, 1)
        count_arr = (self.arr_a, self.arr_b)[next_bit]
        count_arr[node_id] += 1
        self._sanity_check(node_id)
        self._update_pe_pw(node_id)

    def _create_leaf(self):
        assert self.next_id < self.MAX_NODES
        self.arr_a[self.next_id] = 0
        self.arr_b[self.next_id] = 0
        self.arr_pe[self.next_id] = 1
        self.arr_pw[self.next_id] = 1
        self.arr_0c[self.next_id] = self.NO_CHILD
        self.arr_1c[self.next_id] = self.NO_CHILD
        node_id = self.next_id
        self.next_id += 1
        return node_id

    def _get_or_create_child(self, node_id, bit):
        """
        Return child_id for given node_id and bit.
        """
        assert bit in (0, 1)
        child_arr = (self.arr_0c, self.arr_1c)[bit]
        if child_arr[node_id] == self.NO_CHILD:
            child_id = self._create_leaf()
            child_arr[node_id] = child_id
        return child_arr[node_id]

    def _sanity_check(self, node_id):
        """
        Assert invariants on the given node.
        """
        a, b = self.arr_a[node_id], self.arr_b[node_id]
        i0c, i1c = self.arr_0c[node_id], self.arr_1c[node_id]
        if i0c == self.NO_CHILD and i1c == self.NO_CHILD:
            # Leaf.
            assert a + b > 0
        else:
            # Non-leaf.
            assert a == self.get_a(i0c, 0) + self.get_a(i1c, 0)
            assert b == self.get_b(i0c, 0) + self.get_b(i1c, 0)

    def _update_pe_pw(self, node_id):
        """
        Update pe, pw for the given node.
        """
        a, b = self.arr_a[node_id], self.arr_b[node_id]
        i0c, i1c = self.arr_0c[node_id], self.arr_1c[node_id]
        self.arr_pe[node_id] = self.kt_table[a, b]
        if i0c == self.NO_CHILD and i1c == self.NO_CHILD:
            # Leaf.
            self.arr_pw[node_id] = self.arr_pe[node_id]
        else:
            # Non-leaf.
            self.arr_pw[node_id] = (
                0.5 * self.arr_pe[node_id] +
                0.5 * self.get_pw(i0c, 1) * self.get_pw(i1c, 1))

        # FIXME: need log probs
