from katharos.algebra.functor.list_functor import ListFunctor


class TestListFunctorBasics:
    def test_init_empty_list(self):
        functor = ListFunctor([])
        assert functor.xs == []

    def test_init_with_integers(self):
        functor = ListFunctor([1, 2, 3])
        assert functor.xs == [1, 2, 3]

    def test_init_with_strings(self):
        functor = ListFunctor(["a", "b", "c"])
        assert functor.xs == ["a", "b", "c"]

    def test_repr(self):
        functor = ListFunctor([1, 2, 3])
        assert repr(functor) == "ListFunctor([1, 2, 3])"

    def test_repr_empty(self):
        functor = ListFunctor([])
        assert repr(functor) == "ListFunctor([])"


class TestListFunctorFmap:
    def test_fmap_empty_list(self):
        functor = ListFunctor([])
        result = functor.fmap(lambda x: x * 2)
        assert result.xs == []
        assert isinstance(result, ListFunctor)

    def test_fmap_double_integers(self):
        functor = ListFunctor([1, 2, 3])
        result = functor.fmap(lambda x: x * 2)
        assert result.xs == [2, 4, 6]
        assert isinstance(result, ListFunctor)

    def test_fmap_increment(self):
        functor = ListFunctor([1, 2, 3])
        result = functor.fmap(lambda x: x + 1)
        assert result.xs == [2, 3, 4]

    def test_fmap_type_conversion(self):
        functor = ListFunctor([1, 2, 3])
        result = functor.fmap(str)
        assert result.xs == ["1", "2", "3"]

    def test_fmap_string_length(self):
        functor = ListFunctor(["hello", "world", "test"])
        result = functor.fmap(len)
        assert result.xs == [5, 5, 4]

    def test_fmap_string_upper(self):
        functor = ListFunctor(["hello", "world"])
        result = functor.fmap(str.upper)
        assert result.xs == ["HELLO", "WORLD"]

    def test_fmap_complex_function(self):
        functor = ListFunctor([1, 2, 3, 4, 5])

        def complex_function(x):
            return x**2 + 1

        result = functor.fmap(complex_function)
        assert result.xs == [2, 5, 10, 17, 26]

    def test_fmap_returns_new_instance(self):
        functor = ListFunctor([1, 2, 3])
        result = functor.fmap(lambda x: x * 2)
        assert functor is not result
        assert functor.xs == [1, 2, 3]
        assert result.xs == [2, 4, 6]


class TestListFunctorLaws:
    def test_identity_law_integers(self):
        functor = ListFunctor([1, 2, 3, 4, 5])

        def identity(x):
            return x

        result = functor.fmap(identity)
        assert result.xs == functor.xs

    def test_identity_law_strings(self):
        functor = ListFunctor(["a", "b", "c"])

        def identity(x):
            return x

        result = functor.fmap(identity)
        assert result.xs == functor.xs

    def test_identity_law_empty(self):
        functor = ListFunctor([])

        def identity(x):
            return x

        result = functor.fmap(identity)
        assert result.xs == functor.xs

    def test_composition_law_integers(self):
        functor = ListFunctor([1, 2, 3, 4, 5])

        def f(x):
            return x * 2

        def g(x):
            return x + 1

        left_side = functor.fmap(lambda x: g(f(x)))
        right_side = functor.fmap(f).fmap(g)

        assert left_side.xs == right_side.xs

    def test_composition_law_strings(self):
        functor = ListFunctor(["hello", "world", "test"])

        def f(s):
            return s.upper()

        def g(s):
            return s + "!"

        left_side = functor.fmap(lambda x: g(f(x)))
        right_side = functor.fmap(f).fmap(g)

        assert left_side.xs == right_side.xs

    def test_composition_law_type_changes(self):
        functor = ListFunctor([1, 2, 3])

        def f(x):
            return x * 2

        def g(x):
            return str(x)

        left_side = functor.fmap(lambda x: g(f(x)))
        right_side = functor.fmap(f).fmap(g)

        assert left_side.xs == right_side.xs

    def test_composition_law_empty(self):
        functor = ListFunctor([])

        def f(x):
            return x * 2

        def g(x):
            return x + 1

        left_side = functor.fmap(lambda x: g(f(x)))
        right_side = functor.fmap(f).fmap(g)

        assert left_side.xs == right_side.xs

    def test_composition_law_complex(self):
        functor = ListFunctor([1, 2, 3, 4, 5])

        def f(x):
            return x**2

        def g(x):
            return x - 1

        def h(x):
            return x * 3

        left_side = functor.fmap(lambda x: h(g(f(x))))
        right_side = functor.fmap(f).fmap(g).fmap(h)

        assert left_side.xs == right_side.xs


class TestListFunctorEdgeCases:
    def test_fmap_with_none_values(self):
        functor = ListFunctor([None, None, None])
        result = functor.fmap(lambda x: x)
        assert result.xs == [None, None, None]

    def test_fmap_mixed_types(self):
        functor = ListFunctor([1, "hello", 3.14])
        result = functor.fmap(str)
        assert result.xs == ["1", "hello", "3.14"]

    def test_fmap_nested_lists(self):
        functor = ListFunctor([[1, 2], [3, 4], [5, 6]])
        result = functor.fmap(lambda lst: sum(lst))
        assert result.xs == [3, 7, 11]

    def test_fmap_boolean_values(self):
        functor = ListFunctor([True, False, True])
        result = functor.fmap(lambda x: not x)
        assert result.xs == [False, True, False]

    def test_multiple_fmap_chains(self):
        functor = ListFunctor([1, 2, 3])
        result = (
            functor.fmap(lambda x: x * 2).fmap(lambda x: x + 1).fmap(lambda x: x**2)
        )
        assert result.xs == [9, 25, 49]

    def test_fmap_with_tuples(self):
        functor = ListFunctor([(1, 2), (3, 4), (5, 6)])
        result = functor.fmap(lambda t: t[0] + t[1])
        assert result.xs == [3, 7, 11]

    def test_single_element_list(self):
        functor = ListFunctor([42])
        result = functor.fmap(lambda x: x * 2)
        assert result.xs == [84]

    def test_large_list(self):
        large_list = list(range(1000))
        functor = ListFunctor(large_list)
        result = functor.fmap(lambda x: x * 2)
        assert result.xs == [x * 2 for x in large_list]
