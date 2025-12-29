# Katharos

Katharos that provides a set of functions and types for functional programming in `Python`.


## Modules

- `algebra`: Provides a set of algebraic structures for functional programming.
- `ds`: Provides a set of data structures for functional programming.
- `functools`: Provides a set of functional programming tools.

## Algebra
The `algebra` module provides fundamental algebraic structures commonly used in functional programming:

- **Semigroup**: A type with an associative binary operation
- **Monoid**: A type with an associative binary operation and an identity element
- **Functor**: A type that can be mapped over
- **Applicative**: A functor with application, allowing functions within a context to be applied to values within a context
- **Monad**: A structure that represents computations as a series of steps

These abstractions enable composable, reusable code patterns and help manage side effects in a pure functional style.


### Semigroup

A **Semigroup** is a fundamental algebraic structure that consists of:

1. A set of values of type `S`
2. An associative binary operation `op` (represented by the `@` operator)

Unlike a Monoid, a Semigroup does **not** require an identity element. This makes it more general but less powerful for certain operations like folding empty collections.

**Mathematical Properties:**
- **Associativity**: `(a @ b) @ c = a @ (b @ c)` for all `a`, `b`, `c`

**Implementation:**

To create a Semigroup, inherit from the `Semigroup` class and implement:
- `op(self, other)`: The associative binary operation

**Example 1: Creating a Custom Semigroup (Max)**

```python
from katharos.algebra import Semigroup

class Max(Semigroup):
    """A Semigroup that keeps the maximum value."""
    
    def __init__(self, value: int) -> None:
        self.value = value
    
    def op(self, other: 'Max') -> 'Max':
        """Combine two Max values by taking the maximum."""
        return Max(max(self.value, other.value))
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Max) and self.value == other.value
    
    def __repr__(self) -> str:
        return f"Max({self.value})"

# Using the custom Semigroup
a = Max(5)
b = Max(10)
c = Max(3)

# Semigroup operation using @ operator
result = a @ b  # Max(10)

# Associativity property holds
assert (a @ b) @ c == a @ (b @ c)  # max(max(5,10),3) = max(5,max(10,3)) = 10

# Note: No identity element exists for Max over all integers
# (there's no single value i such that max(x, i) = x for all x)
```

**Example 2: NonEmptyList as a Semigroup**

```python
from katharos.ds.list import NonEmptyList

# NonEmptyList is a Semigroup (but not a Monoid, since it can't be empty)
list1 = NonEmptyList(head=1, tail=[2, 3])
list2 = NonEmptyList(head=4, tail=[5])

# Concatenation using @ operator
result = list1 @ list2  # NonEmptyList([1, 2, 3, 4, 5])

# Associativity holds
list3 = NonEmptyList(head=6, tail=[7])
assert (list1 @ list2) @ list3 == list1 @ (list2 @ list3)

# NonEmptyList guarantees at least one element
# This is useful when you need to ensure non-emptiness at the type level
```

**Key Differences from Monoid:**
- **No identity element**: Semigroups don't have a neutral element
- **Cannot fold empty collections**: Without an identity, you need at least one element to start
- **More general**: Every Monoid is a Semigroup, but not every Semigroup is a Monoid
- **Use cases**: Useful when an identity element doesn't make sense (e.g., Max, Min, NonEmptyList)

### Monoid

A **Monoid** is an algebraic structure that extends **Semigroup** by adding an identity element. It consists of:

1. A set of values of type `M`
2. An associative binary operation `op` (represented by the `@` operator)
3. An identity element that acts as a neutral element for the operation

**Mathematical Properties:**
- **Associativity**: `(a @ b) @ c = a @ (b @ c)` for all `a`, `b`, `c`
- **Identity**: `a @ identity() = a` and `identity() @ a = a` for all `a`

**Implementation:**

To create a Monoid, inherit from the `Monoid` class and implement:
- `op(self, other)`: The associative binary operation
- `identity()`: A static method returning the identity element

**Example 1: Creating a Custom Monoid (Sum)**

```python
from katharos.algebra import Monoid

class Sum(Monoid):
    """A Monoid for integer addition with 0 as identity."""
    
    def __init__(self, value: int) -> None:
        self.value = value
    
    def op(self, other: 'Sum') -> 'Sum':
        """Combine two Sum values by adding their integers."""
        return Sum(self.value + other.value)
    
    @staticmethod
    def identity() -> 'Sum':
        """Return the identity element (0 for addition)."""
        return Sum(0)
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sum) and self.value == other.value
    
    def __repr__(self) -> str:
        return f"Sum({self.value})"

# Using the custom Monoid
a = Sum(5)
b = Sum(10)
c = Sum(3)

# Monoid operation using @ operator
result = a @ b  # Sum(15)

# Identity property
identity = Sum.identity()  # Sum(0)
assert a @ identity == a  # 5 + 0 = 5
assert identity @ a == a  # 0 + 5 = 5

# Associativity property
assert (a @ b) @ c == a @ (b @ c)  # (5+10)+3 = 5+(10+3) = 18
```

**Example 2: ImmutableList as a Monoid**

```python
from katharos.ds import ImmutableList

# The identity element is an empty list
empty = ImmutableList.identity()  # ImmutableList([])

# Concatenation is the monoid operation
list1 = ImmutableList([1, 2, 3])
list2 = ImmutableList([4, 5])

# Using the @ operator (monoid operation)
result = list1 @ list2  # ImmutableList([1, 2, 3, 4, 5])

# Identity property holds
assert list1 @ empty == list1  # Left identity
assert empty @ list1 == list1  # Right identity

# Associativity holds
list3 = ImmutableList([6, 7])
assert (list1 @ list2) @ list3 == list1 @ (list2 @ list3)
```

**Example 2: MonoidMaybe for Optional Values**

```python
from katharos.ds.maybe import Maybe, Just, Nothing, MonoidMaybe

# MonoidMaybe combines Maybe values containing Semigroup elements
# Identity is Nothing
identity = MonoidMaybe.identity()  # MonoidMaybe(Nothing())

# Combining with Nothing returns the other value
m1 = MonoidMaybe(Just(ImmutableList([1, 2])))
m2 = MonoidMaybe(Nothing())
result = m1 @ m2  # MonoidMaybe(Just(ImmutableList([1, 2])))

# Combining two Just values combines their contents
m3 = MonoidMaybe(Just(ImmutableList([3, 4])))
m4 = MonoidMaybe(Just(ImmutableList([5, 6])))
result = m3 @ m4  # MonoidMaybe(Just(ImmutableList([3, 4, 5, 6])))
```
