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

class Max(Semigroup["Max"]):
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

class Sum(Monoid["Sum"]):
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
- A Functor wraps values in a context (e.g., `Maybe[A]`, `List[A]`, `Result[A, E]`)
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

class Box[A](Functor["Box", A]):
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
def parse_int(s: str) -> Result[int, ValueError]:
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

**How to Write a Subtype of Functor:**

To create your own Functor type, follow these steps:

**Step 1: Define Your Type**

```python
from katharos.algebra import Functor
from collections.abc import Callable

class MyFunctor[A](Functor["MyFunctor", A]):
    """Your custom functor type."""
    
    def __init__(self, value: A) -> None:
        self._value = value
```

> Note: If your type is covariant, you should use `TypeVar` with the `covariant=True` parameter.

```python
from typing import TypeVar

A = TypeVar('A', covariant=True)

class MyFunctor(Functor["MyFunctor", A]):
    ...
```

**Step 2: Implement the `fmap` Method**

```python
    def fmap[B](self, f: Callable[[A], B]) -> 'MyFunctor[B]':
        """
        Map a function over the wrapped value.
        
        This is the key method that defines functor behavior.
        
        Args:
            f: Function to apply to the value
            
        Returns:
            MyFunctor[B]: New functor with transformed value
        """
        return MyFunctor(f(self._value))
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

class Box[A](Applicative["Box", A]):
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
    
    def ap[B](self, wrapped_funcs: Applicative['Box', Callable[[A], B]]) -> 'Box[B]':
        """Apply a wrapped function to this Box's value."""
        wrapped_funcs = cast(Box[Callable[[A], B]], wrapped_funcs)
        return Box(wrapped_funcs.value(self.value))
    
    def __pow__[B](self, wrapped_funcs: 'Applicative[Box, Callable[[A], B]]') -> 'Box[B]':
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
from typing import NamedTuple

from katharos.ds.result import Failure, Result, Success
from katharos.functools import F


class Person(NamedTuple):
    name: str
    age: int


# Result handles computations that can fail
# pure lifts a value into Success
value = Result.pure(42)  # Success(42)

# Applying wrapped functions
func = Success(lambda x: x * 2)
result = Success(5) ** func  # Success(10)

# Failures propagate
result = Success(5) ** Failure(ValueError("Error"))  # Failure(ValueError("Error"))
result = Failure(ValueError("Error")) ** Success(
    lambda x: x * 2
)  # Failure(ValueError("Error"))


# Combining multiple Results - useful for validation
def validate_age(age: int) -> Result[int, ValueError]:
    if age < 0:
        return Failure(ValueError("Age cannot be negative"))
    if age > 150:
        return Failure(ValueError("Age too high"))
    return Success(age)


def validate_name(name: str) -> Result[str, ValueError]:
    if not name:
        return Failure(ValueError("Name cannot be empty"))
    return Success(name)


@F.curry
def create_person(name: str, age: int) -> Person:
    return Person(name=name, age=age)


# All validations pass
person = validate_age(30) ** validate_name("Alice") ** Result.pure(create_person)
# person = Success({"name": "Alice", "age": 30})

# One validation fails
person = validate_age(30) ** validate_name("") ** Result.pure(create_person)
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

class MyApplicative[A](Applicative["MyApplicative", A]):
    """Your custom applicative type."""
    
    def __init__(self, value: A) -> None:
        self._value = value
```

> Note: If your type is covariant, you should use `TypeVar` with the `covariant=True` parameter.

```python
from typing import TypeVar

A = TypeVar('A', covariant=True)

class MyApplicative(Applicative["MyApplicative", A]):
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
        wrapped_funcs: 'Applicative[MyApplicative, Callable[[A], B]]'
    ) -> 'MyApplicative[B]':
        """
        Apply wrapped functions to this applicative's value.
        
        This is the key method that defines applicative behavior.
        
        Args:
            wrapped_funcs: An applicative containing functions
            
        Returns:
            MyApplicative[B]: Result of applying the wrapped function
        """
        wrapped_funcs = cast(MyApplicative[Callable[[A], B]], wrapped_funcs) # This line is needed because python doesn't support higher kinded types, also it's safe because we know an instance of `Applicative[MyApplicative, Callable[[A], B]]` is an instance of `MyApplicative[Callable[[A], B]]`
        
        # Extract the function and apply it to the value
        return MyApplicative(wrapped_funcs._value(self._value))
```

**Step 5: Add Type Hint For  `__pow__`**

```python
    def __pow__[B](self, other: 'Applicative[MyApplicative, Callable[[A], B]]') -> 'MyApplicative[B]':
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

### Monad

A **Monad** is a powerful abstraction that represents computations as a series of steps. It extends Applicative with the ability to chain dependent computations, where each step can depend on the result of the previous step.

**Core Concept:**
- A Monad extends Applicative with the `bind` operation (also known as `flatMap` or `>>=`)
- `bind` allows sequencing computations where the structure of the next computation depends on the value from the previous one
- Unlike Applicatives, Monads can flatten nested structures, preventing "layers" from accumulating
- The key difference: Applicatives combine independent computations, Monads chain dependent ones

**Mathematical Laws:**

Monads must satisfy three laws:

1. **Left Identity Law**: `ret(a).bind(f) = f(a)`
   - Wrapping a value and binding it with a function is the same as applying the function directly
   
2. **Right Identity Law**: `m.bind(ret) = m`
   - Binding a monad with `ret` (or `pure`) returns the original monad
   
3. **Associativity Law**: `m.bind(f).bind(g) = m.bind(lambda x: f(x).bind(g))`
   - The order of binding operations doesn't matter; chaining binds is associative

**Implementation:**

To create a Monad, inherit from the `Monad[A]` class and implement:
- `pure(x)`: A class method that wraps a value in the monadic context (inherited from Applicative)
- `fmap[B](self, f)`: Map a function over the wrapped value (inherited from Functor)
- `ap(self, wrapped_funcs)`: Apply wrapped functions to wrapped values (inherited from Applicative)
- `bind[B](self, f)`: Chain a computation that returns a monad

**Example 1: Creating a Custom Monad (Box)**

```python
from katharos.algebra import Monad
from collections.abc import Callable

class Box[A](Monad["Box", A]):
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
    
    def bind[B](self, f: Callable[[A], 'Box[B]']) -> 'Box[B]':
        """
        Chain a computation that returns a Box.
        
        This is the key method that makes Box a Monad.
        Unlike fmap, which wraps the result, bind expects f to return
        a Box, preventing nested Box[Box[B]] structures.
        """
        return f(self.value)
    
    def __pow__[B](self, wrapped_funcs: 'Box[Callable[[A], B]]') -> 'Box[B]':
        """
        Enable the ** operator for applicative application.
        
        Note: When implementing your own Monad subtype, you should
        override this method with proper type annotations specific to your
        type. Due to Python's type system limitations, the generic type
        parameters don't always propagate correctly through inheritance.
        """
        return self.ap(wrapped_funcs)
    
    def __or__[B](self, f: Callable[[A], 'Box[B]']) -> 'Box[B]':
        """
        Enable the | operator for monadic bind.
        
        This provides a convenient infix notation for chaining computations.
        """
        return self.bind(f)
    
    def __eq__(self, other: object) -> bool:
        return isinstance(other, Box) and self.value == other.value
    
    def __repr__(self) -> str:
        return f"Box({self.value!r})"

# Using the custom Monad
box = Box(5)

# bind chains computations that return Box
result = box.bind(lambda x: Box(x * 2))  # Box(10)

# Using the | operator for bind
result = box | (lambda x: Box(x * 2))  # Box(10)

# Chain multiple operations - this is where Monad shines
result = (Box(5)
    | (lambda x: Box(x + 3))
    | (lambda x: Box(x * 2)))  # Box(16)

# Compare with fmap - notice the difference
# fmap would create Box(Box(10)) if we returned Box from the function
# bind flattens it to just Box(10)

# Monad laws verification
# Left identity: ret(a).bind(f) = f(a)
f = lambda x: Box(x * 2)
a = 5
assert Box.pure(a).bind(f) == f(a)

# Right identity: m.bind(ret) = m
m = Box(10)
assert m.bind(Box.pure) == m

# Associativity: m.bind(f).bind(g) = m.bind(lambda x: f(x).bind(g))
g = lambda x: Box(x + 1)
assert m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))
```

**Example 2: Maybe as a Monad**

```python
from katharos.ds.maybe import Maybe, Just, Nothing

# Maybe handles optional computations with chaining
# pure lifts a value into Just
value = Maybe.pure(10)  # Just(10)

# bind chains computations that might fail
def safe_divide(x: float) -> Maybe[float]:
    return Just(10.0 / x) if x != 0 else Nothing()

def safe_sqrt(x: float) -> Maybe[float]:
    return Just(x ** 0.5) if x >= 0 else Nothing()

# Chain dependent computations using bind
result = Just(4.0) | safe_sqrt | (lambda x: safe_divide(x))
# Just(5.0) because sqrt(4) = 2, then 10/2 = 5

# Nothing propagates through the chain
result = Just(-4.0) | safe_sqrt | (lambda x: safe_divide(x))
# Nothing() because sqrt of negative fails

result = Just(0.0) | safe_sqrt | (lambda x: safe_divide(x))
# Nothing() because division by zero fails

# Real-world example: Database queries
def find_user(user_id: int) -> Maybe[dict]:
    # Simulate database lookup
    users = {1: {"name": "Alice", "dept_id": 10}}
    return Just(users[user_id]) if user_id in users else Nothing()

def find_department(dept_id: int) -> Maybe[dict]:
    # Simulate database lookup
    depts = {10: {"name": "Engineering"}}
    return Just(depts[dept_id]) if dept_id in depts else Nothing()

# Chain dependent queries
user_with_dept = (
    find_user(1)
    | (lambda user: find_department(user["dept_id"]))
)
# Just({"name": "Engineering"})

# Missing user propagates Nothing
user_with_dept = (
    find_user(999)
    | (lambda user: find_department(user["dept_id"]))
)
# Nothing() - second query never executes
```

**Example 3: Result as a Monad for Error Handling**

```python
from katharos.ds import Result, Success, Failure

# Result handles computations that can fail with error propagation
# pure lifts a value into Success
value = Result.pure(42)  # Success(42)

# bind chains computations that can fail
def parse_int(s: str) -> Result[int, ValueError]:
    try:
        return Success(int(s))
    except ValueError as e:
        return Failure(e)

def divide(x: int) -> Result[float, ValueError]:
    if x == 0:
        return Failure(ValueError("Division by zero"))
    return Success(100.0 / x)

def format_result(x: float) -> Result[str, Exception]:
    return Success(f"Result: {x:.2f}")

# Chain dependent computations using | operator
result = (
    parse_int("10")
    | divide
    | format_result
)
# Success("Result: 10.00")

# Errors propagate through the chain
result = (
    parse_int("invalid")
    | divide
    | format_result
)
# Failure(ValueError("invalid literal for int()..."))

result = (
    parse_int("0")
    | divide
    | format_result
)
# Failure(ValueError("Division by zero"))

# Real-world example: File processing pipeline
def read_file(path: str) -> Result[str, Exception]:
    try:
        with open(path) as f:
            return Success(f.read())
    except Exception as e:
        return Failure(e)

def parse_json(content: str) -> Result[dict, Exception]:
    try:
        import json
        return Success(json.loads(content))
    except Exception as e:
        return Failure(e)

def validate_schema(data: dict) -> Result[dict, ValueError]:
    if "name" in data and "age" in data:
        return Success(data)
    return Failure(ValueError("Invalid schema"))

# Chain file operations
result = (
    read_file("user.json")
    | parse_json
    | validate_schema
)
# Success({...}) or Failure(...) depending on each step
```

**Example 4: ImmutableList as a Monad**

```python
from katharos.ds import ImmutableList

# ImmutableList as a Monad represents non-deterministic computations
# pure creates a singleton list
value = ImmutableList.pure(5)  # ImmutableList([5])

# bind flattens nested lists (flatMap)
def duplicate(x: int) -> ImmutableList[int]:
    return ImmutableList([x, x])

numbers = ImmutableList([1, 2, 3])

# bind applies the function and flattens the result
result = numbers | duplicate
# ImmutableList([1, 1, 2, 2, 3, 3])

# Compare with fmap - it would create nested lists
nested = numbers.fmap(duplicate)
# ImmutableList([ImmutableList([1, 1]), ImmutableList([2, 2]), ImmutableList([3, 3])])

# Real-world example: Generating combinations
def pairs_with(x: int) -> ImmutableList[tuple[int, int]]:
    return ImmutableList([(x, 1), (x, 2), (x, 3)])

result = ImmutableList([10, 20]) | pairs_with
# ImmutableList([(10, 1), (10, 2), (10, 3), (20, 1), (20, 2), (20, 3)])

# Nested bind for cartesian products
def make_pair(x: int) -> ImmutableList[tuple[int, int]]:
    return ImmutableList([2, 3, 4]).fmap(lambda y: (x, y))

result = ImmutableList([1, 2]) | make_pair
# ImmutableList([(1, 2), (1, 3), (1, 4), (2, 2), (2, 3), (2, 4)])
```

**How to Write a Subtype of Monad:**

To create your own Monad type, follow these steps:

**Step 1: Define Your Type**

```python
from katharos.algebra import Monad
from collections.abc import Callable

class MyMonad[A](Monad["MyMonad", A]):
    """Your custom monad type."""
    
    def __init__(self, value: A) -> None:
        self._value = value
```

> Note: If your type is covariant, you should use `TypeVar` with the `covariant=True` parameter.

```python
from typing import TypeVar
from typing import cast

A = TypeVar('A', covariant=True)

class MyMonad(Monad["MyMonad", A]):
    ...
```

**Step 2: Implement the `pure` Class Method (from Applicative)**

```python
    @classmethod
    def pure[T](cls, x: T) -> 'MyMonad[T]':
        """
        Lift a value into the monadic context.
        
        This should wrap the value in the minimal context.
        
        Args:
            x: The value to wrap
            
        Returns:
            MyMonad[T]: The wrapped value
        """
        return MyMonad(x)
```

**Step 3: Implement the `fmap` Method (from Functor)**

```python
    def fmap[B](self, f: Callable[[A], B]) -> 'MyMonad[B]':
        """
        Map a function over the wrapped value.
        
        Args:
            f: Function to apply to the value
            
        Returns:
            MyMonad[B]: New monad with transformed value
        """
        return MyMonad(f(self._value))
```

**Step 4: Implement the `ap` Method (from Applicative)**

```python
    def ap[B](
        self,
        wrapped_funcs: Applicative['MyMonad', Callable[[A], B]]
    ) -> 'MyMonad[B]':
        """
        Apply wrapped functions to this monad's value.
        
        Args:
            wrapped_funcs: A monad containing functions
            
        Returns:
            MyMonad[B]: Result of applying the wrapped function
        """
        wrapped_funcs = cast(MyMonad[Callable[[A], B]], wrapped_funcs) # This line is needed because python doesn't support higher kinded types, also it's safe because we know an instance of `Applicative['MyMonad', Callable[[A], B]]` is an instance of `MyMonad[Callable[[A], B]]`
        return MyMonad(wrapped_funcs._value(self._value))
```

**Step 5: Implement the `bind` Method**

```python
    def bind[B](
        self,
        f: Callable[[A], Monad['MyMonad', B]]
    ) -> 'MyMonad[B]':
        """
        Chain a computation that returns a monad.
        
        This is the key method that defines monadic behavior.
        Unlike fmap, the function f returns a monad, and bind
        flattens the result to prevent nested monads.
        
        Args:
            f: A function that takes a value and returns a monad
            
        Returns:
            MyMonad[B]: The result of applying f and flattening
        """
        # Apply the function to the value - it returns MyMonad[B]
        # No need to wrap again, just return the result
        f = cast(Callable[[A], MyMonad[B]]) # This line is needed because python doesn't support higher kinded types, also it's safe because we know and instance of `Monad['MyMonad', B]` is an instance of MyMonad[B]
        return f(self._value)
```

**Step 6: Add Type Hints For Operators**

```python
    def __pow__[B](self, other: Applicative['MyMonad', Callable[[A], B]]) -> 'MyMonad[B]':
        """Enable ** operator for applicative application."""
        return self.ap(other)
    
    def __or__[B](self, f: Callable[[A], Monad['MyMonad', B]]) -> 'MyMonad[B]':
        """Enable | operator for monadic bind."""
        return self.bind(f)
```

**Key Differences from Functor and Applicative:**
- **Functor**: Only maps functions over values (`fmap`) - transforms values in context
- **Applicative**: Can apply wrapped functions to wrapped values (`ap`) - combines independent computations
- **Monad**: Can chain dependent computations where each step depends on the previous result (`bind`) - enables sequential, dependent operations

**Common Use Cases:**
- **Error handling**: Chain operations that can fail, with automatic error propagation
- **Optional values**: Chain operations on values that might not exist
- **Asynchronous operations**: Chain async operations where each depends on the previous result
- **State management**: Thread state through a sequence of computations
- **Parsing**: Chain parsers where each parser depends on the previous result
- **Database queries**: Chain queries where each query depends on the previous result
- **I/O operations**: Chain I/O operations while maintaining purity


## ds (Data Structures)

The `ds` module provides functional data structures that implement algebraic type classes (Functor, Applicative, Monad, Semigroup, Monoid). These data structures enable type-safe, composable functional programming patterns in Python.

### Overview

The module includes:
- **Maybe**: Optional values with type-safe null handling
- **Result**: Error handling without exceptions
- **ImmutableList**: Immutable list with monadic operations
- **NonEmptyList**: List guaranteed to have at least one element
- **IO**: Encapsulation of side effects
- **MonoidMaybe**: Monoid wrapper for Maybe values

### Maybe

The `Maybe` type represents computations that might fail or values that might be absent. It's an alternative to using `None` that forces explicit handling of the absence case.

#### Constructors

```python
from katharos.ds import Maybe, Just, Nothing

# Create a value that exists
value = Just(42)

# Create an absent value
absent = Nothing()

# Using pure (returns Just)
value = Maybe.pure(42)
```

#### Basic Operations

**Functor - Transform values:**
```python
# Map a function over a Just value
result = Just(5).fmap(lambda x: x * 2)  # Just(10)

# Map over Nothing returns Nothing
result = Nothing().fmap(lambda x: x * 2)  # Nothing()
```

**Applicative - Apply wrapped functions:**
```python
# Apply a wrapped function to a wrapped value
value = Just(5)
func = Just(lambda x: x * 2)
result = value.ap(func)  # Just(10)

# Using ** operator
result = value ** func  # Just(10)

# If either is Nothing, result is Nothing
result = Nothing() ** Just(lambda x: x * 2)  # Nothing()
```

**Monad - Chain dependent computations:**
```python
def safe_divide(x: float) -> Maybe[float]:
    if x == 0:
        return Nothing()
    return Just(10.0 / x)

def safe_sqrt(x: float) -> Maybe[float]:
    if x < 0:
        return Nothing()
    return Just(x ** 0.5)

# Chain operations with bind
result = Just(2).bind(safe_divide).bind(safe_sqrt)  # Just(2.236...)

# Using | operator for chaining
result = Just(4) | safe_divide | safe_sqrt  # Just(1.581...)

# Failure propagates automatically
result = Just(0) | safe_divide | safe_sqrt  # Nothing()
```

#### Pattern Matching

```python
match maybe_value:
    case Just(value=x):
        print(f"Got value: {x}")
    case Nothing():
        print("No value")
```

#### Use Cases

- **Null safety**: Replace `None` with explicit Maybe types
- **Optional configuration**: Handle missing config values
- **Database queries**: Represent records that might not exist
- **Parsing**: Handle values that might fail to parse
- **API responses**: Handle optional fields in responses

### MonoidMaybe

A Monoid wrapper for `Maybe` values where the inner type is a Semigroup. Enables combining Maybe values with a sensible identity element.

```python
from katharos.ds import MonoidMaybe, Just, Nothing

# Create MonoidMaybe instances (assuming inner type is Semigroup)
m1 = MonoidMaybe(Just(value1))
m2 = MonoidMaybe(Just(value2))

# Combine using monoid operation
result = m1.op(m2)  # Combines inner values if both are Just

# Identity element
identity = MonoidMaybe.identity()  # MonoidMaybe(Nothing())

# Nothing acts as identity
MonoidMaybe(Nothing()).op(m1) == m1  # True
m1.op(MonoidMaybe(Nothing())) == m1  # True
```

### Result

The `Result` type represents computations that can either succeed with a value (`Success`) or fail with an exception (`Failure`). It provides railway-oriented programming for error handling.

#### Constructors

```python
from katharos.ds import Result, Success, Failure

# Create a successful result
success = Success(42)

# Create a failed result
failure = Failure(ValueError("Something went wrong"))

# Using pure (returns Success)
success = Result.pure(42)
```

#### Basic Operations

**Functor - Transform successful values:**
```python
# Map over Success
result = Success(5).fmap(lambda x: x * 2)  # Success(10)

# Map over Failure returns the same Failure
result = Failure(ValueError("error")).fmap(lambda x: x * 2)  # Failure(ValueError("error"))
```

**Applicative - Apply wrapped functions:**
```python
# Apply a wrapped function
value = Success(5)
func = Success(lambda x: x * 2)
result = value.ap(func)  # Success(10)

# Using ** operator
result = value ** func  # Success(10)

# Failure propagates
result = Failure(ValueError("error")) ** func  # Failure(ValueError("error"))
```

**Monad - Chain operations that can fail:**
```python
def parse_int(s: str) -> Result[int, ValueError]:
    try:
        return Success(int(s))
    except ValueError as e:
        return Failure(e)

def divide_by_two(x: int) -> Result[float, Exception]:
    return Success(x / 2)

# Chain operations with bind
result = Success("42").bind(parse_int).bind(divide_by_two)  # Success(21.0)

# Using | operator
result = Success("42") | parse_int | divide_by_two  # Success(21.0)

# Error propagates through the chain
result = Success("not_a_number") | parse_int | divide_by_two  # Failure(ValueError(...))
```

#### Pattern Matching

```python
match result:
    case Success(value=x):
        print(f"Success: {x}")
    case Failure(error=e):
        print(f"Error: {e}")
```

#### Use Cases

- **Error handling**: Replace try/except with functional error handling
- **Validation**: Chain validation steps with automatic error propagation
- **File I/O**: Handle file operations that can fail
- **Network requests**: Handle API calls that can fail
- **Data transformation pipelines**: Chain transformations with error handling

### ImmutableList

An immutable list implementation that supports Functor, Applicative, Monad, and Monoid operations. Provides a functional alternative to Python's mutable lists.

#### Constructors

```python
from katharos.ds import ImmutableList

# Create from a list
lst = ImmutableList([1, 2, 3, 4, 5])

# Create a singleton list
singleton = ImmutableList.pure(42)  # ImmutableList([42])

# Empty list (identity element)
empty = ImmutableList.identity()  # ImmutableList([])
```

#### Basic Operations

**Functor - Transform elements:**
```python
# Map a function over all elements
numbers = ImmutableList([1, 2, 3, 4])
doubled = numbers.fmap(lambda x: x * 2)  # ImmutableList([2, 4, 6, 8])

# Type transformations
strings = numbers.fmap(str)  # ImmutableList(['1', '2', '3', '4'])
```

**Applicative - Cartesian product of functions and values:**
```python
# Apply multiple functions to multiple values
values = ImmutableList([1, 2, 3])
funcs = ImmutableList([lambda x: x * 2, lambda x: x + 10])

result = values.ap(funcs)
# ImmutableList([2, 4, 6, 11, 12, 13])

# Using ** operator
result = values ** funcs
```

**Monad - Flatten nested lists:**
```python
# bind (flatMap) flattens the result
def duplicate(x: int) -> ImmutableList[int]:
    return ImmutableList([x, x])

numbers = ImmutableList([1, 2, 3])
result = numbers.bind(duplicate)  # ImmutableList([1, 1, 2, 2, 3, 3])

# Using | operator
result = numbers | duplicate

# Generate combinations
def pair_with_next(x: int) -> ImmutableList[tuple[int, int]]:
    return ImmutableList([(x, x+1), (x, x+2)])

result = ImmutableList([1, 2]) | pair_with_next
# ImmutableList([(1, 2), (1, 3), (2, 3), (2, 4)])
```

**Monoid - Concatenation:**
```python
# Concatenate lists
list1 = ImmutableList([1, 2, 3])
list2 = ImmutableList([4, 5, 6])

# Using op method
result = list1.op(list2)  # ImmutableList([1, 2, 3, 4, 5, 6])

# Using @ operator (semigroup operation)
result = list1 @ list2  # ImmutableList([1, 2, 3, 4, 5, 6])

# Using + operator
result = list1 + list2  # ImmutableList([1, 2, 3, 4, 5, 6])

# Identity element
empty = ImmutableList.identity()
list1.op(empty) == list1  # True
```

#### Sequence Operations

```python
# Length
len(ImmutableList([1, 2, 3]))  # 3

# Indexing
lst = ImmutableList([10, 20, 30])
lst[0]  # 10
lst[1]  # 20

# Membership
3 in ImmutableList([1, 2, 3])  # True

# Iteration
for x in ImmutableList([1, 2, 3]):
    print(x)

# Convert to list
list(ImmutableList([1, 2, 3]))  # [1, 2, 3]

# Equality and hashing
ImmutableList([1, 2]) == ImmutableList([1, 2])  # True
hash(ImmutableList([1, 2]))  # Can be used in sets/dicts
```

#### Use Cases

- **Immutable data structures**: Thread-safe data sharing
- **Functional pipelines**: Chain transformations on collections
- **List comprehensions**: Functional alternative with explicit types
- **Combinations and permutations**: Generate combinations using bind
- **Data processing**: Transform collections functionally

### NonEmptyList

A list guaranteed to contain at least one element. Useful when you need to ensure a collection is never empty.

#### Constructors

```python
from katharos.ds import NonEmptyList

# Create with head and tail
nel = NonEmptyList(head=1, tail=[2, 3, 4])

# Create singleton
singleton = NonEmptyList.pure(42)  # NonEmptyList(head=42, tail=[])
```

#### Properties

```python
nel = NonEmptyList(head=1, tail=[2, 3, 4])

# Access head (first element)
nel.head  # 1

# Access tail (remaining elements)
nel.tail  # [2, 3, 4]
```

#### Operations

**Functor:**
```python
nel = NonEmptyList(head=1, tail=[2, 3])
doubled = nel.fmap(lambda x: x * 2)  # NonEmptyList(head=2, tail=[4, 6])
```

**Applicative:**
```python
values = NonEmptyList(head=1, tail=[2])
funcs = NonEmptyList(head=lambda x: x * 2, tail=[lambda x: x + 10])
result = values.ap(funcs)  # NonEmptyList with all combinations
```

**Monad:**
```python
def duplicate(x: int) -> NonEmptyList[int]:
    return NonEmptyList(head=x, tail=[x])

nel = NonEmptyList(head=1, tail=[2])
result = nel.bind(duplicate)  # NonEmptyList(head=1, tail=[1, 2, 2])
```

**Semigroup (Concatenation):**
```python
nel1 = NonEmptyList(head=1, tail=[2])
nel2 = NonEmptyList(head=3, tail=[4])

# Using op method
result = nel1.op(nel2)  # NonEmptyList(head=1, tail=[2, 3, 4])

# Using + operator
result = nel1 + nel2  # NonEmptyList(head=1, tail=[2, 3, 4])
```

#### Use Cases

- **Aggregations**: Ensure at least one value for operations like max/min
- **Configuration**: Require at least one option
- **User input**: Validate non-empty collections
- **Graph algorithms**: Represent paths that must have at least one node
- **Fold operations**: Safe folding without needing initial value

### IO

The `IO` type encapsulates side effects, allowing you to describe I/O operations without immediately executing them. This maintains referential transparency in functional code.

#### Constructors

```python
from katharos.ds import IO

# Create an IO action with a value
io = IO(42)

# Using pure
io = IO.pure(42)
```

#### Basic Operations

**Functor - Transform the value:**
```python
io = IO(5)
doubled = io.fmap(lambda x: x * 2)  # IO(10)

# Value is not executed until you call execute()
doubled.value  # 10
```

**Applicative - Apply wrapped functions:**
```python
value = IO(5)
func = IO(lambda x: x * 2)

result = value.ap(func)  # IO(10)

# Using ** operator
result = value ** func  # IO(10)
```

**Monad - Chain I/O operations:**
```python
def read_config(path: str) -> IO[dict]:
    # In practice, this would read from file
    return IO({"setting": "value"})

def process_config(config: dict) -> IO[str]:
    return IO(config.get("setting", "default"))

# Chain operations
result = IO("config.json").bind(read_config).bind(process_config)

# Using | operator
result = IO("config.json") | read_config | process_config
```

**Sequencing - Combine side effects:**
```python
from katharos.ds.side_effect import FunctionWithSideEffect

def print_action():
    print("Hello")

def write_action():
    print("World")

io1 = IO(None, FunctionWithSideEffect(f=print_action))
io2 = IO(None, FunctionWithSideEffect(f=write_action))

# Sequence operations (>> operator)
combined = io1 >> io2

# Execute both side effects in order
combined.execute()  # Prints: Hello\nWorld
```

#### Execution

```python
# Create an IO action
io = IO(42)

# Execute the side effects (if any)
io.execute()

# Access the value
io.value  # 42
```

#### Use Cases

- **File I/O**: Describe file operations without executing them
- **Console I/O**: Describe print/input operations
- **Database operations**: Describe queries without executing
- **Network requests**: Describe HTTP calls without making them
- **Testing**: Mock I/O operations by replacing IO actions
- **Composition**: Build complex I/O operations from simple ones

### Common Patterns

#### Error Handling with Result

```python
from katharos.ds import Result, Success, Failure

def validate_age(age: int) -> Result[int, ValueError]:
    if age < 0:
        return Failure(ValueError("Age cannot be negative"))
    if age > 150:
        return Failure(ValueError("Age too high"))
    return Success(age)

def calculate_birth_year(age: int) -> Result[int, Exception]:
    from datetime import datetime
    return Success(datetime.now().year - age)

# Chain validations
result = Success(25) | validate_age | calculate_birth_year
match result:
    case Success(value=year):
        print(f"Born in {year}")
    case Failure(error=e):
        print(f"Error: {e}")
```

#### Optional Values with Maybe

```python
from katharos.ds import Maybe, Just, Nothing

def get_user(user_id: int) -> Maybe[dict]:
    # Simulate database lookup
    users = {1: {"name": "Alice"}, 2: {"name": "Bob"}}
    if user_id in users:
        return Just(users[user_id])
    return Nothing()

def get_name(user: dict) -> Maybe[str]:
    return Just(user.get("name")) if "name" in user else Nothing()

# Chain operations
result = Just(1) | get_user | get_name
match result:
    case Just(value=name):
        print(f"User name: {name}")
    case Nothing():
        print("User not found")
```

#### List Comprehensions with ImmutableList

```python
from katharos.ds import ImmutableList

# Traditional list comprehension
# result = [x * y for x in [1, 2, 3] for y in [10, 20]]

# Functional equivalent using bind
numbers = ImmutableList([1, 2, 3])
multipliers = ImmutableList([10, 20])

result = numbers.bind(
    lambda x: multipliers.fmap(lambda y: x * y)
)
# ImmutableList([10, 20, 20, 40, 30, 60])
```

#### Combining Multiple Maybe Values

```python
from katharos.ds import Maybe, Just, Nothing

def add(x: int) -> Callable[[int], int]:
    return lambda y: x + y

# Applicative style - combine independent computations
maybe_x = Just(5)
maybe_y = Just(10)
maybe_func = Just(add(5))

result = maybe_y.ap(maybe_func)  # Just(15)

# If any is Nothing, result is Nothing
result = Nothing().ap(Just(lambda x: x + 1))  # Nothing()
```

### Operator Summary

| Operator | Type Class | Method | Description |
|----------|-----------|---------|-------------|
| `fmap(f)` | Functor | - | Map function over wrapped value |
| `**` | Applicative | `ap` | Apply wrapped function to wrapped value |
| `\|` | Monad | `bind` | Chain dependent computations |
| `>>` | Monad | `sequence` | Sequence actions, discard first result |
| `@` | Semigroup | `op` | Combine two values |

### Type Safety

All data structures are fully typed with Python's type system:

```python
from katharos.ds import Maybe, Just, ImmutableList

# Type inference works correctly
numbers: Maybe[int] = Just(42)
strings: ImmutableList[str] = ImmutableList(["a", "b", "c"])

# Type transformations are tracked
result: Maybe[str] = numbers.fmap(str)  # Maybe[int] -> Maybe[str]
```

### Algebraic Laws

All data structures satisfy their respective algebraic laws:

**Functor Laws:**
1. Identity: `x.fmap(id) == x`
2. Composition: `x.fmap(f).fmap(g) == x.fmap(lambda x: g(f(x)))`

**Applicative Laws:**
1. Identity: `v.ap(pure(id)) == v`
2. Homomorphism: `pure(x).ap(pure(f)) == pure(f(x))`
3. Interchange: `pure(y).ap(u) == u.ap(pure(lambda f: f(y)))`

**Monad Laws:**
1. Left identity: `pure(x).bind(f) == f(x)`
2. Right identity: `m.bind(pure) == m`
3. Associativity: `m.bind(f).bind(g) == m.bind(lambda x: f(x).bind(g))`

**Monoid Laws:**
1. Left identity: `identity.op(x) == x`
2. Right identity: `x.op(identity) == x`
3. Associativity: `(x.op(y)).op(z) == x.op(y.op(z))`

These laws ensure predictable, composable behavior across all operations.

## functools

The `functools` module provides utility functions for functional programming, including function composition, identity, and fold operations. All utilities are available through the `F` class as static methods.

### Overview

The module provides:
- **compose**: Function composition
- **id**: Identity function
- **foldl**: Left fold over iterables
- **foldr**: Right fold over iterables
- **sigma**: Combine semigroup elements

### F Class

All utilities are accessed through the `F` class as static methods. No instantiation is required.

```python
from katharos.functools import F
```

### compose

Compose two functions together, creating a new function that applies them in sequence.

**Signature:**
```python
F.compose[A, B, C](f: Callable[[B], C]) -> Callable[[Callable[[A], B]], Callable[[A], C]]
```

**Description:**

Function composition follows mathematical notation: `(f ∘ g)(x) = f(g(x))`. The `compose` function takes a function `f` and returns a function that takes another function `g`, producing a composed function that applies `g` first, then `f`.

**Examples:**

```python
from katharos.functools import F

# Basic composition
def add_one(x: int) -> int:
    return x + 1

def multiply_by_two(x: int) -> int:
    return x * 2

# Compose: multiply_by_two(add_one(x))
composed = F.compose(multiply_by_two)(add_one)
result = composed(3)  # (3 + 1) * 2 = 8

# String operations
def to_upper(s: str) -> str:
    return s.upper()

def add_exclamation(s: str) -> str:
    return s + "!"

composed = F.compose(add_exclamation)(to_upper)
result = composed("hello")  # "HELLO!"

# Type transformations
def int_to_str(x: int) -> str:
    return str(x)

def str_length(s: str) -> int:
    return len(s)

composed = F.compose(str_length)(int_to_str)
result = composed(12345)  # 5
```

**Multiple Compositions:**

```python
def add_one(x: int) -> int:
    return x + 1

def multiply_by_two(x: int) -> int:
    return x * 2

def subtract_three(x: int) -> int:
    return x - 3

# Compose multiple functions
# subtract_three(multiply_by_two(add_one(x)))
composed = F.compose(subtract_three)(
    F.compose(multiply_by_two)(add_one)
)
result = composed(5)  # ((5 + 1) * 2) - 3 = 9
```

**Use Cases:**
- **Pipeline construction**: Build data transformation pipelines
- **Function reuse**: Combine existing functions without creating new ones
- **Point-free style**: Write code without explicitly mentioning arguments
- **Abstraction**: Create higher-level operations from simpler ones

### id

The identity function returns its argument unchanged. Useful as a default or no-op function.

**Signature:**
```python
F.id[A](x: A) -> A
```

**Description:**

The identity function is the neutral element for function composition: `compose(f)(id) = f` and `compose(id)(f) = f`. It's commonly used in functional programming as a default function or to satisfy type requirements.

**Examples:**

```python
from katharos.functools import F

# Basic usage
F.id(42)        # 42
F.id("hello")   # "hello"
F.id([1, 2, 3]) # [1, 2, 3]
F.id(None)      # None

# Identity preserves object identity
lst = [1, 2, 3]
F.id(lst) is lst  # True

# Used with fmap (from Functor)
from katharos.ds import Just

maybe_value = Just(42)
same_value = maybe_value.fmap(F.id)  # Just(42)

# Used as a default function
def process(value: int, transform: Callable[[int], int] = F.id) -> int:
    return transform(value)

process(10)              # 10 (uses identity)
process(10, lambda x: x * 2)  # 20 (uses custom function)
```

**Use Cases:**
- **Default function parameter**: Provide a no-op default
- **Testing functor laws**: Verify `fmap(id) = id`
- **Placeholder**: Use where a function is required but no transformation is needed
- **Function composition identity**: Neutral element in composition

### foldl

Left fold (reduce) a function over an iterable, processing elements from left to right.

**Signature:**
```python
F.foldl[A, B](f: Callable[[B, A], B], acc: B, xs: Iterable[A]) -> B
```

**Description:**

Left fold processes elements from left to right, accumulating a result. The function `f` takes the accumulator as the first argument and the current element as the second. This is equivalent to Python's `functools.reduce` but with explicit initial value.

**Process:** `foldl(f, acc, [x1, x2, x3]) = f(f(f(acc, x1), x2), x3)`

**Examples:**

```python
from katharos.functools import F

# Sum of numbers
result = F.foldl(lambda acc, x: acc + x, 0, [1, 2, 3, 4])
# 0 + 1 = 1, 1 + 2 = 3, 3 + 3 = 6, 6 + 4 = 10
# Result: 10

# String concatenation
result = F.foldl(lambda acc, x: acc + x, "", ["a", "b", "c"])
# "" + "a" = "a", "a" + "b" = "ab", "ab" + "c" = "abc"
# Result: "abc"

# Build a list
result = F.foldl(lambda acc, x: acc + [x], [], [1, 2, 3])
# Result: [1, 2, 3]

# Reverse a list
result = F.foldl(lambda acc, x: [x] + acc, [], [1, 2, 3])
# [] + [1] = [1], [2, 1], [3, 2, 1]
# Result: [3, 2, 1]

# Product of numbers
result = F.foldl(lambda acc, x: acc * x, 1, [2, 3, 4])
# Result: 24

# Count elements
result = F.foldl(lambda acc, x: acc + 1, 0, [10, 20, 30])
# Result: 3

# Maximum value
result = F.foldl(lambda acc, x: max(acc, x), float('-inf'), [3, 7, 2, 9, 1])
# Result: 9
```

**With Generators:**

```python
# Works with any iterable
result = F.foldl(lambda acc, x: acc + x, 0, (x for x in range(1, 5)))
# Result: 10
```

**Use Cases:**
- **Aggregation**: Sum, product, min, max operations
- **List construction**: Build lists from iterables
- **State accumulation**: Thread state through a sequence
- **Custom reductions**: Any operation that combines elements sequentially

### foldr

Right fold (reduce) a function over an iterable, processing elements from right to left.

**Signature:**
```python
F.foldr[A, B](f: Callable[[A, B], B], acc: B, xs: Iterable[A]) -> B
```

**Description:**

Right fold processes elements from right to left, accumulating a result. The function `f` takes the current element as the first argument and the accumulator as the second. This is useful for operations where order matters or for building right-associative structures.

**Process:** `foldr(f, acc, [x1, x2, x3]) = f(x1, f(x2, f(x3, acc)))`

**Examples:**

```python
from katharos.functools import F

# Sum of numbers
result = F.foldr(lambda x, acc: x + acc, 0, [1, 2, 3, 4])
# f(1, f(2, f(3, f(4, 0))))
# Result: 10

# String concatenation
result = F.foldr(lambda x, acc: x + acc, "", ["a", "b", "c"])
# f("a", f("b", f("c", "")))
# "a" + ("b" + ("c" + "")) = "abc"
# Result: "abc"

# Build a list (preserves order)
result = F.foldr(lambda x, acc: [x] + acc, [], [1, 2, 3])
# Result: [1, 2, 3]

# Subtraction (demonstrates right-associativity)
result = F.foldr(lambda x, acc: x - acc, 0, [1, 2, 3])
# 1 - (2 - (3 - 0)) = 1 - (2 - 3) = 1 - (-1) = 2
# Result: 2

# Compare with foldl for non-associative operations
foldl_result = F.foldl(lambda acc, x: acc - x, 0, [1, 2, 3])
# (0 - 1) - 2 - 3 = -6
# Result: -6 (different from foldr!)

# Product of numbers
result = F.foldr(lambda x, acc: x * acc, 1, [2, 3, 4])
# Result: 24
```

**Use Cases:**
- **Right-associative operations**: Operations where right-to-left matters
- **List construction**: Build lists while preserving order
- **Tree building**: Construct right-leaning trees
- **Lazy evaluation**: Can short-circuit in lazy languages (not applicable in Python)

### Fold Comparison

**Associative Operations:**

For associative operations (like addition, multiplication), `foldl` and `foldr` produce the same result:

```python
# Addition is associative: (a + b) + c = a + (b + c)
F.foldl(lambda acc, x: acc + x, 0, [1, 2, 3, 4])  # 10
F.foldr(lambda x, acc: x + acc, 0, [1, 2, 3, 4])  # 10
```

**Non-Associative Operations:**

For non-associative operations (like subtraction), they produce different results:

```python
# Subtraction is not associative
F.foldl(lambda acc, x: acc - x, 0, [1, 2, 3])  # -6
F.foldr(lambda x, acc: x - acc, 0, [1, 2, 3])  # 2
```

**Performance Considerations:**

- `foldl` is generally more efficient in strict languages like Python
- `foldr` requires converting the iterable to a list and reversing it
- For large iterables with associative operations, prefer `foldl`

### sigma

Combine all elements of a non-empty list using the semigroup operation (`@` operator).

**Signature:**
```python
F.sigma[A: Semigroup](xs: NonEmptyList[A]) -> A
```

**Description:**

The `sigma` function (Σ) combines all elements in a non-empty list using their semigroup operation. This is a specialized fold that uses the `@` operator (matmul) which is overloaded for semigroup types.

**Examples:**

```python
from katharos.functools import F
from katharos.ds import NonEmptyList, ImmutableList

# Combine ImmutableLists (which are Semigroups)
lists = NonEmptyList(
    head=ImmutableList([1, 2]),
    tail=[ImmutableList([3, 4]), ImmutableList([5, 6])]
)
result = F.sigma(lists)
# ImmutableList([1, 2]) @ ImmutableList([3, 4]) @ ImmutableList([5, 6])
# Result: ImmutableList([1, 2, 3, 4, 5, 6])

# Combine NonEmptyLists
nels = NonEmptyList(
    head=NonEmptyList(head=1, tail=[2]),
    tail=[NonEmptyList(head=3, tail=[4])]
)
result = F.sigma(nels)
# Result: NonEmptyList(head=1, tail=[2, 3, 4])
```

**Custom Semigroups:**

```python
from katharos.algebra import Semigroup

class Sum(Semigroup["Sum"]):
    def __init__(self, value: int):
        self.value = value
    
    def op(self, other: "Sum") -> "Sum":
        return Sum(self.value + other.value)

# Combine Sum instances
sums = NonEmptyList(
    head=Sum(1),
    tail=[Sum(2), Sum(3), Sum(4)]
)
result = F.sigma(sums)
# Result: Sum(10)
```

**Use Cases:**
- **Concatenation**: Combine multiple lists or strings
- **Aggregation**: Sum or combine custom semigroup types
- **Monoid operations**: Combine elements with associative operations
- **Data merging**: Merge multiple data structures

### Common Patterns

#### Building Pipelines with Compose

```python
from katharos.functools import F

# Define transformations
def parse_int(s: str) -> int:
    return int(s)

def double(x: int) -> int:
    return x * 2

def to_string(x: int) -> str:
    return f"Result: {x}"

# Build pipeline
pipeline = F.compose(to_string)(F.compose(double)(parse_int))

# Use pipeline
result = pipeline("21")  # "Result: 42"
```

#### Implementing Map with Fold

```python
from katharos.functools import F

def map_with_foldl(f, xs):
    return F.foldl(lambda acc, x: acc + [f(x)], [], xs)

result = map_with_foldl(lambda x: x * 2, [1, 2, 3, 4])
# Result: [2, 4, 6, 8]
```

#### Implementing Filter with Fold

```python
from katharos.functools import F

def filter_with_foldl(predicate, xs):
    return F.foldl(
        lambda acc, x: acc + [x] if predicate(x) else acc,
        [],
        xs
    )

result = filter_with_foldl(lambda x: x % 2 == 0, [1, 2, 3, 4, 5, 6])
# Result: [2, 4, 6]
```

#### Counting with Fold

```python
from katharos.functools import F

def count_if(predicate, xs):
    return F.foldl(
        lambda acc, x: acc + 1 if predicate(x) else acc,
        0,
        xs
    )

result = count_if(lambda x: x > 5, [1, 3, 6, 8, 2, 9])
# Result: 3
```

#### Grouping with Fold

```python
from katharos.functools import F

def group_by(key_func, xs):
    def add_to_group(acc, x):
        key = key_func(x)
        if key not in acc:
            acc[key] = []
        acc[key].append(x)
        return acc
    
    return F.foldl(add_to_group, {}, xs)

result = group_by(lambda x: x % 2, [1, 2, 3, 4, 5, 6])
# Result: {1: [1, 3, 5], 0: [2, 4, 6]}
```

#### Flattening Lists with Fold

```python
from katharos.functools import F

def flatten(nested_list):
    return F.foldl(lambda acc, x: acc + x, [], nested_list)

result = flatten([[1, 2], [3, 4], [5, 6]])
# Result: [1, 2, 3, 4, 5, 6]
```

### Integration with Other Modules

#### With Maybe

```python
from katharos.functools import F
from katharos.ds import Just, Nothing

# Use id with Maybe
Just(42).fmap(F.id)  # Just(42)

# Use compose with Maybe operations
def safe_divide(x: float):
    return Nothing() if x == 0 else Just(10.0 / x)

def safe_sqrt(x: float):
    return Nothing() if x < 0 else Just(x ** 0.5)

# Compose doesn't work directly with monadic functions,
# but you can use bind (|) operator instead
result = Just(2) | safe_divide | safe_sqrt
```

#### With ImmutableList

```python
from katharos.functools import F
from katharos.ds import ImmutableList

# Use compose with fmap
add_one = lambda x: x + 1
double = lambda x: x * 2

transform = F.compose(double)(add_one)
result = ImmutableList([1, 2, 3]).fmap(transform)
# ImmutableList([4, 6, 8])

# Use foldl to sum list elements
numbers = ImmutableList([1, 2, 3, 4, 5])
total = F.foldl(lambda acc, x: acc + x, 0, numbers)
# 15
```

#### With Result

```python
from katharos.functools import F
from katharos.ds import Success, Failure

# Use id with Result
Success(42).fmap(F.id)  # Success(42)

# Use compose for transformations
parse = lambda s: int(s)
double = lambda x: x * 2

transform = F.compose(double)(parse)
result = Success("21").fmap(transform)
# Success(42)
```

### Best Practices

**1. Use compose for pure functions:**
```python
# Good: Compose pure functions
transform = F.compose(f)(g)

# Avoid: Don't compose functions with side effects
# Bad example (side effects in composition)
```

**2. Choose the right fold:**
```python
# Use foldl for efficiency (left-to-right)
F.foldl(lambda acc, x: acc + x, 0, large_list)

# Use foldr when order matters (right-to-left)
F.foldr(lambda x, acc: [x] + acc, [], items)
```

**3. Leverage id for clarity:**
```python
# Good: Use id as a clear no-op
def process(value, transform=F.id):
    return transform(value)

# Avoid: Don't create custom identity functions
# Bad: lambda x: x  # Use F.id instead
```

**4. Type annotations with compose:**
```python
# Good: Clear type annotations
def f(x: int) -> str:
    return str(x)

def g(x: float) -> int:
    return int(x)

composed: Callable[[float], str] = F.compose(f)(g)
```

### Summary

The `functools` module provides essential functional programming utilities:

- **F.compose**: Combine functions into pipelines
- **F.id**: Identity function for defaults and testing
- **F.foldl**: Efficient left-to-right reduction
- **F.foldr**: Right-to-left reduction for order-sensitive operations
- **F.sigma**: Combine semigroup elements

These utilities enable point-free style programming, function composition, and powerful data transformations while maintaining type safety and functional purity.

## License

MIT License