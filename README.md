# Katharos

Katharos is a functional programming library for Python that provides algebraic abstractions like Semigroups, Monoids, Functors, Applicatives, and Monads, along with immutable data structures to enable composable, type-safe, and side-effect-free code.

<img src="./logo.png" alt="logo" width="300" height="300">

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

**Example 3: MonoidMaybe for Optional Values**

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

### Functor

A **Functor** is a type that can be mapped over, allowing you to apply a function to values inside a computational context without changing the structure itself. It's one of the most fundamental abstractions in functional programming.

**Core Concept:**
- A Functor wraps values in a context (e.g., `Maybe[A]`, `List[A]`, `Result[A]`)
- It provides `fmap` to apply a function to the wrapped value(s) while preserving the context
- The structure remains unchanged; only the values are transformed

**Mathematical Laws:**

Functors must satisfy two laws:

1. **Identity Law**: `fmap(id) = id`
   - Mapping the identity function should return the same functor
   
2. **Composition Law**: `fmap(g ∘ f) = fmap(g) ∘ fmap(f)`
   - Mapping a composition of functions should be the same as composing the mapped functions

**Implementation:**

To create a Functor, inherit from the `Functor[A]` class and implement:
- `fmap[B](self, f: Callable[[A], B]) -> Functor[B]`: Map a function over the functor's contents

**Example 1: Creating a Custom Functor (Box)**

```python
from katharos.algebra import Functor
from collections.abc import Callable

class Box[A](Functor[A]):
    """A simple container that wraps a single value."""
    
    def __init__(self, value: A) -> None:
        self.value = value
    
    def fmap[B](self, f: Callable[[A], B]) -> 'Box[B]':
        """Apply a function to the wrapped value."""
        return Box(f(self.value))
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Box) and self.value == other.value
    
    def __repr__(self) -> str:
        return f"Box({self.value!r})"

# Using the custom Functor
box = Box(5)

# Map a function over the value
result = box.fmap(lambda x: x * 2)  # Box(10)

# Functor laws verification
# Identity law: fmap(id) = id
identity = lambda x: x
assert box.fmap(identity) == box

# Composition law: fmap(g . f) = fmap(g) . fmap(f)
f = lambda x: x + 3
g = lambda x: x * 2
assert box.fmap(lambda x: g(f(x))) == box.fmap(f).fmap(g)
```

**Example 2: Maybe as a Functor**

```python
from katharos.ds.maybe import Maybe, Just, Nothing

# Maybe handles optional values
just_value = Just(10)
nothing_value = Nothing()

# fmap applies the function only if a value exists
result1 = just_value.fmap(lambda x: x * 2)  # Just(20)
result2 = nothing_value.fmap(lambda x: x * 2)  # Nothing()

# Chain multiple transformations
result = Just(5).fmap(lambda x: x + 3).fmap(lambda x: x * 2)  # Just(16)

# Safe computation without null checks
def safe_divide(x: int) -> Maybe[float]:
    return Just(10.0 / x) if x != 0 else Nothing()

# Using fmap to transform the result
result = safe_divide(2).fmap(lambda x: x + 1)  # Just(6.0)
result = safe_divide(0).fmap(lambda x: x + 1)  # Nothing()
```

**Example 3: Result as a Functor for Error Handling**

```python
from katharos.ds import Result, Success, Failure

# Result handles computations that can fail
success = Success(42)
failure = Failure(ValueError("Something went wrong"))

# fmap applies the function only to successful values
result1 = success.fmap(lambda x: x * 2)  # Success(84)
result2 = failure.fmap(lambda x: x * 2)  # Failure(ValueError(...))

# Chain operations - errors propagate automatically
def parse_int(s: str) -> Result[int]:
    try:
        return Success(int(s))
    except ValueError as e:
        return Failure(e)

# Transform successful results
result = parse_int("42").fmap(lambda x: x * 2).fmap(lambda x: x + 10)  # Success(94)
result = parse_int("invalid").fmap(lambda x: x * 2)  # Failure(ValueError(...))
```

**Example 4: ImmutableList as a Functor**

```python
from katharos.ds import ImmutableList

# Lists are functors that map over each element
numbers = ImmutableList([1, 2, 3, 4, 5])

# fmap applies the function to each element
doubled = numbers.fmap(lambda x: x * 2)  # ImmutableList([2, 4, 6, 8, 10])
squared = numbers.fmap(lambda x: x ** 2)  # ImmutableList([1, 4, 9, 16, 25])

# Chain transformations
result = numbers.fmap(lambda x: x + 1).fmap(lambda x: x * 2)
# ImmutableList([4, 6, 8, 10, 12])

# Empty list preserves structure
empty = ImmutableList([])
result = empty.fmap(lambda x: x * 2)  # ImmutableList([])
```

**Common Use Cases:**
- **Optional values**: Transform values that may or may not exist (`Maybe`)
- **Error handling**: Transform successful results while propagating errors (`Result`)
- **Collections**: Transform each element in a collection (`List`)
- **Async operations**: Transform values that will be available in the future
- **Parsing**: Transform parsed values without unwrapping the parser context
- **Dependency injection**: Transform values in a context with dependencies

### Applicative

An **Applicative** functor is a functor with additional structure that allows you to apply functions wrapped in a context to values wrapped in a context. It sits between Functors and Monads in the hierarchy of functional abstractions.

**Core Concept:**
- An Applicative extends Functor with two key operations:
  - `pure`: Lift a plain value into the applicative context
  - `ap`: Apply a wrapped function to a wrapped value
- It enables combining multiple independent computations in a context
- Unlike Monads, Applicatives don't allow the result of one computation to determine the structure of the next

**Mathematical Laws:**

Applicatives must satisfy four laws:

1. **Identity Law**: `v ** pure(id) = v`
   - Applying the wrapped identity function returns the same value
   
2. **Composition Law**: `w ** (v ** (u ** pure(compose))) = (w ** v) ** u`
   - Function composition works as expected in the applicative context
   
3. **Homomorphism Law**: `pure(x) ** pure(f) = pure(f(x))`
   - Applying a wrapped function to a wrapped value is the same as wrapping the result
   
4. **Interchange Law**: `pure(y) ** u = u ** pure(lambda f: f(y))`
   - The order of evaluation doesn't matter for pure values

**Implementation:**

To create an Applicative, inherit from the `Applicative[A]` class and implement:
- `pure(x)`: A class method that wraps a value in the applicative context
- `ap(self, wrapped_funcs)`: Apply wrapped functions to the wrapped value
- `fmap[B](self, f)`: Inherited from Functor - map a function over the wrapped value

**Example 1: Creating a Custom Applicative (Box)**

```python
from katharos.algebra import Applicative
from collections.abc import Callable

class Box[A](Applicative[A]):
    """A simple container that wraps a single value."""
    
    def __init__(self, value: A) -> None:
        self.value = value
    
    @classmethod
    def pure[T](cls, x: T) -> 'Box[T]':
        """Wrap a value in a Box."""
        return Box(x)
    
    def fmap[B](self, f: Callable[[A], B]) -> 'Box[B]':
        """Apply a function to the wrapped value."""
        return Box(f(self.value))
    
    def ap[B](self, wrapped_funcs: 'Box[Callable[[A], B]]') -> 'Box[B]':
        """Apply a wrapped function to this Box's value."""
        return Box(wrapped_funcs.value(self.value))
    
    def __pow__[B](self, wrapped_funcs: 'Box[Callable[[A], B]]') -> 'Box[B]':
        """
        Enable the ** operator for applicative application.
        
        Note: When implementing your own Applicative subtype, you should
        override this method with proper type annotations specific to your
        type. Due to Python's type system limitations, the generic type
        parameters don't always propagate correctly through inheritance.
        """
        return self.ap(wrapped_funcs)
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Box) and self.value == other.value
    
    def __repr__(self) -> str:
        return f"Box({self.value!r})"

# Using the custom Applicative
def double(x: int) -> int:
    return x * 2

value = Box(5)
func = Box(double)

# Apply wrapped function using ** operator
result = value ** func  # Box(10)

# Using pure to lift values
pure_value = Box.pure(10)  # Box(10)

# Applicative laws verification
# Identity law
identity = lambda x: x
assert value ** Box.pure(identity) == value

# Homomorphism law
f = lambda x: x * 2
x = 5
assert Box.pure(x) ** Box.pure(f) == Box.pure(f(x))
```

**Example 2: Maybe as an Applicative**

```python
from katharos.ds.maybe import Maybe, Just, Nothing

# Maybe handles optional computations
# pure lifts a value into Just
value = Maybe.pure(10)  # Just(10)

# Applying a wrapped function
func = Just(lambda x: x * 2)
result = Just(5) ** func  # Just(10)

# Nothing propagates through applicative operations
result = Just(5) ** Nothing()  # Nothing()
result = Nothing() ** Just(lambda x: x * 2)  # Nothing()

# Combining multiple Maybe values
# Useful for validation or combining optional values
def add(x: int) -> Callable[[int], int]:
    return lambda y: x + y

result = Maybe.pure(add) ** Just(3) ** Just(5)  # Just(8)
result = Maybe.pure(add) ** Just(3) ** Nothing()  # Nothing()

# Real-world example: Form validation
def create_user(name: str) -> Callable[[int], Callable[[str], dict]]:
    return lambda age: lambda email: {
        "name": name,
        "age": age,
        "email": email
    }

# All fields present
user = Just("Alice") ** Just(30) ** Just("alice@example.com") ** Maybe.pure(create_user)
# user = Just({"name": "Alice", "age": 30, "email": "alice@example.com"})

# Missing field
user = Just("Bob") ** Nothing() ** Just("bob@example.com") ** Maybe.pure(create_user)
# user = Nothing()
```

**Example 3: Result as an Applicative for Error Handling**

```python
from katharos.ds import Result, Success, Failure

# Result handles computations that can fail
# pure lifts a value into Success
value = Result.pure(42)  # Success(42)

# Applying wrapped functions
func = Success(lambda x: x * 2)
result = Success(5) ** func  # Success(10)

# Failures propagate
result = Success(5) ** Failure(ValueError("Error"))  # Failure(ValueError("Error"))
result = Failure(ValueError("Error")) ** Success(lambda x: x * 2)  # Failure(ValueError("Error"))

# Combining multiple Results - useful for validation
def validate_age(age: int) -> Result[int]:
    if age < 0:
        return Failure(ValueError("Age cannot be negative"))
    if age > 150:
        return Failure(ValueError("Age too high"))
    return Success(age)

def validate_name(name: str) -> Result[str]:
    if not name:
        return Failure(ValueError("Name cannot be empty"))
    return Success(name)

def create_person(name: str) -> Callable[[int], dict]:
    return lambda age: {"name": name, "age": age}

# All validations pass
person = validate_name("Alice") ** validate_age(30) ** Result.pure(create_person)
# person = Success({"name": "Alice", "age": 30})

# One validation fails
person = validate_name("") ** validate_age(30) ** Result.pure(create_person)
# person = Failure(ValueError("Name cannot be empty"))
```

**Example 4: ImmutableList as an Applicative**

```python
from collections.abc import Callable

from katharos.ds.list import ImmutableList

# ImmutableList applies functions to values in a cartesian product manner
# pure creates a singleton list
value = ImmutableList[int].pure(5)  # ImmutableList([5])

# Applying wrapped functions
funcs = ImmutableList[Callable[[int], int]](
    [
        lambda x: x * 2,
        lambda x: x + 10,
    ]
)
values = ImmutableList[int]([1, 2, 3])

# Each function is applied to each value
result = values**funcs
# ImmutableList([2, 4, 6, 11, 12, 13])


# Real-world example: Generating combinations
def make_url(protocol: str) -> Callable[[str], Callable[[str], str]]:
    return lambda domain: lambda path: f"{protocol}://{domain}/{path}"


protocols = ImmutableList[str](["http", "https"])
domains = ImmutableList[str](["example.com", "test.com"])
paths = ImmutableList[str](["api", "docs"])

urls: ImmutableList[str] = paths**domains**protocols ** ImmutableList.pure(make_url)
# ImmutableList([
#     "http://example.com/api", "http://example.com/docs",
#     "http://test.com/api", "http://test.com/docs",
#     "https://example.com/api", "https://example.com/docs",
#     "https://test.com/api", "https://test.com/docs"
# ])
```

**How to Write a Subtype of Applicative:**

To create your own Applicative type, follow these steps:

**Step 1: Define Your Type**

```python
from katharos.algebra import Applicative
from collections.abc import Callable

class MyApplicative[A](Applicative[A]):
    """Your custom applicative type."""
    
    def __init__(self, value: A) -> None:
        self._value = value
```

> Note: If your type is covariant, you should use `TypeVar` with the `covariant=True` parameter.

```python
from typing import TypeVar

A = TypeVar('A', covariant=True)

class MyApplicative(Applicative[A]):
    ...
```

**Step 2: Implement the `pure` Class Method**

```python
    @classmethod
    def pure[T](cls, x: T) -> 'MyApplicative[T]':
        """
        Lift a value into the applicative context.
        
        This should wrap the value in the minimal context.
        
        Args:
            x: The value to wrap
            
        Returns:
            MyApplicative[T]: The wrapped value
        """
        return MyApplicative(x)
```

**Step 3: Implement the `fmap` Method (from Functor)**

```python
    def fmap[B](self, f: Callable[[A], B]) -> 'MyApplicative[B]':
        """
        Map a function over the wrapped value.
        
        Args:
            f: Function to apply to the value
            
        Returns:
            MyApplicative[B]: New applicative with transformed value
        """
        return MyApplicative(f(self._value))
```

**Step 4: Implement the `ap` Method**

```python
    def ap[B](
        self,
        wrapped_funcs: 'MyApplicative[Callable[[A], B]]'
    ) -> 'MyApplicative[B]':
        """
        Apply wrapped functions to this applicative's value.
        
        This is the key method that defines applicative behavior.
        
        Args:
            wrapped_funcs: An applicative containing functions
            
        Returns:
            MyApplicative[B]: Result of applying the wrapped function
        """
        # Extract the function and apply it to the value
        return MyApplicative(wrapped_funcs._value(self._value))
```

**Step 5: Add Type Hint For  `__pow__`**

```python
    def __pow__[B](self, other: 'MyApplicative[Callable[[A], B]]') -> 'MyApplicative[B]':
        return self.ap(other)
```

**Key Differences from Functor and Monad:**
- **Functor**: Only maps functions over values (`fmap`)
- **Applicative**: Can apply wrapped functions to wrapped values (`ap`), enabling combining multiple independent computations
- **Monad**: Can chain dependent computations where each step depends on the previous result (`bind`)

**Common Use Cases:**
- **Validation**: Accumulate multiple validation errors
- **Combining independent computations**: When you have multiple wrapped values to combine
- **Parsing**: Apply parsers in sequence without dependencies
- **Configuration**: Combine multiple configuration sources
- **Form handling**: Validate multiple form fields independently